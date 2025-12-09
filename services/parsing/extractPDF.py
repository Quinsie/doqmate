# services/parsing/extractPDF.py

"""
extractPDF.py

functions:
    extractPDF                  | 이미지/텍스트 추출 함수

helpers:
    _extractText                | 텍스트 추출 헬퍼
    _extractImages              | 이미지 추출 헬퍼
    _filterImagesBySize         | 이미지 1차 필터링 (크기 기반) 헬퍼
    _filterImagesByContainment  | 이미지 2차 필터링 (포함 기반) 헬퍼

PDF파일 경로를 입력으로 받아 텍스트와 이미지를 추출하여 반환하는 스크립트.
"""
import os
import fitz
import logging

from services.schemas.pdfSchemas import (
    TextBlock,
    ImageBlock,
    PDFExtractionResult,
)

logger = logging.getLogger(__name__)

# 이미지 저장 루트 디렉토리 (환경변수로도 변경 가능)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PDF_IMAGE_DIR = os.getenv(
    "PDF_IMAGE_DIR",
    os.path.join(PROJECT_ROOT, "data", "pdf_images"),
)

os.makedirs(PDF_IMAGE_DIR, exist_ok=True)


def _extractText(doc: "fitz.Document") -> list[TextBlock]:
    text_blocks: list[TextBlock] = []
    global_block_idx = 0

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        raw_blocks = page.get_text("blocks")
        page_num = page_index + 1

        for block in raw_blocks:
            if len(block) < 7 or block[6] != 0:
                continue

            try:
                rect = fitz.Rect(block[:4])
                text = (block[4] or "").replace("\n", " ").strip()
                if not text:
                    continue

                bbox = (float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1))
                global_block_idx += 1
                block_id = f"p{page_num}_b{global_block_idx}"

                text_blocks.append(
                    TextBlock(
                        page=page_num,
                        block_id=block_id,
                        bbox=bbox,
                        text=text,
                        prob=None,
                    )
                )
            except Exception as e:
                logger.exception(
                    "텍스트 블록 파싱 중 오류 발생: page=%d block=%r error=%s",
                    page_num,
                    block,
                    e,
                )
                continue

    logger.info(
        "텍스트 블록 추출 완료: total_blocks=%d",
        len(text_blocks),
    )
    return text_blocks


def _filterImagesBySize(page: "fitz.Page"):
    min_width = 100
    min_height = 100

    before = 0
    image_candidates = []
    for img_info in page.get_images(full=True):
        before += 1
        try:
            xref = img_info[0]
            width = img_info[2]
            height = img_info[3]

            if width >= min_width and height >= min_height:
                bbox = page.get_image_bbox(img_info)
                image_candidates.append(
                    {
                        "xref": xref,
                        "width": width,
                        "height": height,
                        "bbox": bbox,
                    }
                )

        except Exception as e:
            logger.exception(
                "이미지 후보 필터링 중 오류 발생: page=%d img_info=%r error=%s",
                page.number + 1,
                img_info,
                e,
            )
            continue

    logger.info(
        "크기 관계 필터링 완료: before=%d after=%d",
        before,
        len(image_candidates),
    )
    return image_candidates


def _filterImagesByContainment(candidates):
    if not candidates:
        return []

    indices_to_remove = set()
    num_candidates = len(candidates)

    for i in range(num_candidates):
        if i in indices_to_remove:
            continue
        bbox_i = candidates[i]["bbox"]

        for j in range(num_candidates):
            if i == j or j in indices_to_remove:
                continue

            bbox_j = candidates[j]["bbox"]

            if bbox_j.contains(bbox_i):
                indices_to_remove.add(i)
                break
            elif bbox_i.contains(bbox_j):
                indices_to_remove.add(j)

    final_candidates = [
        candidate
        for idx, candidate in enumerate(candidates)
        if idx not in indices_to_remove
    ]

    logger.info(
        "포함 관계 필터링 완료: before=%d after=%d",
        len(candidates),
        len(final_candidates),
    )
    return final_candidates


def _extractImages(
    doc: "fitz.Document",
    pdf_path: str,
    documentId: str,
) -> list[ImageBlock]:

    image_blocks: list[ImageBlock] = []

    pdf_image_root = os.path.join(PDF_IMAGE_DIR, documentId)
    os.makedirs(pdf_image_root, exist_ok=True)

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        page_num = page_index + 1

        candidates = _filterImagesBySize(page=page)
        filtered_candidates = _filterImagesByContainment(candidates)

        # 추가: 동일 bbox 중복 제거 (페이지 단위)
        seen_bboxes = set()

        local_img_idx = 0
        for candidate in filtered_candidates:
            try:
                xref = candidate["xref"]
                width = candidate["width"]
                height = candidate["height"]
                bbox_rect = candidate["bbox"]

                # === bbox dedup key ===
                bbox_key = (
                    round(float(bbox_rect.x0), 1),
                    round(float(bbox_rect.y0), 1),
                    round(float(bbox_rect.x1), 1),
                    round(float(bbox_rect.y1), 1),
                )
                if bbox_key in seen_bboxes:
                    continue
                seen_bboxes.add(bbox_key)

                # 이미지 추출
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image.get("ext", "png")

                bbox = (
                    float(bbox_rect.x0),
                    float(bbox_rect.y0),
                    float(bbox_rect.x1),
                    float(bbox_rect.y1),
                )

                local_img_idx += 1
                image_id = f"p{page_num}_img{local_img_idx}"

                filename = f"{image_id}.{ext}"
                abs_path = os.path.join(pdf_image_root, filename)

                try:
                    with open(abs_path, "wb") as f:
                        f.write(image_bytes)
                except Exception as e:
                    logger.exception(
                        "이미지 파일 저장 실패: page=%d image_id=%s path=%s error=%s",
                        page_num,
                        image_id,
                        abs_path,
                        e,
                    )
                    image_path_rel = None
                else:
                    image_path_rel = os.path.join(documentId, filename)

                image_blocks.append(
                    ImageBlock(
                        page=page_num,
                        image_id=image_id,
                        bbox=bbox,
                        width=width,
                        height=height,
                        image_bytes=image_bytes,
                        image_path=image_path_rel,
                    )
                )

            except Exception as e:
                logger.exception(
                    "이미지 추출 중 오류 발생: page=%d xref=%r error=%s",
                    page_num,
                    candidate.get("xref"),
                    e,
                )
                continue

    logger.info(
        "이미지 블록 추출 완료: total_blocks=%d (base_dir=%s)",
        len(image_blocks),
        PDF_IMAGE_DIR,
    )
    return image_blocks


def extractPDF(pdf_path: str, documentId: str) -> PDFExtractionResult:
    logger.info("PDF 추출 시작: pdf_path=%s document_id=%s", pdf_path, documentId)

    doc = fitz.open(pdf_path)
    try:
        text_blocks = _extractText(doc)
        image_blocks = _extractImages(
            doc=doc,
            pdf_path=pdf_path,
            documentId=documentId,
        )
    finally:
        doc.close()

    logger.info(
        "PDF 추출 완료: pdf_path=%s document_id=%s text_blocks=%d image_blocks=%d",
        pdf_path,
        documentId,
        len(text_blocks),
        len(image_blocks),
    )

    return PDFExtractionResult(
        text_blocks=text_blocks,
        image_blocks=image_blocks,
    )


__all__ = ["extractPDF"]
