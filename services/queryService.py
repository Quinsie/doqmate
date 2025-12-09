# services/queryService.py

"""
queryService.py

functions:
    progressQuery   | STEP 2 전체 파이프라인 (질의 정제 -> 벡터 검색 -> 최종 답변 생성)

helpers:
    _estimateRetrievalConfidence  | 검색 점수 기반 신뢰도 추정 헬퍼
    _analyzeIntentAmbiguity       | 검색 결과 개수 기반 의도 모호성 추정 헬퍼
    _debugPrintQueryPipeline      | 디버그용 전체 STEP2 파이프라인 출력 헬퍼
    _collectImagesFromChunks      | 검색된 청크들에서 image_paths를 취합하는 헬퍼
"""
from __future__ import annotations

import time
import logging
from loggerConfig import (
    setup_root_logging,
    setup_service_file_handlers,
    service_log_context,
)

import json  # image_paths JSON 문자열 풀기용
from typing import Any, Dict, List
import os

from services.llm.answerGeneration import generateAnswerWithContext
from services.llm.queryRefine import refineQuery
from services.retrieval.search import searchTopKWithNeighbors
from services.schemas.querySchemas import (
    QueryContextChunk,
    QueryResult,
)

logger = logging.getLogger(__name__)

# 검색 신뢰도 threshold 상수 (점수 스케일에 맞춰 나중에 조정 가능)
MIN_CONFIDENCE_LEVEL_FOR_ANSWER = "low"  # unknown / low / medium / high 중 최소 허용 레벨
CONFIDENCE_ORDER = ["unknown", "low", "medium", "high"]

# LLM에 넘길 최대 컨텍스트 청크 개수
MAX_CONTEXT_CHUNKS_FOR_LLM = 10


def _confidenceBelowMinimum(level: str) -> bool:
    """
    helper: _confidenceBelowMinimum
    입력: level (retrieval_confidence)
    출력: MIN_CONFIDENCE_LEVEL_FOR_ANSWER보다 낮으면 True
    """
    try:
        return CONFIDENCE_ORDER.index(level) < CONFIDENCE_ORDER.index(
            MIN_CONFIDENCE_LEVEL_FOR_ANSWER,
        )
    except ValueError:
        # 이상한 값 들어오면 보수적으로 막는다
        return True


def _estimateRetrievalConfidence(maxScore: float) -> str:
    """
    helper: _estimateRetrievalConfidence
    입력: maxScore (검색된 청크 중 최대 score)
    출력: retrieval_confidence 문자열

    검색된 청크들의 최대 score를 기반으로 retrieval_confidence를 추정한다.
    score는 0~1 범위를 가정한다 (1에 가까울수록 더 관련 있음).
    """
    if maxScore >= 0.85:
        return "high"
    if maxScore >= 0.65:
        return "medium"
    if maxScore >= 0.40:
        return "low"
    return "unknown"


def _analyzeIntentAmbiguity(numChunks: int) -> str:
    """
    helper: _analyzeIntentAmbiguity
    입력: numChunks (검색된 청크 개수)
    출력: intent_ambiguity_level 문자열

    검색된 문서 조각 수를 기준으로 의도 모호성을 rough하게 추정한다.
    (기존 RAG 파이프라인에서 사용하던 heuristic을 그대로 따른다.)
    """
    if numChunks == 0:
        return "high"
    if numChunks <= 2:
        return "medium"
    return "low"


def _debugPrintQueryPipeline(
    *,
    question: str,
    normalizedQuery: str,
    keywords: list[str],
    filters: dict,
    chunks: list[dict],
    answer: str,
    retrievalConfidence: str,
    intentAmbiguityLevel: str,
    needClarification: bool,
    latencyMs: float,
) -> None:
    """
    helper: _debugPrintQueryPipeline
    """
    print("\n======================[DEBUG] QUERY PIPELINE======================")  # DEBUG
    print(f"[DEBUG] question           : {question!r}")  # DEBUG
    print(f"[DEBUG] normalized_query   : {normalizedQuery!r}")  # DEBUG
    print(f"[DEBUG] keywords           : {keywords}")  # DEBUG
    print(f"[DEBUG] filters            : {filters}")  # DEBUG

    print("\n[DEBUG] retrieval_confidence   :", retrievalConfidence)  # DEBUG
    print("[DEBUG] intent_ambiguity_level :", intentAmbiguityLevel)  # DEBUG
    print("[DEBUG] need_clarification     :", needClarification)  # DEBUG
    print("[DEBUG] latency_ms             :", round(latencyMs, 2))  # DEBUG

    print("\n[DEBUG] [RETRIEVED CHUNKS - FULL]")  # DEBUG
    if not chunks:
        print("  (no chunks)")  # DEBUG
    else:
        for idx, c in enumerate(chunks, start=1):
            text = str(c.get("text") or "")
            meta = dict(c.get("meta") or {})
            score = float(c.get("score") or 0.0)
            chunkId = c.get("chunk_id")
            page = meta.get("page")
            documentId = meta.get("document_id") or meta.get("manual_id")
            filename = meta.get("filename")

            snippet = text[:120].replace("\n", " ")
            if len(text) > 120:
                snippet += "..."

            print(f"\n  --- CHUNK #{idx} ---")  # DEBUG
            print(f"    chunk_id   : {chunkId}")  # DEBUG
            print(f"    score      : {score:.4f}")  # DEBUG
            print(f"    filename   : {filename}")  # DEBUG
            print(f"    document_id: {documentId}")  # DEBUG
            print(f"    page       : {page}")  # DEBUG
            print(f"    snippet    : {snippet!r}")  # DEBUG
            print(f"    meta       : {meta}")  # DEBUG

    print("\n[DEBUG] [FINAL ANSWER]")  # DEBUG
    print(answer)  # DEBUG
    print("================================================================\n")  # DEBUG


# NEW: 검색된 청크들에서 image_paths를 취합해 최종 images 리스트를 만드는 헬퍼
def _collectImagesFromChunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    입력:
        chunks : searchTopKWithNeighbors가 반환한 raw chunk dict 리스트
                 (각 dict는 최소한 text, score, meta를 포함)
    출력:
        images : [
            {
                "image_key": "DOC123/p3_img1.png",
                "document_id": "DOC123",
                "page": 3,
                "image_index": 1,
                "url": "/pdf_images/DOC123/p3_img1.png",
                "related_chunk_ids": ["DOC123_p3_c0", "DOC123_p3_c1"],
            },
            ...
        ]

    image_paths 메타는 현재 Chroma에 JSON 문자열로 저장되므로
    여기서 다시 list로 복원해서 사용해야 한다.
    """
    image_map: Dict[str, Dict[str, Any]] = {}

    for c in chunks:
        meta = dict(c.get("meta") or {})
        chunk_id = c.get("chunk_id")
        page = meta.get("page")

        raw_image_paths = meta.get("image_paths")
        if not raw_image_paths:
            continue

        # 1) 기본 케이스: list/tuple/set 그대로 들어온 경우 (옛 인덱스 호환)
        image_paths: List[str] = []
        if isinstance(raw_image_paths, (list, tuple, set)):
            image_paths = [str(x) for x in raw_image_paths if x is not None]

        # 2) 현재 표준 케이스: JSON 문자열 형태로 저장된 경우
        elif isinstance(raw_image_paths, str):
            decoded = None
            try:
                decoded = json.loads(raw_image_paths)
            except Exception:
                decoded = None

            if isinstance(decoded, (list, tuple, set)):
                image_paths = [str(x) for x in decoded if x is not None]
            elif decoded is None:
                # JSON이 아니거나 파싱 실패 → 그냥 단일 경로 문자열로 취급
                image_paths = [raw_image_paths]
            else:
                # dict 등 애매한 구조면 전체를 문자열로 취급
                image_paths = [raw_image_paths]

        else:
            # 그 외 타입은 무시 (안전하게 패스)
            continue

        if not image_paths:
            continue

        for p in image_paths:
            if p is None:
                continue

            image_key = str(p)  # 예: "DOC123/p3_img1.png"

            # === image_key에서 document_id / page / image_index 파싱 ===
            document_id = None
            page_from_name = None
            image_index = None

            try:
                # "DOC123/p3_img1.png" → "DOC123", "p3_img1.png"
                doc_part, file_part = image_key.split("/", 1)
                document_id = doc_part

                base, _ = os.path.splitext(file_part)  # "p3_img1"
                if base.startswith("p"):
                    body = base[1:]  # "3_img1"
                    if "_img" in body:
                        page_str, img_str = body.split("_img", 1)
                        page_from_name = int(page_str)
                        image_index = int(img_str)
            except Exception:
                # 파싱 실패해도 최소한 image_key는 쓰게 둠
                pass

            key = image_key  # dedup 기준은 경로 자체

            info = image_map.setdefault(
                key,
                {
                    "image_key": image_key,
                    "document_id": document_id,
                    "page": page_from_name or page,
                    "image_index": image_index,
                    "related_chunk_ids": set(),
                },
            )

            if chunk_id:
                info["related_chunk_ids"].add(str(chunk_id))

            # page가 None이면 meta의 page로 보완
            if info.get("page") is None and page is not None:
                info["page"] = page

    images: List[Dict[str, Any]] = []
    for info in image_map.values():
        image_key = info["image_key"]
        document_id = info.get("document_id")

        # 서버에서 static 서빙을 "/pdf_images/<image_key>"로 한다는 가정
        # (nginx나 FastAPI StaticFiles 설정에 따라 필요 시 수정)
        url = f"/pdf_images/{image_key}"

        images.append(
            {
                "image_key": image_key,                      # "DOC123/p3_img1.png"
                "document_id": document_id,                  # "DOC123"
                "page": info.get("page"),                    # 3
                "image_index": info.get("image_index"),      # 1
                "url": url,                                  # "/pdf_images/DOC123/p3_img1.png"
                "related_chunk_ids": sorted(info["related_chunk_ids"]),
            },
        )

    return images


def progressQuery(
    *,
    chatbotId: str,
    question: str,
    userGroup: str | None = None,
    topK: int = 5,
    debug: bool = True,
) -> QueryResult:
    """
    STEP 2 전체 파이프라인
    """

    setup_root_logging()
    setup_service_file_handlers()

    with service_log_context("queryService"):
        t0 = time.time()
        q = (question or "").strip()
        if not q:
            raise ValueError("question은 비어 있을 수 없습니다.")

        # 1) 질문 정제
        norm = refineQuery(question=q, chatbotId=chatbotId, userGroup=userGroup)
        normalizedQuery = norm.normalized_query

        # TASK 1 meta 기반 safety 차단 처리
        normMeta = getattr(norm, "meta", {}) or {}
        safetyMeta = normMeta.get("safety") or {}
        blockRequired = bool(safetyMeta.get("block_required") or False)
        if blockRequired:
            elapsedMs = (time.time() - t0) * 1000.0

            safeAnswer = (
                "이 챗봇은 업로드된 문서를 기반으로 한 업무 질의응답용입니다.\n"
                "해당 질문은 서비스 정책상 답변하지 않습니다."
            )

            result = QueryResult(
                question=q,
                normalized_query=normalizedQuery,
                answer=safeAnswer,
                supporting_chunks=[],
                retrieval_confidence="blocked",
                intent_ambiguity_level="high",
                need_clarification=False,
                latency_ms=elapsedMs,
                images=[],  # 차단 시 이미지 없음
            )

            logger.info(
                "[RAG] progressQuery 차단 응답 (chatbot_id=%s, user_group=%s, reason=%s)",
                chatbotId,
                userGroup,
                safetyMeta.get("reason") or "policy_block",
            )

            if debug:
                _debugPrintQueryPipeline(
                    question=q,
                    normalizedQuery=normalizedQuery,
                    keywords=norm.keywords,
                    filters=norm.filters,
                    chunks=[],
                    answer=result.answer,
                    retrievalConfidence=result.retrieval_confidence,
                    intentAmbiguityLevel=result.intent_ambiguity_level,
                    needClarification=result.need_clarification,
                    latencyMs=elapsedMs,
                )
            return result

        # 2) 벡터 검색 (이웃 청크 포함)
        rawChunks = searchTopKWithNeighbors(
            normalizedQuery=normalizedQuery,
            chatbotId=chatbotId,
            userGroup=userGroup,
            topK=topK,
            neighborRadius=2,  # ±2 청크까지 포함
        )

        # score 기준 정렬
        chunks = sorted(
            rawChunks,
            key=lambda c: float(c.get("score") or 0.0),
            reverse=True,
        )

        maxScore = max((float(c.get("score") or 0.0) for c in chunks), default=0.0)
        retrievalConfidence = _estimateRetrievalConfidence(maxScore)
        intentAmbiguityLevel = _analyzeIntentAmbiguity(len(chunks))

        # 3) 신뢰도 너무 낮으면 안전 응답
        if _confidenceBelowMinimum(retrievalConfidence):
            elapsedMs = (time.time() - t0) * 1000.0

            supportingChunks: list[QueryContextChunk] = []
            for c in chunks:
                supportingChunks.append(
                    QueryContextChunk(
                        chunk_id=c.get("chunk_id"),
                        text=str(c.get("text") or ""),
                        score=float(c.get("score") or 0.0),
                        meta=dict(c.get("meta") or {}),
                    ),
                )

            # 신뢰도 낮아도 참고용 이미지는 같이 내려준다
            images = _collectImagesFromChunks(chunks)

            safeAnswer = (
                "이 챗봇은 업로드된 문서를 기반으로만 답변합니다.\n"
                "현재 질문과 직접적으로 연관된 문서 내용을 찾지 못해, "
                "임의로 추측해서 답변하지 않겠습니다."
            )

            result = QueryResult(
                question=q,
                normalized_query=normalizedQuery,
                answer=safeAnswer,
                supporting_chunks=supportingChunks,
                retrieval_confidence=retrievalConfidence,
                intent_ambiguity_level=intentAmbiguityLevel,
                need_clarification=False,
                latency_ms=elapsedMs,
                images=images,
            )

            logger.info(
                "[RAG] progressQuery 낮은 신뢰도로 인한 안전 응답 "
                "(chatbot_id=%s, user_group=%s, topK=%d, latency=%.1fms, max_score=%.3f)",
                chatbotId,
                userGroup,
                topK,
                elapsedMs,
                maxScore,
            )

            if debug:
                _debugPrintQueryPipeline(
                    question=q,
                    normalizedQuery=normalizedQuery,
                    keywords=norm.keywords,
                    filters=norm.filters,
                    chunks=chunks,
                    answer=result.answer,
                    retrievalConfidence=retrievalConfidence,
                    intentAmbiguityLevel=intentAmbiguityLevel,
                    needClarification=result.need_clarification,
                    latencyMs=elapsedMs,
                )

            return result

        # 4) LLM 컨텍스트용 청크 구성
        chunksForLLM = sorted(
            chunks,
            key=lambda c: (
                0 if float(c.get("score") or 0.0) > 0 else 1,
                (c.get("meta") or {}).get("document_id") or "",
                (c.get("meta") or {}).get("order_index")
                if (c.get("meta") or {}).get("order_index") is not None
                else 10**9,
            ),
        )

        contextChunksForLLM = chunksForLLM[:MAX_CONTEXT_CHUNKS_FOR_LLM]

        # 이 답변에 진짜로 쓰인 컨텍스트 기준으로 이미지 모으기
        images = _collectImagesFromChunks(contextChunksForLLM)

        # 5) 최종 답변 생성
        answerResult = generateAnswerWithContext(
            question=q,
            normalizedQuery=normalizedQuery,
            keywords=norm.keywords,
            filters=norm.filters,
            retrievalConfidence=retrievalConfidence,
            intentAmbiguityLevel=intentAmbiguityLevel,
            contextChunks=contextChunksForLLM,
        )

        elapsedMs = (time.time() - t0) * 1000.0

        supportingChunks: list[QueryContextChunk] = answerResult.supporting_chunks

        result = QueryResult(
            question=q,
            normalized_query=answerResult.normalized_query
            if getattr(answerResult, "normalized_query", None)
            else normalizedQuery,
            answer=answerResult.answer,
            supporting_chunks=supportingChunks,
            retrieval_confidence=answerResult.meta.retrieval_confidence,
            intent_ambiguity_level=answerResult.meta.intent_ambiguity_level,
            need_clarification=answerResult.meta.need_clarification,
            latency_ms=elapsedMs,
            images=images,
        )

        logger.info(
            "[RAG] progressQuery 완료 (chatbot_id=%s, user_group=%s, topK=%d, latency=%.1fms, max_score=%.3f)",
            chatbotId,
            userGroup,
            topK,
            elapsedMs,
            maxScore,
        )

        if debug:
            _debugPrintQueryPipeline(
                question=q,
                normalizedQuery=result.normalized_query,
                keywords=norm.keywords,
                filters=norm.filters,
                chunks=chunks,
                answer=answerResult.answer,
                retrievalConfidence=result.retrieval_confidence,
                intentAmbiguityLevel=result.intent_ambiguity_level,
                needClarification=result.need_clarification,
                latencyMs=elapsedMs,
            )

        return result


__all__ = ["progressQuery"]


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    questionArg = "테스트 질문입니다."
    chatbotId = "test_chatbot"
    userGroup: str | None = None
    topK = 5

    if len(sys.argv) >= 2:
        questionArg = sys.argv[1]
    if len(sys.argv) >= 3:
        chatbotId = sys.argv[2]
    if len(sys.argv) >= 4:
        userGroup = sys.argv[3] or None
    if len(sys.argv) >= 5:
        try:
            topK = int(sys.argv[4])
        except Exception:
            topK = 5

    try:
        _ = progressQuery(
            chatbotId=chatbotId,
            question=questionArg,
            userGroup=userGroup,
            topK=topK,
            debug=True,
        )
    except Exception as e:
        logger.exception("queryService 테스트 실행 중 예외 발생: error=%s", e)
        print(f"[ERROR] queryService 실행 중 오류: {e}")
        sys.exit(1)
