# services/retrieval/store.py

"""
store.py

functions:
    upsertChunks    | 청크 + 임베딩을 Chroma 컬렉션에 저장/갱신

helpers:
    _getClient              | Persistent Chroma 클라이언트 생성 헬퍼
    _collectionName         | chatbot_id 기반 컬렉션 이름 생성 헬퍼
    _getOrCreateCollection  | 컬렉션 조회/없으면 생성 헬퍼

설명:
    - RAG 인덱싱 단계에서 생성된 텍스트 청크(TextChunk 등)를
      해당 chatbot_id용 Chroma 컬렉션에 저장하는 레이어.
    - 검색(search) / 삭제(delete) / 리셋(reset) 기능은 별도 모듈에서 다룰 예정이며,
      이 파일은 "쓰기(인덱싱)" 책임만 가진다.

환경변수:
    CHROMA_DIR        : Chroma persistent DB 경로
    COLLECTION_PREFIX : 컬렉션 이름 prefix (기본값 "chatbot_")
"""
from __future__ import annotations

import os
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except ImportError:
    chromadb = None
    ChromaSettings = None
    logger.warning(
        "[VectorStore] chromadb 패키지가 설치되어 있지 않습니다. "
        "pip install chromadb 이후 사용해주세요."
    )

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.join(PROJECT_ROOT, "data", "chroma"))
COLLECTION_PREFIX = os.getenv("COLLECTION_PREFIX", "chatbot_")


def _getClient():
    """
    helper: _getClient
    입력: 없음
    출력:
        client : Persistent Chroma 클라이언트 인스턴스
    """
    if chromadb is None or ChromaSettings is None:
        raise RuntimeError(
            "chromadb 가 설치되어 있지 않습니다. "
            "pip install chromadb 후 다시 시도해주세요."
        )

    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=ChromaSettings(allow_reset=False),
    )
    return client


def _collectionName(chatbotId: str) -> str:
    """
    helper: _collectionName
    입력: chatbotId
    출력: 컬렉션 이름
    """
    return f"{COLLECTION_PREFIX}{chatbotId}"


def _getOrCreateCollection(chatbotId: str):
    """
    helper: _getOrCreateCollection
    입력: chatbotId
    출력: 해당 챗봇용 Chroma 컬렉션
    """
    client = _getClient()
    name = _collectionName(chatbotId)
    col = client.get_or_create_collection(name=name)
    return col


def upsertChunks(
    *,
    chatbotId: str,
    documentId: str,
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> int:
    """
    function: upsertChunks
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"chunks 길이({len(chunks)})와 embeddings 길이({len(embeddings)})가 일치하지 않습니다."
        )

    logger.info(
        "[VectorStore] upsertChunks 시작 (chatbot_id=%s, document_id=%s, n=%d)",
        chatbotId,
        documentId,
        len(chunks),
    )

    col = _getOrCreateCollection(chatbotId)

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict[str, Any]] = []

    for chunk, emb in zip(chunks, embeddings):
        chunkId = chunk.get("chunk_id")
        if not chunkId:
            chunkId = f"{documentId}_{len(ids)}"

        text = chunk.get("text") or ""
        if not isinstance(text, str):
            text = str(text)

        metaRaw = chunk.get("meta") or {}
        if not isinstance(metaRaw, dict):
            metaRaw = {"_raw_meta": str(metaRaw)}

        cleanMeta: dict[str, Any] = {}
        user_group_value: str | None = None

        for k, v in metaRaw.items():
            # user_group_tags는 리스트 타입 → 안전한 스칼라로 변환
            if k == "user_group_tags" and isinstance(v, (list, tuple, set)):
                tags_list = [str(x) for x in v if x is not None]
                if tags_list:
                    # 검색 필터용: user_group (단일 태그, 첫 번째)
                    user_group_value = tags_list[0]
                    # 디버그/뷰잉용: "default,internal" 같은 문자열
                    cleanMeta["user_group_tags"] = ",".join(tags_list)
                continue

            # image_paths는 리스트 → JSON 문자열로 직렬화 (Chroma가 list 메타를 허용하지 않음)
            if k == "image_paths" and isinstance(v, (list, tuple, set)):
                paths = [str(x) for x in v if x is not None]
                try:
                    cleanMeta["image_paths"] = json.dumps(paths, ensure_ascii=False)
                except Exception:
                    cleanMeta["image_paths"] = str(paths)
                continue

            # 1) 기본 스칼라 타입은 그대로
            if v is None or isinstance(v, (str, int, float, bool)):
                cleanMeta[k] = v
            # 2) 나머지 리스트/딕셔너리류는 JSON 문자열로 직렬화
            elif isinstance(v, (list, dict, set, tuple)):
                try:
                    cleanMeta[k] = json.dumps(v, ensure_ascii=False)
                except Exception:
                    cleanMeta[k] = str(v)
            # 3) 기타 타입은 그냥 str()로
            else:
                cleanMeta[k] = str(v)

        # user_group_tags에서 추출한 대표 그룹을 별도 메타로 추가
        if user_group_value is not None and "user_group" not in cleanMeta:
            cleanMeta["user_group"] = user_group_value

        # 공통 필드 강제 주입
        meta: dict[str, Any] = {
            **cleanMeta,
            "chunk_id": chunkId,
            "chatbot_id": chatbotId,
            "document_id": documentId,
        }

        ids.append(chunkId)
        docs.append(text)
        metas.append(meta)

    try:
        if hasattr(col, "upsert"):
            col.upsert(
                ids=ids,
                documents=docs,
                metadatas=metas,
                embeddings=embeddings,
            )
        else:
            col.add(
                ids=ids,
                documents=docs,
                metadatas=metas,
                embeddings=embeddings,
            )
    except Exception as e:
        logger.exception(
            "[VectorStore] upsertChunks 실패 (chatbot_id=%s, document_id=%s): %s",
            chatbotId,
            documentId,
            e,
        )
        raise

    logger.info(
        "[VectorStore] upsertChunks 성공 (chatbot_id=%s, document_id=%s, n=%d)",
        chatbotId,
        documentId,
        len(ids),
    )
    return len(ids)


__all__ = ["upsertChunks"]
