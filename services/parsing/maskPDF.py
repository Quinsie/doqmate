# services/parsing/maskPDF.py

"""
maskPDF.py

functions:
    maskPDF             | PDF 페이지 렌더링 후 텍스트/이미지 영역을 마스킹 및 전처리

helpers:
    _renderPage         | PDF 페이지를 고정 DPI로 렌더링
    _collectPageBBoxes  | 페이지별 텍스트/이미지 bbox 수집
    _maskPage           | 페이지 이미지 위에 bbox 영역 마스킹
    _preprocessForOCR   | OCR 목적의 전처리(그레이스케일, 노이즈 제거, 블러, 이진화)

PDF 경로와 extractPDF의 결과를 입력으로 받아 각 페이지를 렌더링.
미리 추출된 텍스트/이미지 영역을 흰색으로 마스킹 및 이진화 (OCR 전처리)
이후 좌표계 재변환에 필요한 메타데이터를 MaskedPage 형태로 반환하는 스크립트.
"""
import cv2
import fitz
import logging
import numpy as np

from services.schemas.pdfSchemas import (
    BBox,
    MaskedPage,
    PDFExtractionResult,
)

logger = logging.getLogger(__name__)

# Global VARs
RENDER_DPI = 300
MASK_COLOR = (255, 255, 255)

def _renderPage(page: "fitz.Page") -> "np.ndarray":
    """
    helper: _renderPage
    입력: PyMuPDF 페이지 객체, 출력: OpenCV BGR 이미지

    페이지를 렌더링하고 numpy 배열로 변환한다.
    """
    pix = page.get_pixmap(dpi=RENDER_DPI)

    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)

    if pix.n == 4: image = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3: image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    elif pix.n == 1: image = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
    else:  # 예상 밖 채널 수인 경우 그대로 반환 (후속 단계에서 문제 발생 시 로깅으로 확인)
        logger.warning(
            "예상 밖 채널 수(pix.n=%d)를 가진 페이지 렌더링 결과입니다. 그대로 사용합니다.",
            pix.n,
        )
        image = img_array

    return image

def _collectPageBBoxes(
    extraction: PDFExtractionResult,
) -> tuple[dict[int, list[BBox]], dict[int, list[BBox]]]:
    """
    helper: _collectPageBBoxes
    입력: PDFExtractionResult, 출력: (텍스트 bbox dict, 이미지 bbox dict)

    extractPDF(...) 결과에서 페이지별 텍스트/이미지 bbox를 모은다.
    - key: page 번호(1-base)
    - value: [(x0, y0, x1, y1), ...] 리스트
    """
    textByPage: dict[int, list[BBox]] = {}
    imageByPage: dict[int, list[BBox]] = {}

    for tb in extraction.text_blocks:
        textByPage.setdefault(tb.page, []).append(tb.bbox)
    for ib in extraction.image_blocks:
        imageByPage.setdefault(ib.page, []).append(ib.bbox)

    return textByPage, imageByPage

def _maskPage(
    image: "np.ndarray",
    pageRect: "fitz.Rect",
    bboxes: list[BBox],
) -> None:
    """
    helper: _maskPage
    입력:
        image: OpenCV BGR 이미지 (in-place 수정)
        pageRect: PDF 페이지의 좌표 정보
        bboxes: PDF 좌표계 기준 bbox 리스트
    출력: 없음 (image를 직접 수정, void)

    PDF 좌표계 기준 bbox를 렌더링된 이미지 좌표계로 스케일링한 뒤 해당 영역을 MASK_COLOR로 채워 마스킹한다.
    """
    if image is None or image.size == 0 or not bboxes:
        return

    height, width, _ = image.shape

    scaleX = width / float(pageRect.width)
    scaleY = height / float(pageRect.height)

    for bbox in bboxes:
        try:
            x0, y0, x1, y1 = bbox
        except Exception as e:
            logger.exception("bbox 파싱 중 오류 발생: bbox=%r error=%s", bbox, e)
            continue

        x0_px = int(x0 * scaleX)
        y0_px = int(y0 * scaleY)
        x1_px = int(x1 * scaleX)
        y1_px = int(y1 * scaleY)

        # 좌표 정규화
        x0_px, x1_px = sorted((x0_px, x1_px))
        y0_px, y1_px = sorted((y0_px, y1_px))

        cv2.rectangle(image, (x0_px, y0_px), (x1_px, y1_px), MASK_COLOR, thickness=-1)

def _preprocessForOCR(image: "np.ndarray") -> "np.ndarray":
    """
    helper: _preprocessForOCR
    입력: 마스킹까지 끝난 BGR 이미지, 출력: OCR용 이진화 이미지

    OCR을 위한 전처리 파이프라인.
    - BGR -> GRAY
    - fastNlMeansDenoising으로 노이즈 제거
    - GaussianBlur로 부드럽게 처리
    - adaptiveThreshold로 이진화
    """
    # 이미지 예외처리
    if image is None or image.size == 0:
        return image

    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        logger.exception("그레이스케일 변환 중 오류 발생: error=%s", e)
        return image

    try:
        denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
        blurred = cv2.GaussianBlur(denoised, (3, 3), 0)
        binary = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            15,
        )
    # 전처리 실패 시 최소한 GRAY 이미지는 반환하여 OCR이 시도는 가능하도록 함
    except Exception as e:
        logger.exception("이미지 전처리(노이즈 제거/블러/이진화) 중 오류 발생: error=%s", e)
        return gray

    return binary

def maskPDF(pdfPath: str, extraction: PDFExtractionResult) -> list[MaskedPage]:
    """
    function: maskPDF
    입력:
        pdfPath     : 마스킹 대상 PDF 파일 경로
        extraction  : extractPDF 반환값
    출력:
        maskedPages : 각 페이지별 OCR용 이미지 및 좌표 변환 메타데이터를 담은 MaskedPage 리스트

    동작 개요:
        1) PDF를 열어 페이지 단위로 렌더링
        2) 각 페이지에 대해 텍스트/이미지 bbox를 수집
        3) 해당 bbox 영역을 MASK_COLOR(흰색)로 마스킹 :: 이유는... 검정이면 글자로 오인할 수도 있다고 판단했습니다.
        4) 마스킹된 이미지를 OCR에 적합한 형태로 전처리(그레이스케일 + 노이즈 제거 + 블러 + 이진화)
        5) 각 페이지에 대해 (page, image, scaleX, scaleY, pageRect)를 담은 MaskedPage를 생성해 반환
    """
    logger.info("PDF 마스킹 및 전처리 시작: pdf_path=%s", pdfPath)

    try:
        doc = fitz.open(pdfPath)
    except Exception as e:
        logger.exception("PDF 파일 조회 중 오류 발생: pdf_path=%s error=%s", pdfPath, e)
        raise

    maskedPages: list[MaskedPage] = []

    try:
        textByPage, imageByPage = _collectPageBBoxes(extraction)
        numPages = len(doc)

        for pageIndex in range(numPages):
            pageNum = pageIndex + 1

            try:
                page = doc.load_page(pageIndex)
            except Exception as e:
                logger.exception(
                    "페이지 로드 중 오류 발생: page_index=%d error=%s",
                    pageIndex,
                    e,
                )
                continue

            try:
                image = _renderPage(page)
            except Exception as e:
                logger.exception("페이지 렌더링 중 오류 발생: page=%d error=%s", pageNum, e)
                continue

            # 렌더링 결과 기준 스케일 팩터 계산
            try:
                height, width, _ = image.shape
                scaleX = width / float(page.rect.width)
                scaleY = height / float(page.rect.height)
            except Exception as e:
                logger.exception(
                    "페이지 스케일 계산 중 오류 발생: page=%d error=%s",
                    pageNum,
                    e,
                )
                continue

            # 해당 페이지의 텍스트/이미지 bbox 적용
            pageTextBBoxes = textByPage.get(pageNum, [])
            pageImageBBoxes = imageByPage.get(pageNum, [])

            if pageTextBBoxes: _maskPage(image=image, pageRect=page.rect, bboxes=pageTextBBoxes)
            if pageImageBBoxes: _maskPage(image=image, pageRect=page.rect, bboxes=pageImageBBoxes)

            # OCR 전처리
            processed = _preprocessForOCR(image)

            maskedPages.append(
                MaskedPage(
                    page=pageNum,
                    image=processed,
                    scaleX=scaleX,
                    scaleY=scaleY,
                    pageRect=page.rect,
                )
            )

        logger.info(
            "PDF 마스킹 및 전처리 완료: pdf_path=%s total_pages=%d processed_pages=%d",
            pdfPath,
            numPages,
            len(maskedPages),
        )
    
    finally: doc.close()
    return maskedPages

__all__ = ["maskPDF"]