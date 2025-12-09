# services/retrieval/search.py
"""
search.py

functions:
    searchTopK              | 정규화된 질의를 바탕으로 벡터DB에서 top-k 검색 수행
    searchTopKWithNeighbors | top-k + 이웃 청크까지 확장해서 반환

helpers:
    _getClient
    _collectionName
    _tryGetCollection
    _buildWhere
    _buildMeta
"""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional

from services.embedding.embedding import embedText, EmbeddingError

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except ImportError:  # 실제 실행 환경에서 chromadb 미설치 시 방어
    chromadb = None
    ChromaSettings = None
    logger.warning(
        "[VectorStore] chromadb 패키지가 설치되어 있지 않습니다. "
        "pip install chromadb 이후 searchTopK를 사용할 수 있습니다.",
    )

# store.py와 경로 규칙 맞추기
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.join(PROJECT_ROOT, "data", "chroma"))
COLLECTION_PREFIX = os.getenv("COLLECTION_PREFIX", "chatbot_")


def _getClient():
    """
    helper: _getClient
    입력: 없음, 출력: chromadb.PersistentClient 인스턴스

    CHROMA_DIR 경로를 사용하는 Persistent Chroma 클라이언트를 생성한다.
    chromadb 미설치 시 RuntimeError를 발생시킨다.
    """
    if chromadb is None or ChromaSettings is None:
        raise RuntimeError(
            "chromadb 가 설치되어 있지 않습니다. "
            "pip install chromadb 후 다시 시도해주세요.",
        )

    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=ChromaSettings(allow_reset=False),
    )
    return client


def _collectionName(chatbotId: str) -> str:
    """
    helper: _collectionName
    입력: chatbotId, 출력: 실제 Chroma 컬렉션 이름

    chatbot_id → COLLECTION_PREFIX를 붙인 실제 컬렉션 이름으로 매핑한다.
    """
    return f"{COLLECTION_PREFIX}{chatbotId}"


def _tryGetCollection(chatbotId: str):
    """
    helper: _tryGetCollection
    입력: chatbotId, 출력: 컬렉션 객체 또는 None

    검색 용도로 컬렉션을 가져오되, 존재하지 않으면 None을 반환한다.
    (없는데 get_or_create를 호출하면 빈 컬렉션이 새로 생기므로,
    검색 시에는 이 헬퍼를 통해 "없는 경우 빈 검색 결과"를 주도록 한다.)
    """
    client = _getClient()
    name = _collectionName(chatbotId)

    try:
        col = client.get_collection(name=name)
        return col
    except Exception:
        logger.warning(
            "[VectorStore] 컬렉션이 존재하지 않습니다 (chatbot_id=%s, name=%s)",
            chatbotId,
            name,
        )
        return None


def _buildWhere(chatbotId: str, userGroup: Optional[str]) -> Dict[str, Any]:
    """
    helper: _buildWhere
    Chroma where 필터를 구성.
    - user_group은 단일 문자열 메타 필드 (예: "default", "internal").
    """
    filters: List[Dict[str, Any]] = [
        {"chatbot_id": {"$eq": chatbotId}},
    ]

    if userGroup:
        # 단일 스칼라 필드 user_group 기준으로 equality 필터
        filters.append({"user_group": {"$eq": userGroup}})

    if len(filters) == 1:
        return filters[0]
    return {"$and": filters}


def _buildMeta(metaRaw: Dict[str, Any]) -> Dict[str, Any]:
    """
    helper: _buildMeta
    검색/조회 결과의 raw 메타에서 공통 meta 구조를 빌드.
    """
    documentId = metaRaw.get("document_id") or metaRaw.get("manual_id")

    meta = {
        "filename": metaRaw.get("filename"),
        "page": metaRaw.get("page", 0),
        "document_id": documentId,
        "manual_id": metaRaw.get("manual_id") or documentId,
        "chatbot_id": metaRaw.get("chatbot_id"),
        "process_tag": metaRaw.get("process_tag"),
        "user_group_tags": metaRaw.get("user_group_tags", []),
        "image_paths": metaRaw.get("image_paths", []),
        # 추가된 순번 정보
        "order_index": metaRaw.get("order_index"),
        "page_chunk_order": metaRaw.get("page_chunk_order"),
    }
    return meta


def searchTopK(
    *,
    normalizedQuery: str,
    chatbotId: str,
    userGroup: str | None = None,
    topK: int = 5,
) -> List[Dict[str, Any]]:
    """
    function: searchTopK
    입력:
        - normalizedQuery : TASK 1에서 정제된 질의 문자열
        - chatbotId       : 컬렉션을 구분할 chatbot_id
        - userGroup       : 사용자 그룹 태그(필터용), 없으면 전체
        - topK            : 상위 몇 개의 문서 조각을 가져올지
    출력:
        - list[dict] : 각 요소는 {"chunk_id", "text", "score", "meta"} 구조의 dict

    Chroma 벡터 DB에서 normalizedQuery 임베딩을 기반으로 top-k 검색을 수행한다.
    """
    col = _tryGetCollection(chatbotId)
    if col is None:
        return []

    try:
        queryVec = embedText(normalizedQuery)
    except EmbeddingError as e:
        logger.exception(
            "[VectorStore] 쿼리 임베딩 실패 (chatbot_id=%s, query=%r): %s",
            chatbotId,
            normalizedQuery,
            e,
        )
        return []
    except Exception as e:
        logger.exception(
            "[VectorStore] 쿼리 임베딩 중 알 수 없는 오류 (chatbot_id=%s, query=%r): %s",
            chatbotId,
            normalizedQuery,
            e,
        )
        return []

    where = _buildWhere(chatbotId, userGroup)

    try:
        result = col.query(
            query_embeddings=[queryVec],
            n_results=topK,
            where=where,
        )
    except Exception as e:
        logger.exception(
            "[VectorStore] 컬렉션 쿼리 실패 (chatbot_id=%s, query=%r): %s",
            chatbotId,
            normalizedQuery,
            e,
        )
        return []

    ids_all = result.get("ids", [[]])
    docs_all = result.get("documents", [[]])
    metas_all = result.get("metadatas", [[]])
    dists_all = result.get("distances", [[]]) if "distances" in result else [[]]

    ids = ids_all[0] if ids_all else []
    documents = docs_all[0] if docs_all else []
    metadatas = metas_all[0] if metas_all else []
    distances = dists_all[0] if dists_all else []

    chunks: List[Dict[str, Any]] = []

    for idx, doc in enumerate(documents):
        metaRaw = metadatas[idx] if idx < len(metadatas) else {}

        if distances and idx < len(distances):
            dist = distances[idx]
            try:
                # 거리 → (0,1] 범위 유사도로 정규화
                score = 1.0 / (1.0 + dist)
            except Exception:
                score = 0.0
        else:
            score = 0.0

        meta = _buildMeta(metaRaw)

        chunkId = metaRaw.get("chunk_id")
        if not chunkId and idx < len(ids):
            # chunk_id가 메타에 없으면 Chroma id로 fallback
            chunkId = ids[idx]

        chunks.append(
            {
                "chunk_id": chunkId,
                "text": doc,
                "score": score,
                "meta": meta,
            },
        )

    return chunks


def searchTopKWithNeighbors(
    *,
    normalizedQuery: str,
    chatbotId: str,
    userGroup: str | None = None,
    topK: int = 5,
    neighborRadius: int = 1,
) -> List[Dict[str, Any]]:
    """
    function: searchTopKWithNeighbors
    입력:
        - normalizedQuery : TASK 1에서 정제된 질의 문자열
        - chatbotId       : 컬렉션을 구분할 chatbot_id
        - userGroup       : 사용자 그룹 태그(필터용), 없으면 전체
        - topK            : 기본 top-k 개수
        - neighborRadius  : 각 hit 주변에서 몇 step까지 이웃을 포함할지 (±1, ±2 ...)
    출력:
        - list[dict] : 기본 top-k + 이웃 청크까지 확장된 결과

    동작:
        1) searchTopK으로 기본 top-k를 찾고
        2) 각 hit에 대해 order_index ± neighborRadius 범위의 청크를
           동일 document_id 내에서 추가로 가져온다.
        3) base hit는 원래 score, neighbor는 score=0.0 으로 두고
           base → neighbor 순서로 반환.
    """
    # 1) 기본 top-k
    baseChunks = searchTopK(
        normalizedQuery=normalizedQuery,
        chatbotId=chatbotId,
        userGroup=userGroup,
        topK=topK,
    )
    if not baseChunks or neighborRadius <= 0:
        return baseChunks

    col = _tryGetCollection(chatbotId)
    if col is None:
        return baseChunks

    # base hit들의 (document_id, order_index) 모으기
    doc_to_target_orders: Dict[str, set[int]] = {}
    seen_ids: set[str] = set()

    for ch in baseChunks:
        chunk_id = ch.get("chunk_id")
        if chunk_id:
            seen_ids.add(chunk_id)

        meta = ch.get("meta") or {}
        doc_id = meta.get("document_id")
        order_index = meta.get("order_index")

        if doc_id is None or order_index is None:
            continue

        target_set = doc_to_target_orders.setdefault(doc_id, set())
        for d in range(-neighborRadius, neighborRadius + 1):
            if d == 0:
                continue
            target_set.add(order_index + d)

    neighborChunks: List[Dict[str, Any]] = []

    # 2) 문서별로 이웃 청크 조회
    for doc_id, order_set in doc_to_target_orders.items():
        if not order_set:
            continue

        min_idx = min(order_set)
        max_idx = max(order_set)

        try:
            # Collection.get 은 ids/documents/metadatas 가 1차원 리스트로 온다.
            res = col.get(
                where={
                    "$and": [
                        {"document_id": {"$eq": doc_id}},
                        {"order_index": {"$gte": min_idx}},
                        {"order_index": {"$lte": max_idx}},
                    ]
                }
            )
        except Exception as e:
            logger.exception(
                "[VectorStore] neighbor 조회 실패 (chatbot_id=%s, document_id=%s): %s",
                chatbotId,
                doc_id,
                e,
            )
            continue

        ids = res.get("ids", []) or []
        documents = res.get("documents", []) or []
        metadatas = res.get("metadatas", []) or []

        for idx, doc in enumerate(documents):
            metaRaw = metadatas[idx] if idx < len(metadatas) else {}
            oi = metaRaw.get("order_index")

            # 우리가 원하는 order_index 범위만 활용
            if oi is None or oi not in order_set:
                continue

            chunkId = metaRaw.get("chunk_id")
            if not chunkId and idx < len(ids):
                chunkId = ids[idx]

            # base hit 또는 이미 추가된 neighbor 중복 방지
            if chunkId and chunkId in seen_ids:
                continue
            if chunkId:
                seen_ids.add(chunkId)

            meta = _buildMeta(metaRaw)

            neighborChunks.append(
                {
                    "chunk_id": chunkId,
                    "text": doc,
                    "score": 0.0,  # neighbor는 점수 0.0 (원한다면 별도 로직 가능)
                    "meta": meta,
                }
            )

    # 3) neighbor는 document_id, order_index 순으로 정렬
    neighborChunks.sort(
        key=lambda ch: (
            (ch.get("meta") or {}).get("document_id") or "",
            (ch.get("meta") or {}).get("order_index") if (ch.get("meta") or {}).get("order_index") is not None else -1,
        )
    )

    # 기본 hit + neighbor 합쳐서 반환
    return baseChunks + neighborChunks


__all__ = ["searchTopK", "searchTopKWithNeighbors"]
