# services/schemas/querySchemas.py

"""
querySchemas.py

dataclasses:
    QueryRefineResult     | TASK 1 (질의 정규화) 결과 스키마
    QueryContextChunk     | 벡터 검색으로 얻은 문서 조각 정보
    RagMeta               | RAG 메타 정보 (신뢰도, 모호성 등)
    AnswerResult          | TASK 2 (최종 답변) 결과 스키마
    QueryResult           | 전체 STEP 2 파이프라인 결과 스키마

쿼리 분석/검색/답변 생성에 사용되는 공통 타입 정의 모듈.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass
class QueryRefineResult:
    """
    TASK 1: normalize_question 결과를 표현하는 dataclass.

    - normalized_query : 검색용으로 정제된 질문
    - keywords         : 검색/LLM 보조용 키워드 리스트
    - filters          : 문서 타입/섹션/대상 그룹/태그 등 필터 정보
    - meta             : 원 쿼리 등 부가 메타 데이터
    """
    normalized_query: str
    keywords: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

@dataclass
class QueryContextChunk:
    """
    벡터 검색 결과로 얻어진 단일 문서 조각.

    - chunk_id : 벡터 인덱싱 시 부여된 청크 ID
    - text     : 실제 본문 텍스트
    - score    : 유사도 기반 점수 (1에 가까울수록 관련성 높음)
    - meta     : filename, page, manual_id, chatbot_id 등 메타데이터
    """
    chunk_id: str | None
    text: str
    score: float
    meta: dict[str, Any] = field(default_factory=dict)

@dataclass
class RagMeta:
    """
    RAG 상위 파이프라인 메타 정보.

    - retrieval_confidence    : high|medium|low|unknown
    - intent_ambiguity_level  : low|medium|high
    - need_clarification      : 추가 질문/설명이 필요한지 여부
    """
    retrieval_confidence: str = "unknown"
    intent_ambiguity_level: str = "unknown"
    need_clarification: bool = False

@dataclass
class AnswerResult:
    """
    TASK 2: 최종 답변 생성 결과.

    - answer            : 최종 자연어 답변
    - supporting_chunks : 답변 생성에 사용된 문서 조각 리스트
    - meta              : RagMeta (retrieval_confidence 등)
    """
    answer: str
    supporting_chunks: list[QueryContextChunk] = field(default_factory=list)
    meta: RagMeta = field(default_factory=RagMeta)

@dataclass
class QueryResult:
    """
    STEP 2 전체 파이프라인 결과.

    - question              : 원 질문
    - normalized_query      : TASK 1 결과
    - answer                : 최종 답변
    - supporting_chunks     : 답변에 사용된 문서 조각
    - retrieval_confidence  : 검색 신뢰도
    - intent_ambiguity_level: 의도 모호성
    - need_clarification    : 추가 설명 필요 여부
    - latency_ms            : 전체 파이프라인 수행 시간(ms)
    - images                : 쿼리와 관련된 이미지 정보 리스트
                              (예: {"image_key": "DOC123/p3_img1.png", "page": 3, ...})
    """
    question: str
    normalized_query: str
    answer: str
    supporting_chunks: list[QueryContextChunk] = field(default_factory=list)
    retrieval_confidence: str = "unknown"
    intent_ambiguity_level: str = "unknown"
    need_clarification: bool = False
    latency_ms: float = 0.0
    images: list[dict[str, Any]] = field(default_factory=list)  # NEW

__all__ = [
    "QueryRefineResult",
    "QueryContextChunk",
    "RagMeta",
    "AnswerResult",
    "QueryResult",
]
