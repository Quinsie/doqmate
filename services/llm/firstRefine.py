# services/llm/firstRefine.py

"""
firstRefine.py

functions:
    cleanOcrTextRaw       | 디버그/단일 문자열 테스트용
    cleanOcrTextBlocks    | TextBlock 리스트 단위 1차 정제

helpers:
    _safeCleanText        | LLM 호출 및 JSON 파싱 래퍼 (실패 시 원문 반환)

OCR 단계에서 생성된 텍스트를 Qwen LLM(Task 0)을 통해 1차 정제하는 스크립트.
"""
from __future__ import annotations

import json
import logging

from services.llm.client import callQwen, parseJson
from services.schemas.pdfSchemas import TextBlock

logger = logging.getLogger(__name__)

def _safeCleanText(raw_text: str) -> str:
    """
    helper: _safeCleanText
    입력: OCR 원문 텍스트 문자열
    출력: 정제된 텍스트 문자열 (실패 시 원문 그대로 반환)

    Qwen Task 0(OCR 1차 정제)을 호출하고, 결과 JSON을 파싱하는 헬퍼.
    - cleaned_text가 비어 있거나 파싱 실패 시 raw_text를 그대로 반환한다.
    - 예외는 내부에서 로깅만 하고 상위로 전파하지 않는다.
    """
    text = (raw_text or "").strip()
    if not text:
        return raw_text

    payload = json.dumps(
        {
            "raw_text": raw_text,
        },
        ensure_ascii=False,
    )

    try:
        raw_content = callQwen(
            task_id=0,
            input_payload=payload,
            temperature=0.0,
            max_tokens=2048,
        )
    except Exception as e:
        logger.exception("[LLM] OCR 1차 정제 호출 실패, 원문 사용: %s", e)
        return raw_text

    try:
        data = parseJson(raw_content)
        cleaned = str(data.get("cleaned_text", "")).strip()
        if not cleaned:
            logger.warning(
                "[LLM] OCR 1차 정제 결과가 비어 있음, 원문 사용 | raw_len=%d",
                len(raw_text),
            )
            return raw_text
        return cleaned
    except Exception as e:
        logger.exception(
            "[LLM] OCR 1차 정제 JSON 파싱 실패, 원문 사용: %s | raw_preview=%r",
            e,
            raw_content[:300],
        )
        return raw_text

def cleanOcrTextRaw(raw_text: str) -> str:
    """
    function: cleanOcrTextRaw [for Debug]
    입력: OCR 원문 텍스트 문자열
    출력: 정제된 텍스트 문자열

    디버그/테스트용 단일 문자열 OCR 1차 정제 함수.
    - 내부적으로 _safeCleanText를 호출한다.
    - 실패 시 원문을 그대로 반환한다.
    """
    cleaned = _safeCleanText(raw_text)
    logger.info(
        "[OCR-TASK0] 단일 텍스트 정제 완료 | raw_len=%d cleaned_len=%d",
        len(raw_text or ""),
        len(cleaned or ""),
    )
    return cleaned

def cleanOcrTextBlocks(blocks: list[TextBlock]) -> list[TextBlock]:
    """
    function: cleanOcrTextBlocks
    입력: runOCR 등에서 생성된 TextBlock 리스트
    출력: 텍스트만 1차 정제된 TextBlock 리스트 (동일한 길이/순서 유지)

    메타 정보는 그대로 유지하고 text만 정제.
    각 블록별로 Qwen Task 0을 호출하되, 오류 발생 시 해당 블록은 원문 text를 유지한다.
    """
    if not blocks:
        logger.info("[OCR-TASK0] 입력 TextBlock이 비어 있음, 그대로 반환")
        return blocks

    cleaned_blocks: list[TextBlock] = []
    total = len(blocks)
    changed_count = 0

    logger.info(
        "[OCR-TASK0] TextBlock 리스트 1차 정제 시작 | total_blocks=%d",
        total,
    )

    for idx, block in enumerate(blocks):
        original_text = block.text or ""
        stripped = original_text.strip()

        # 내용이 없으면 LLM 호출 없이 그대로 사용
        if not stripped:
            cleaned_blocks.append(block)
            continue

        cleaned_text = _safeCleanText(original_text)
        if cleaned_text != original_text:
            changed_count += 1

        data = dict(block.__dict__)
        data["text"] = cleaned_text
        cleaned_block = TextBlock(**data)
        cleaned_blocks.append(cleaned_block)

        if (idx + 1) % 50 == 0:
            logger.debug(
                "[OCR-TASK0] 진행 상황 | processed=%d/%d changed=%d",
                idx + 1,
                total,
                changed_count,
            )

    logger.info(
        "[OCR-TASK0] TextBlock 리스트 1차 정제 완료 | total=%d changed=%d",
        total,
        changed_count,
    )

    return cleaned_blocks

__all__ = [
    "cleanOcrTextRaw",
    "cleanOcrTextBlocks",
]