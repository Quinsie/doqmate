# services/schemas/embeddingSchemas.py

"""
embeddingSchemas.py

dataclass:
    TextChunk               | RAG 인덱싱/검색용 텍스트 청크 단위 정보

pydantic:
    EmbeddingRequest        | 임베딩 서버 /v1/embeddings 요청 바디 스키마
    EmbeddingResponseItem   | 단일 텍스트에 대한 임베딩 응답 아이템
    EmbeddingResponse       | /v1/embeddings 전체 응답 스키마

이 파일은 임베딩/검색 레이어에서 사용되는 데이터 스키마를 관리한다.
"""
from typing import Any, List
from pydantic import BaseModel
from dataclasses import dataclass

@dataclass
class TextChunk:
    """
    dataclass: TextChunk

    - chunk_id : 문서 전체에서 유일한 청크 식별자
                 (예: "manual001_p3_c0")
    - text     : 벡터 임베딩 대상이 되는 텍스트 청크 내용
    - page     : 해당 청크가 소속된 페이지 번호 (1-base)
    - order    : 페이지 내 청크 순서 (0-base)
    - meta     : 검색/RAG 단계에서 사용되는 메타데이터 딕셔너리
                 (filename, document_id, chatbot_id, user_group_tags,
                  process_tag, chunk_order 등)

    secondRefine -> chunking 과정에서 생성되는 최종 텍스트 단위.
    VectorDB(Chroma 등)에 저장될 문서 조각이며, 임베딩/검색에서 핵심 단위가 된다.
    """
    chunk_id: str
    text: str
    page: int
    order: int
    meta: dict[str, Any]

class EmbeddingRequest(BaseModel):
    """
    pydantic: EmbeddingRequest

    - model : 클라이언트가 요청하는 임베딩 모델 이름
    - input : 임베딩 대상 문장/텍스트 리스트
    """
    model: str
    input: List[str]

class EmbeddingResponseItem(BaseModel):
    """
    pydantic: EmbeddingResponseItem

    - embedding : 하나의 문장/텍스트에 대한 임베딩 벡터 (float 리스트)
    """
    embedding: List[float]

class EmbeddingResponse(BaseModel):
    """
    pydantic: EmbeddingResponse

    - data : EmbeddingResponseItem 리스트 (입력 개수와 동일한 길이)
    """
    data: List[EmbeddingResponseItem]