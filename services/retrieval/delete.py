"""
delete.py

functions:
    deleteChunksByDocument  | 특정 문서(document_id)의 모든 청크/임베딩을 삭제

설명:
    
chatbotId + documentId 기준으로
    해당 문서에서 생성된 모든 청크(벡터 + 메타데이터)를
    Chroma 컬렉션에서 삭제하는 레이어.
실제 PDF 파일 삭제는 documentService.py 등에서 처리하고,
  이 모듈은 "벡터/메타데이터 정리"만 담당한다.
"""

from __future__ import annotations

import logging
from typing import Any

from .store import _getOrCreateCollection  # 기존 헬퍼 재사용

logger = logging.getLogger(__name__)

def deleteChunksByDocument(
    *,
    chatbotId: str,
    documentId: str,
) -> dict[str, Any]:
    """
    deleteChunksByDocument

    입력: chatbotId, documentId, 출력: 삭제 결과 요약 dict

    chatbotId + documentId 기준으로
    해당 문서에서 생성된 모든 청크(벡터 + 메타데이터)를 삭제.

    
    upsertChunks에서 metadatas에 document_id를 항상 넣어주고 있으므로
    where={"document_id": documentId} 조건으로 한 번에 삭제 가능."""
    logger.info("[VectorStore] deleteChunksByDocument 시작 (chatbot_id=%s, document_id=%s)",
        chatbotId,
        documentId,)

    col = _getOrCreateCollection(chatbotId)

    try:
        # Chroma delete: 메타데이터 필터 기반 삭제
        delete_result = col.delete(where={"document_id": documentId})
    except Exception as e:
        logger.exception(
            "[VectorStore] deleteChunksByDocument 실패 (chatbot_id=%s, document_id=%s): %s",
            chatbotId,
            documentId,
            e,
        )
        raise

    logger.info(
        "[VectorStore] deleteChunksByDocument 성공 (chatbot_id=%s, document_id=%s)",
        chatbotId,
        documentId,
    )

    return {
        "chatbot_id": chatbotId,
        "document_id": documentId,
        "delete_result": delete_result,
    }

all = ["deleteChunksByDocument"]