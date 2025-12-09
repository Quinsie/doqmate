# services/llm/secondRefine.py

"""
secondRefine.py

functions:
    mergeText          | PyMuPDF 텍스트 + 1차 정제된 OCR 텍스트를 페이지 단위로 2차 정제(병합)

helpers:
    _buildPageTexts    | 페이지별 PyMuPDF/OCR 텍스트 집계 헬퍼
    _runTask3ForPage   | 단일 페이지에 대해 Qwen Task 3 호출 및 응답 파싱
    _fallbackMergePage | Task 3 실패 시 PyMuPDF+OCR 텍스트를 그대로 이어붙이는 fallback

페이지 단위로 PyMuPDF 텍스트와 OCR 1차 정제 텍스트를 하나의 긴 문자열로 묶어 Task 3에 전달.
Task 3는 JSON ONLY로 응답하며, merged_blocks/merge_log 스펙을 따른다.
실패 시에는 pymupdf_text + "\\n" + ocr_text_cleaned 를 그대로 이어붙여 사용한다.
반환 타입은 기존 파이프라인과의 호환을 위해 page -> [MergedTextBlock] 구조.
"""

from __future__ import annotations

import json
import logging
from typing import Any  # 추가

from services.llm.client import callQwen, parseJson
from services.schemas.pdfSchemas import (
    MergedTextBlock,
    PDFExtractionResult,
    TextBlock,
)

logger = logging.getLogger(__name__)

# 내부 헬퍼: 페이지별 텍스트/블록 집계
def _buildPageTexts(
    extraction: PDFExtractionResult,
    ocrBlocks: list[TextBlock],
) -> tuple[
    dict[int, str],               # pymupdf_texts
    dict[int, str],               # ocr_texts
    dict[int, list[str]],         # src_ids_by_page
    dict[int, list[dict[str, Any]]],  # blocks_by_page (Task3에 넘길 raw 블록 정보)
]:
    """
    helper: _buildPageTexts
    입력:
        - extraction : extractPDF 결과 (PyMuPDF TextBlock 포함)
        - ocrBlocks  : 1차 정제 완료된 OCR TextBlock 리스트
    출력:
        - pymupdf_texts : page -> PyMuPDF 텍스트 전체 문자열
        - ocr_texts     : page -> OCR 1차 정제 텍스트 전체 문자열
        - src_ids_by_page : page -> 이 페이지에 포함된 모든 원본 block_id 리스트
        - blocks_by_page  : page -> [
              {
                  "source": "pymupdf" | "ocr",
                  "block_id": str,
                  "text": str,
                  "bbox": [x0, y0, x1, y1],
                  "prob": float | null
              },
              ...
          ]

    페이지 단위로 텍스트를 모아 하나의 문자열로 만들고,
    동시에 Task 3에서 사용할 수 있도록 블록 단위 메타데이터도 구성한다.
    """
    pymupdf_by_page: dict[int, list[str]] = {}
    ocr_by_page: dict[int, list[str]] = {}
    src_ids_by_page: dict[int, list[str]] = {}
    blocks_by_page: dict[int, list[dict[str, Any]]] = {}

    # PyMuPDF 텍스트
    for tb in extraction.text_blocks:
        page = int(tb.page)
        text = (tb.text or "").strip()
        if not text:
            continue

        pymupdf_by_page.setdefault(page, []).append(text)
        src_ids_by_page.setdefault(page, []).append(tb.block_id)

        blocks_by_page.setdefault(page, []).append(
            {
                "source": "pymupdf",
                "block_id": tb.block_id,
                "text": text,
                "bbox": list(tb.bbox),
                "prob": tb.prob,
            }
        )

    # OCR 텍스트 (1차 정제 완료본)
    for tb in ocrBlocks:
        page = int(tb.page)
        text = (tb.text or "").strip()
        if not text:
            continue

        ocr_by_page.setdefault(page, []).append(text)
        src_ids_by_page.setdefault(page, []).append(tb.block_id)

        blocks_by_page.setdefault(page, []).append(
            {
                "source": "ocr",
                "block_id": tb.block_id,
                "text": text,
                "bbox": list(tb.bbox),
                "prob": tb.prob,
            }
        )

    # 리스트를 최종 문자열로 변환
    pymupdf_texts: dict[int, str] = {}
    ocr_texts: dict[int, str] = {}

    for page, texts in pymupdf_by_page.items():
        pymupdf_texts[page] = "\n".join(texts).strip()

    for page, texts in ocr_by_page.items():
        ocr_texts[page] = "\n".join(texts).strip()

    return pymupdf_texts, ocr_texts, src_ids_by_page, blocks_by_page

# 내부 헬퍼: Task 3 호출 및 페이지 단위 병합
def _runTask3ForPage(
    page: int,
    pymupdf_text: str,
    ocr_text_cleaned: str,
    blocks_for_page: list[dict[str, Any]],
    *,
    chatbotId: str | None = None,
    documentId: str | None = None,
) -> dict[str, Any] | None:
    """
    helper: _runTask3ForPage
    입력:
        - page             : 페이지 번호 (1-base)
        - pymupdf_text     : 해당 페이지 PyMuPDF 텍스트 전체
        - ocr_text_cleaned : 해당 페이지 OCR 1차 정제 텍스트 전체
        - blocks_for_page  : Task 3에 전달할 블록 단위 메타데이터
        - chatbotId/documentId : 로깅용(optional)
    출력:
        - dict | None: Task 3 JSON 응답 전체.
                       (형식 예시는 하단 참고)
                       실패 시 None.

    Task 3를 호출한다.
    INPUT JSON 스펙(예시):
    {
      "page": 1,
      "pymupdf_text": "...",
      "ocr_text_cleaned": "...",
      "blocks": [ { ... }, ... ]
    }

    OUTPUT JSON 스펙(예시):
    {
      "merged_blocks": [
        {
          "text": "병합된 텍스트 한 덩어리",
          "src_block_ids": ["p1_b3", "p1_ocr_b2"]
        },
        ...
      ],
      "merge_log": [
        {
          "src_block_id": "p1_b3",
          "action": "kept",
          "reason": "PyMuPDF 신뢰도 우선"
        },
        ...
      ]
    }
    """
    # 두 입력이 모두 비어 있으면 호출할 필요 없음
    if not (pymupdf_text or ocr_text_cleaned):
        return None

    payload_dict = {
        "page": int(page),
        "pymupdf_text": pymupdf_text,
        "ocr_text_cleaned": ocr_text_cleaned,
        "blocks": blocks_for_page or [],
    }

    payload = json.dumps(
        payload_dict,
        ensure_ascii=False,
    )

    try:
        raw_content = callQwen(
            task_id=3,
            input_payload=payload,
            temperature=0.0,
          # 페이지 단위 병합은 출력이 짧기 때문에 512~1024로 제한하는 것이 안전
            max_tokens=1024,
        )
    except Exception as e:
        logger.exception(
            "[SECOND-REFINE] Task 3 호출 실패 | page=%d chatbot_id=%s document_id=%s error=%s",
            page,
            chatbotId,
            documentId,
            e,
        )
        return None

    try:
        data = parseJson(raw_content)
    except Exception as e:
        logger.exception(
            "[SECOND-REFINE] Task 3 응답 JSON 파싱 실패 | page=%d chatbot_id=%s document_id=%s error=%s raw_preview=%r",
            page,
            chatbotId,
            documentId,
            e,
            (raw_content or "")[:300],
        )
        return None

    merged_blocks = data.get("merged_blocks")
    if not isinstance(merged_blocks, list) or len(merged_blocks) == 0:
        logger.warning(
            "[SECOND-REFINE] Task 3 응답 merged_blocks 비어 있음 | page=%d chatbot_id=%s document_id=%s",
            page,
            chatbotId,
            documentId,
        )
        return None

    logger.info(
        "[SECOND-REFINE] Task 3 페이지 병합 완료 | page=%d merged_blocks=%d",
        page,
        len(merged_blocks),
    )
    return data

# 내부 헬퍼: Task 3 실패 시 fallback 병합
def _fallbackMergePage(
    page: int,
    pymupdf_text: str,
    ocr_text_cleaned: str,
) -> str:
    """
    helper: _fallbackMergePage
    입력:
        - page             : 페이지 번호
        - pymupdf_text     : 해당 페이지 PyMuPDF 텍스트 전체
        - ocr_text_cleaned : 해당 페이지 OCR 1차 정제 텍스트 전체
    출력:
        - str: PyMuPDF + OCR 텍스트를 그대로 이어붙인 문자열

    Task 3 실패 시에는 pymupdf_text + "\\n" + ocr_text_cleaned 를 그대로 이어붙여 사용한다.
    둘 중 하나가 비어 있어도 나머지 하나는 그대로 유지한다.
    """
    pym = (pymupdf_text or "").strip()
    ocr = (ocr_text_cleaned or "").strip()

    if pym and ocr:
        merged = f"{pym}\n{ocr}"
    elif pym:
        merged = pym
    elif ocr:
        merged = ocr
    else:
        merged = ""

    if merged:
        logger.warning(
            "[SECOND-REFINE] Task 3 실패로 fallback 병합 수행 | page=%d len=%d",
            page,
            len(merged),
        )
    else:
        logger.warning(
            "[SECOND-REFINE] Task 3 실패 및 입력 텍스트 없음 | page=%d",
            page,
        )

    return merged

# 공개 함수: 문서 단위 2차 정제(페이지 단위 병합)
def mergeText(
    extraction: PDFExtractionResult,
    ocrBlocks: list[TextBlock],
    *,
    chatbotId: str | None = None,
    documentId: str | None = None,
) -> dict[int, list[MergedTextBlock]]:
    """
    function: mergeText
    입력:
        - extraction : extractPDF 결과 (PyMuPDF 텍스트/이미지 포함)
        - ocrBlocks  : 1차 정제 완료된 OCR TextBlock 리스트
        - chatbotId  : 로깅/메타용(현재 단계에서는 선택적)
        - documentId : 로깅/메타용(현재 단계에서는 선택적)
    출력:
        - dict[int, list[MergedTextBlock]]:
            page 번호를 키로, 해당 페이지의 MergedTextBlock 리스트를 값으로 하는 딕셔너리.
            (페이지당 하나 이상 생성 가능)

    동작 개요:
        1) _buildPageTexts로 페이지별 PyMuPDF/OCR 텍스트 및 블록 메타 집계
        2) 각 페이지에 대해 _runTask3ForPage로 Qwen Task 3 병합 수행
        3) Task 3 실패 또는 빈 응답 시 _fallbackMergePage로 PyMuPDF+OCR 텍스트를 그대로 이어붙임
        4) 최종 merged_blocks를 페이지당 여러 개의 MergedTextBlock로 감싸서 반환
    """
    (
        pymupdf_texts,
        ocr_texts,
        src_ids_by_page,
        blocks_by_page,
    ) = _buildPageTexts(
        extraction=extraction,
        ocrBlocks=ocrBlocks,
    )

    # PyMuPDF 또는 OCR 어느 한쪽에라도 텍스트가 있는 페이지들의 합집합
    all_pages = set(pymupdf_texts.keys()) | set(ocr_texts.keys())
    result: dict[int, list[MergedTextBlock]] = {}

    logger.info(
        "[SECOND-REFINE] 문서 2차 정제 시작(페이지 단위 병합) | pages=%d chatbot_id=%s document_id=%s",
        len(all_pages),
        chatbotId,
        documentId,
    )

    for page in sorted(all_pages):
        pym_text = pymupdf_texts.get(page, "")
        ocr_text = ocr_texts.get(page, "")
        page_blocks = blocks_by_page.get(page, [])

        # 1) Task 3 호출
        task3_data = _runTask3ForPage(
            page=page,
            pymupdf_text=pym_text,
            ocr_text_cleaned=ocr_text,
            blocks_for_page=page_blocks,
            chatbotId=chatbotId,
            documentId=documentId,
        )

        page_result: list[MergedTextBlock] = []

        if task3_data is not None:
            merged_blocks = task3_data.get("merged_blocks") or []
            merge_log = task3_data.get("merge_log")

            for idx, blk in enumerate(merged_blocks):
                text = str(blk.get("text") or "").strip()
                if not text:
                    continue

                src_ids_raw = blk.get("src_block_ids") or []
                if isinstance(src_ids_raw, list):
                    src_ids = [str(s) for s in src_ids_raw]
                else:
                    src_ids = [str(src_ids_raw)]

                merged_block = MergedTextBlock(
                    page=int(page),
                    block_id=f"p{page}_m{idx+1}",
                    text=text,
                    src_block_ids=src_ids,
                    debug_log=merge_log,
                )
                page_result.append(merged_block)

        # 2) Task 3가 실패했거나, 유효한 merged_blocks가 없는 경우 fallback
        if not page_result:
            merged_text = _fallbackMergePage(
                page=page,
                pymupdf_text=pym_text,
                ocr_text_cleaned=ocr_text,
            )

            merged_text = (merged_text or "").strip()
            if not merged_text:
                # 이 페이지에는 최종적으로 쓸 텍스트가 없음
                result[page] = []
                continue

            src_ids = src_ids_by_page.get(page, [])

            merged_block = MergedTextBlock(
                page=int(page),
                block_id=f"p{page}_m1",
                text=merged_text,
                src_block_ids=list(src_ids),
                debug_log=None,
            )
            page_result = [merged_block]

        result[page] = page_result

    logger.info(
        "[SECOND-REFINE] 문서 2차 정제 완료(페이지 단위 병합) | pages=%d",
        len(result),
    )
    return result

__all__ = ["mergeText"]
