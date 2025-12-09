# services/llm/queryRefine.py

"""
queryRefine.py

functions:
    refineQuery      | 사용자의 질문을 TASK 1로 정제하고 검색용 키워드/필터 생성

helpers:
    _defaultFilters  | TASK 1 실패 시 사용할 기본 필터 스키마

기존 services_rag_pipeline.normalize_question 구현을
services/llm 계층에 맞게 분리/이식한 모듈.
"""
from __future__ import annotations

import json
import logging

from services.llm.client import callQwen, parseJson
from services.schemas.querySchemas import QueryRefineResult

logger = logging.getLogger(__name__)

def _defaultFilters() -> dict[str, object]:
    """
    helper: _defaultFilters
    입력: 없음, 출력: 기본 필터 dict

    TASK 1 LLM 응답 파싱 실패 시 사용할 안전한 기본 필터 스키마.
    """
    return {
        "doc_type": None,
        "section_hint": None,
        "target_group": None,
        "manual_tags": [],
    }

def refineQuery(
    question: str,
    chatbotId: str,
    userGroup: str | None = None,
) -> QueryRefineResult:
    """
    function: refineQuery
    입력:
        - question : 원 질문
        - chatbotId: 챗봇 ID
        - userGroup: 사용자 그룹 태그(선택)
    출력:
        - QueryRefineResult

    TASK 1: 사용자의 질문을 정제하고 검색용 키워드/필터를 생성.
    LLM 응답이 망가질 가능성에 대비해 안전한 fallback을 포함한다.
    """
    inputObj = {
        "question": question,
        "chatbot_id": chatbotId,
        "user_group": userGroup,
    }

    raw = callQwen(
        task_id=1,
        input_payload=json.dumps(inputObj, ensure_ascii=False),
        temperature=0.0,
        max_tokens=1024,
    )

    try:
        data = parseJson(raw)
    except Exception:
        logger.warning(
            "[RAG] TASK 1 JSON 파싱 실패, fallback 사용. raw=%r",
            raw[:200],
        )
        return QueryRefineResult(
            normalized_query=question,
            keywords=[],
            filters=_defaultFilters(),
            meta={"original_query": question},
        )

    normalizedQuery = data.get("normalized_query", question)
    keywords = data.get("keywords", []) or []
    filters = data.get("filters") or {}
    meta = data.get("meta") or {}

    filters.setdefault("doc_type", None)
    filters.setdefault("section_hint", None)
    filters.setdefault("target_group", None)
    filters.setdefault("manual_tags", [])

    # meta에 기본 필드 세팅
    meta.setdefault("original_query", question)
    meta.setdefault("in_scope", True)
    safetyMeta = meta.get("safety") or {}
    if not isinstance(safetyMeta, dict):
        safetyMeta = {}
    safetyMeta.setdefault("block_required", False)
    safetyMeta.setdefault("category", "unknown")
    safetyMeta.setdefault("reason", None)
    meta["safety"] = safetyMeta

    if not isinstance(keywords, list):
        keywords = [str(keywords)]

    logger.info(
        "[RAG] TASK 1 완료 (chatbot_id=%s, user_group=%s, orig_len=%d, norm_len=%d)",
        chatbotId,
        userGroup,
        len(question or ""),
        len(normalizedQuery or ""),
    )

    return QueryRefineResult(
        normalized_query=str(normalizedQuery),
        keywords=[str(k) for k in keywords],
        filters=filters,
        meta=meta,
    )

__all__ = ["refineQuery"]
