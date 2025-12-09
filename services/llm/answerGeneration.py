# services/llm/answerGeneration.py

"""
answerGeneration.py
[최종 수정: 2025-11-23 by 표지호]

functions:
    generateAnswerWithContext  | TASK 2, 문맥 청크 + 메타 정보를 기반으로 최종 답변 생성

helpers:
    _buildInputObject          | TASK 2 LLM 입력 payload 구성
    _fallbackAnswer            | LLM 실패 시 사용할 기본 fallback 답변 생성

기존 services_rag_pipeline.generate_answer 중
TASK 2 LLM 호출 및 JSON 파싱 부분을 분리/이식한 모듈.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from services.llm.client import callQwen, parseJson
from services.schemas.querySchemas import (
    AnswerResult,
    QueryContextChunk,
    RagMeta,
)

logger = logging.getLogger(__name__)

# 최종 응답에 노출할 supporting_chunks 최대 개수
MAX_SUPPORTING_CHUNKS_IN_RESULT = 5

def _buildInputObject(
    question: str,
    normalizedQuery: str,
    keywords: list[str],
    filters: dict[str, Any],
    retrievalConfidence: str,
    intentAmbiguityLevel: str,
    contextChunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    helper: _buildInputObject
    입력: 질문, TASK 1 결과, 검색 메타, 컨텍스트 청크
    출력: TASK 2 LLM에 넘길 JSON 오브젝트(dict)

    프롬프트 스펙(TASK 2 OUTPUT_FORMAT)에 맞춰 입력 payload를 구성한다.
    """
    return {
        "question": question,
        "normalized_query": normalizedQuery,
        "keywords": keywords,
        "filters": filters,
        "retrieval_confidence": retrievalConfidence,
        "intent_ambiguity_level": intentAmbiguityLevel,
        "context_chunks": contextChunks,
    }

def _fallbackAnswer(
    *,
    question: str,
    chunks: list[dict[str, Any]],
    retrievalConfidence: str,
    intentAmbiguityLevel: str,
) -> AnswerResult:
    """
    helper: _fallbackAnswer
    입력: 질문, 검색 청크, retrieval/meta
    출력: AnswerResult

    TASK 2 JSON 파싱 실패 시 사용할 기본 fallback 로직.
    - 검색된 첫 chunk를 그대로 답변으로 사용하거나, 없으면 고정 문자열.
    """
    if chunks:
        answerText = chunks[0].get("text") or "관련된 정보를 찾지 못했습니다."
    else:
        answerText = "관련된 정보를 찾지 못했습니다."

    # NEW: 더 이상 chunk 내용을 그대로 답변하지 않음
    answerText = (
        "답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.\n"
        "이 챗봇은 문서에 근거하지 않은 내용을 임의로 생성하지 않습니다."
    )

    meta = RagMeta(
        retrieval_confidence=retrievalConfidence,
        intent_ambiguity_level=intentAmbiguityLevel,
        need_clarification=False,
    )

    # 점수 기준으로 상위 N개만 supporting_chunks로 노출
    try:
        limitedChunks = sorted(
            chunks,
            key=lambda c: float(c.get("score") or 0.0),
            reverse=True,
        )[:MAX_SUPPORTING_CHUNKS_IN_RESULT]
    except Exception:
        limitedChunks = chunks[:MAX_SUPPORTING_CHUNKS_IN_RESULT]

    ctxChunks: list[QueryContextChunk] = []
    for c in limitedChunks:
        ctxChunks.append(
            QueryContextChunk(
                chunk_id=c.get("chunk_id"),
                text=str(c.get("text") or ""),
                score=float(c.get("score") or 0.0),
                meta=dict(c.get("meta") or {}),
            ),
        )

    return AnswerResult(
        answer=answerText,
        supporting_chunks=ctxChunks,
        meta=meta,
    )

def generateAnswerWithContext(
    *,
    question: str,
    normalizedQuery: str,
    keywords: list[str],
    filters: dict[str, Any],
    retrievalConfidence: str,
    intentAmbiguityLevel: str,
    contextChunks: list[dict[str, Any]],
) -> AnswerResult:
    """
    function: generateAnswerWithContext
    입력:
        - question             : 원 질문
        - normalizedQuery      : TASK 1 정규화 질의
        - keywords             : TASK 1 키워드
        - filters              : TASK 1 필터
        - retrievalConfidence  : high|medium|low|unknown
        - intentAmbiguityLevel : low|medium|high
        - contextChunks        : searchTopK 결과 (dict 리스트)
    출력:
        - AnswerResult

    TASK 2: LLM에 contextChunks + 메타 정보를 전달하여 최종 답변을 생성한다.
    JSON 파싱 실패 시 _fallbackAnswer를 사용한다.
    """
    inputObj = _buildInputObject(
        question=question,
        normalizedQuery=normalizedQuery,
        keywords=keywords,
        filters=filters,
        retrievalConfidence=retrievalConfidence,
        intentAmbiguityLevel=intentAmbiguityLevel,
        contextChunks=contextChunks,
    )

    # LLM 호출
    raw = callQwen(
        task_id=2,
        input_payload=json.dumps(inputObj, ensure_ascii=False),
        temperature=0.1,
        max_tokens=2048,
    )

    try:
        data = parseJson(raw)
    except Exception:
        logger.warning(
            "[RAG] TASK 2 JSON 파싱 실패, fallback 사용. raw=%r",
            raw[:200],
        )
        return _fallbackAnswer(
            question=question,
            chunks=contextChunks,
            retrievalConfidence=retrievalConfidence,
            intentAmbiguityLevel=intentAmbiguityLevel,
        )

    # LLM 결과 정리
    answerText = str(data.get("answer") or "").strip()
    if not answerText:
        logger.warning("[RAG] TASK 2 결과 answer가 비어 있어 fallback 사용")
        return _fallbackAnswer(
            question=question,
            chunks=contextChunks,
            retrievalConfidence=retrievalConfidence,
            intentAmbiguityLevel=intentAmbiguityLevel,
        )

    # LLM이 answerable / safety_blocked를 root나 meta로 줄 수 있도록 확장
    answerable = bool(data.get("answerable", True))
    safetyBlocked = bool(data.get("safety_blocked", False))

    rawChunks = data.get("supporting_chunks") or contextChunks
    rawMeta = data.get("meta") or {}

    rawMeta.setdefault("retrieval_confidence", retrievalConfidence)
    rawMeta.setdefault("intent_ambiguity_level", intentAmbiguityLevel)
    rawMeta.setdefault("need_clarification", False)

    # meta 안에 answerable, safety_blocked도 함께 넣어둔다 (스키마 확장 없이 dict로만 보존)
    rawMeta.setdefault("answerable", answerable)
    rawMeta.setdefault("safety_blocked", safetyBlocked)

    # supporting_chunks도 점수 기준 상위 N개만 남기고, 없으면 그대로
    try:
        limitedChunks = sorted(
            rawChunks,
            key=lambda c: float(c.get("score") or 0.0),
            reverse=True,
        )[:MAX_SUPPORTING_CHUNKS_IN_RESULT]
    except Exception:
        limitedChunks = rawChunks[:MAX_SUPPORTING_CHUNKS_IN_RESULT]

    meta = RagMeta(
        retrieval_confidence=str(rawMeta.get("retrieval_confidence") or "unknown"),
        intent_ambiguity_level=str(
            rawMeta.get("intent_ambiguity_level") or "unknown",
        ),
        need_clarification=bool(rawMeta.get("need_clarification") or False),
    )

    ctxChunks: list[QueryContextChunk] = []
    for c in limitedChunks:
        ctxChunks.append(
            QueryContextChunk(
                chunk_id=c.get("chunk_id"),
                text=str(c.get("text") or ""),
                score=float(c.get("score") or 0.0),
                meta=dict(c.get("meta") or {}),
            ),
        )

    return AnswerResult(
        answer=answerText,
        supporting_chunks=ctxChunks,
        meta=meta,
    )

__all__ = ["generateAnswerWithContext"]
