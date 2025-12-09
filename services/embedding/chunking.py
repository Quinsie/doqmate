# services/embedding/chunking.py

"""
chunking.py

functions:
    chunkMergedPages     | 2차 정제 결과를 벡터DB 인덱싱용 텍스트 청크로 분할

helpers:
    _buildPageText       | 페이지 단위 MergedTextBlock들을 하나의 문자열로 병합
    _chunkPageText       | 단일 페이지 텍스트를 maxChars/overlap 기준으로 청킹

secondRefine 반환값을 입력으로 받아 각 페이지의 텍스트를 문자 수 기준으로 잘라 TextChunk 리스트를 생성한다.
이 모듈은 "정제된 텍스트 -> 청크" 단계까지만 책임진다.
"""
import logging

from services.schemas.pdfSchemas import MergedTextBlock
from services.schemas.embeddingSchemas import TextChunk

logger = logging.getLogger(__name__)

def _buildPageText(blocks: list[MergedTextBlock]) -> str:
    """
    helper: _buildPageText
    입력:
        blocks  : 단일 페이지에 대한 MergedTextBlock 리스트
    출력:
        pageText: 페이지 전체를 대표하는 문자열

    동작:
        - 페이지 내 여러 MergedTextBlock이 있을 수 있으므로 (지금은 가능성 없음)
          각 블록의 text를 정제 후 두 줄 개행("\n\n")을 기준으로 이어붙인다.
        - 개별 블록 텍스트는 strip() 후 사용하며, 비어 있는 블록은 무시한다.
    """
    if not blocks:
        return ""

    texts: list[str] = []

    for block in blocks:
        text = (block.text or "").strip()
        if not text:
            continue
        texts.append(text)

    if not texts:
        return ""

    return "\n\n".join(texts).strip()

def _chunkPageText(
    *,
    page: int,
    pageText: str,
    chatbotId: str,
    documentId: str,
    filename: str | None,
    userGroupTags: list[str],
    maxChars: int,
    overlap: int,
) -> list[TextChunk]:
    """
    helper: _chunkPageText
    입력:
        page          : 페이지 번호
        pageText      : 해당 페이지 전체 텍스트
        chatbotId     : 논리적 챗봇 ID
        documentId    : 논리적 문서 ID
        filename      : 원본 파일명 (없으면 None)
        userGroupTags : 사용자 그룹 태그 리스트
        maxChars      : 청크당 최대 문자 수
        overlap       : 인접 청크 간 겹치는 문자 수
    출력:
        chunks        : 단일 페이지에서 생성된 TextChunk 리스트

    동작:
        - pageText를 maxChars / overlap 기준으로 앞에서부터 순차적으로 분할한다.
        - 청크 간에는 overlap 만큼의 문자를 겹치게 하여 문맥이 끊기지 않도록 한다.
        - 각 청크에는 chunk_id 및 메타데이터를 채워넣는다.
    """
    chunks: list[TextChunk] = []

    text = (pageText or "").strip()
    if not text:
        return chunks

    length = len(text)
    start = 0
    order = 0

    while start < length:
        end = min(start + maxChars, length)
        chunkText = text[start:end].strip()
        if not chunkText:
            break

        chunkId = f"{documentId}_p{page}_c{order}"

        meta: dict[str, object] = {
            "filename": filename,
            "page": page,
            "document_id": documentId,
            "chatbot_id": chatbotId,
            "user_group_tags": userGroupTags,
            "process_tag": "body",
            "chunk_order": order,
        }

        chunks.append(
            TextChunk(
                chunk_id=chunkId,
                text=chunkText,
                page=page,
                order=order,
                meta=meta,
            )
        )

        if end >= length:
            break

        # overlap 만큼 이전 위치로 되돌아가서 다음 청크를 시작
        start = end - overlap
        if start < 0:
            start = 0

        order += 1

    return chunks

def chunkMergedPages(
    mergedPages: dict[int, list[MergedTextBlock]],
    *,
    chatbotId: str,
    documentId: str,
    filename: str | None = None,
    userGroupTags: list[str] | None = None,
    maxChars: int = 800,
    overlap: int = 200,
) -> list[TextChunk]:
    """
    function: chunkMergedPages
    입력:
        mergedPages   : 2차 정제 결과 (page -> [MergedTextBlock...])
        chatbotId     : 논리적 챗봇 ID
        documentId    : 논리적 문서 ID
        filename      : 원본 파일명 (없으면 None)
        userGroupTags : 사용자 그룹 태그 리스트 (None이면 ["default"])
        maxChars      : 청크당 최대 문자 수 (기본 800)
        overlap       : 인접 청크 간 겹치는 문자 수 (기본 200)
    출력:
        chunks        : 전체 문서에 대한 TextChunk 리스트

    동작 개요:
        1) page 오름차순으로 mergedPages를 순회
        2) 각 페이지에 대해 _buildPageText로 페이지 전체 텍스트 생성
        3) _chunkPageText를 호출해 페이지 텍스트를 청크 단위로 분할
        4) 생성된 모든 TextChunk를 단일 리스트로 모아 반환
    """
    if maxChars <= 0:
        raise ValueError(f"maxChars는 0보다 커야 합니다. maxChars={maxChars}")
    if overlap < 0:
        raise ValueError(f"overlap은 0 이상이어야 합니다. overlap={overlap}")

    if not mergedPages:
        logger.info(
            "chunkMergedPages: mergedPages 비어 있음 | chatbot_id=%s document_id=%s",
            chatbotId,
            documentId,
        )
        return []

    if not userGroupTags:
        userGroupTags = ["default"]

    logger.info(
        "chunkMergedPages 시작: chatbot_id=%s document_id=%s pages=%d maxChars=%d overlap=%d",
        chatbotId,
        documentId,
        len(mergedPages),
        maxChars,
        overlap,
    )

    allChunks: list[TextChunk] = []

    for page in sorted(mergedPages.keys()):
        blocks = mergedPages.get(page) or []
        pageText = _buildPageText(blocks)

        if not pageText:
            logger.debug(
                "chunkMergedPages: 페이지 텍스트 없음, 스킵 | page=%d chatbot_id=%s document_id=%s",
                page,
                chatbotId,
                documentId,
            )
            continue

        pageChunks = _chunkPageText(
            page=page,
            pageText=pageText,
            chatbotId=chatbotId,
            documentId=documentId,
            filename=filename,
            userGroupTags=userGroupTags,
            maxChars=maxChars,
            overlap=overlap,
        )

        allChunks.extend(pageChunks)

    logger.info(
        "chunkMergedPages 완료: chatbot_id=%s document_id=%s total_chunks=%d",
        chatbotId,
        documentId,
        len(allChunks),
    )

    return allChunks

__all__ = ["chunkMergedPages"]