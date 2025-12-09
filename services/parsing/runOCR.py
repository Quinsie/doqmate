# services/parsing/runOCR.py

"""
runOCR.py

functions:
    runOCR              | 마스킹/전처리된 페이지 이미지에 EasyOCR를 수행해 TextBlock 리스트로 반환

helpers:
    _getReader          | EasyOCR 커스텀 리더기 초기화/캐시
    _convertBBoxToPdf   | EasyOCR 픽셀 좌표 bbox를 PDF 좌표계 BBox로 변환
    _runPage            | 단일 페이지에 대해 OCR 수행 및 TextBlock 리스트 생성

maskPDF에서 반환된 MaskedPage의 이미지 정보를 기반으로 OCR 수행.
OCR 결과를 PDF 좌표계로 스케일링 진행한 뒤 TextBlock형태로 반환.
커스텀 EasyOCR 모델을 교체하면 기본 모델도 사용 가능하다.
탐지모델은 기본 CRAFT모델 이용.
"""
import os
import torch
import easyocr
import logging
import numpy as np

from services.schemas.pdfSchemas import (
    BBox,
    MaskedPage,
    TextBlock,
)

logger = logging.getLogger(__name__)

# Global VARs
_ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_EASYOCR_MODEL_DIR = os.path.join(_ROOT_DIR, "models", "EasyOCR", "model")
_EASYOCR_NETWORK_DIR = os.path.join(_ROOT_DIR, "models", "EasyOCR", "network")
_EASYOCR_NETWORK_NAME = "doqmateOCR"
_OCR_READER: "easyocr.Reader | None" = None # 모듈 단위 캐시 (모델을 한 번만 로드하고 재사용을 위함)

def _getReader() -> "easyocr.Reader":
    """
    helper: _getReader
    입력: 없음, 출력: EasyOCR Reader 인스턴스

    EasyOCR 호출 헬퍼. 모듈 레벨에서 한 번만 호출.
    """
    global _OCR_READER

    if _OCR_READER is not None: return _OCR_READER

    use_gpu = torch.cuda.is_available()
    logger.info(
        "EasyOCR Reader 초기화 시작: gpu=%s model_dir=%s network_dir=%s network_name=%s",
        use_gpu,
        _EASYOCR_MODEL_DIR,
        _EASYOCR_NETWORK_DIR,
        _EASYOCR_NETWORK_NAME,
    )

    if not os.path.isdir(_EASYOCR_MODEL_DIR):
        logger.warning(
            "EasyOCR model_storage_directory가 존재하지 않습니다: %s",
            _EASYOCR_MODEL_DIR,
        )
    if not os.path.isdir(_EASYOCR_NETWORK_DIR):
        logger.warning(
            "EasyOCR user_network_directory가 존재하지 않습니다: %s",
            _EASYOCR_NETWORK_DIR,
        )

    try:
        _OCR_READER = easyocr.Reader(
            ["ko"],
            gpu = use_gpu,
            model_storage_directory = _EASYOCR_MODEL_DIR,
            user_network_directory = _EASYOCR_NETWORK_DIR,
            recog_network = _EASYOCR_NETWORK_NAME,
        )
    except Exception as e:
        logger.exception("EasyOCR Reader 초기화 실패: error=%s", e)
        raise

    logger.info("EasyOCR Reader 초기화 완료")
    return _OCR_READER

def _convertBBoxToPdf(maskedPage: MaskedPage, bbox_points) -> BBox:
    """
    helper: _convertBBoxToPdf
    입력:
        maskedPage  : 해당 페이지의 마스킹/렌더링 메타데이터
        bbox_points : EasyOCR bbox 포인트(4점)
    출력:
        BBox 튜플(float x0, y0, x1, y1) - PDF 좌표계 기준

    렌더링 이미지 기준 좌표계 BBox를 PDF 좌표계로 변환한다.
    """
    try:
        xs = [float(p[0]) for p in bbox_points]
        ys = [float(p[1]) for p in bbox_points]
    except Exception as e:
        logger.exception(
            "OCR bbox 포인트 파싱 중 오류 발생: page = %d bbox = %r error = %s",
            maskedPage.page,
            bbox_points,
            e,
        )
        return 0.0, 0.0, 0.0, 0.0

    x0_px = min(xs)
    y0_px = min(ys)
    x1_px = max(xs)
    y1_px = max(ys)

    if maskedPage.scaleX == 0 or maskedPage.scaleY == 0:
        logger.error(
            "scaleX/scaleY가 0입니다. PDF 좌표로 변환할 수 없습니다: page = %d scaleX = %f scaleY = %f",
            maskedPage.page,
            maskedPage.scaleX,
            maskedPage.scaleY,
        )
        return 0.0, 0.0, 0.0, 0.0

    x0_pdf = x0_px / maskedPage.scaleX
    y0_pdf = y0_px / maskedPage.scaleY
    x1_pdf = x1_px / maskedPage.scaleX
    y1_pdf = y1_px / maskedPage.scaleY

    return x0_pdf, y0_pdf, x1_pdf, y1_pdf

def _runPage(
    maskedPage: MaskedPage,
    reader: "easyocr.Reader",
) -> list[TextBlock]:
    """
    helper: _runPage
    입력:
        maskedPage : 단일 페이지 OCR용 이미지 및 스케일 메타데이터
        reader     : EasyOCR Reader 인스턴스
    출력:
        해당 페이지에서 인식된 TextBlock 리스트

    MaskedPage에서 렌더링된 페이지를 꺼내 OCR 수행
    """
    textBlocks: list[TextBlock] = []

    image = maskedPage.image
    if image is None or image.size == 0:
        logger.warning("빈 페이지 이미지가 전달되었습니다: page=%d", maskedPage.page)
        return textBlocks

    try:
        result = reader.readtext(image, detail=1, paragraph=False)
    except Exception as e:
        logger.exception(
            "EasyOCR readtext 중 오류 발생: page=%d error=%s",
            maskedPage.page,
            e,
        )
        return textBlocks

    if not result:
        logger.info("OCR 결과 없음: page=%d", maskedPage.page)
        return textBlocks

    localIdx = 0
    for entry in result:
        try:
            # EasyOCR 결과 형식: (bbox_points(4점), text(str), prob(float))
            bbox_points, text, prob = entry
        except Exception as e:
            logger.exception(
                "EasyOCR 결과 파싱 중 오류 발생: page=%d entry=%r error=%s",
                maskedPage.page,
                entry,
                e,
            )
            continue

        text = (text or "").strip()
        if not text:
            continue

        bbox_pdf = _convertBBoxToPdf(maskedPage, bbox_points)
        localIdx += 1
        blockId = f"p{maskedPage.page}_ocr_b{localIdx}"

        try:
            prob_val = float(prob)
        except Exception:
            prob_val = None

        textBlocks.append(
            TextBlock(
                page=maskedPage.page,
                block_id=blockId,
                bbox=bbox_pdf,
                text=text,
		prob=prob_val,
            )
        )

    logger.info(
        "페이지 OCR 완료: page=%d blocks=%d",
        maskedPage.page,
        len(textBlocks),
    )
    return textBlocks

def runOCR(maskedPages: list[MaskedPage]) -> list[TextBlock]:
    """
    function: runOCR
    입력:
        maskedPages : maskPDF(...)에서 반환된 MaskedPage 리스트
    출력:
        ocrBlocks   : EasyOCR를 통해 인식된 TextBlock 리스트

    MaskedPage를 받아 OCR 수행 이후 정보를 TextBlock형태로 반환
    """
    logger.info("runOCR 시작: total_pages=%d", len(maskedPages))

    if not maskedPages:
        logger.warning("runOCR에 전달된 MaskedPage 리스트가 비어 있습니다.")
        return []

    reader = _getReader()
    allBlocks: list[TextBlock] = []

    for maskedPage in maskedPages:
        pageBlocks = _runPage(
            maskedPage=maskedPage,
            reader=reader,
        )
        allBlocks.extend(pageBlocks)

    logger.info(
        "runOCR 완료: total_pages=%d total_blocks=%d",
        len(maskedPages),
        len(allBlocks),
    )

    del reader
    torch.cuda.empty_cache()

    return allBlocks

__all__ = ["runOCR"]
