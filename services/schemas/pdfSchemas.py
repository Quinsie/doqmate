# services/schemas/pdfSchemas.py

"""
pdfSchemas.py

dataclass:
    TextBlock           | 텍스트 블록 단위 정보
    ImageBlock          | 이미지 블록 단위 정보
    PDFExtractionResult | PDF 하나에 대한 텍스트/이미지 정보
    MaskedPage          | 생성된 이미지와 PDF의 좌표계를 맞추기 위한 정보

PDF 처리에 사용될 구조체들이 기록된 스크립트.
"""
from dataclasses import dataclass
from typing import Any  #  추가

"""
Type Alias: BBox
- Format : (x0, y0, x1, y1)
- x0, y0 : 좌상단(Top-Left) 좌표 (PDF Point 단위)
- x1, y1 : 우하단(Bottom-Right) 좌표 (PDF Point 단위)
"""
BBox = tuple[float, float, float, float]


@dataclass
class TextBlock:
    """
    dataclass: TextBlock
    - page      : 1-base 페이지 번호
    - block_id  : 블록 고유 식별자
    - bbox      : PDF 좌표계 기준의 텍스트 영역 (x0, y0, x1, y1)
    - text      : 노이즈 제거 및 포맷팅이 완료된 정제 텍스트

    PDF 내 포함된 텍스트를 별도 처리하기 위한 구조체.
    """
    page: int
    block_id: str
    bbox: BBox
    text: str
    prob: float | None = None


@dataclass
class ImageBlock:
    """
    dataclass: ImageBlock
    - page          : 1-base 페이지 번호
    - image_id      : 이미지 고유 식별자
    - bbox          : PDF 좌표계 기준의 이미지 영역 (x0, y0, x1, y1)
    - width         : 이미지 원본 가로 픽셀 수
    - height        : 이미지 원본 세로 픽셀 수
    - image_bytes   : 메모리 상의 이미지 바이너리 데이터 (VLM 입력용)
    - image_path    : 서버 내 저장된 이미지 파일 상대 경로(선택)

    PDF 내 포함된 사진을 별도 처리하기 위한 구조체.
    """
    page: int
    image_id: str
    bbox: BBox
    width: int
    height: int
    image_bytes: bytes
    image_path: str | None = None   # 👈 추가된 필드


@dataclass
class PDFExtractionResult:
    """
    dataclass: PDFExtractionResult
    - text_blocks   : 추출된 모든 텍스트 블록의 리스트
    - image_blocks  : 추출된 모든 이미지 블록의 리스트

    단일 PDF 파일에 대한 PyMuPDF 파싱 결과를 총괄하는 컨테이너.
    """
    text_blocks: list[TextBlock]
    image_blocks: list[ImageBlock]


@dataclass
class MaskedPage:
    """
    dataclass: MaskedPage
    - page      : 1-base 페이지 번호
    - image     : OCR 전처리까지 완료된 단일 페이지 이미지 (이진화된 numpy 배열)
    - scaleX    : PDF 좌표계(x) -> 이미지 픽셀 좌표계(x) 스케일 팩터
    - scaleY    : PDF 좌표계(y) -> 이미지 픽셀 좌표계(y) 스케일 팩터
    - pageRect  : PDF 페이지 원본 Rect (PDF 좌표계 기준)

    OCR 단계에서는 image를 사용해 EasyOCR를 수행한다. image는 maskPDF에서 300dpi기준으로 렌더링된다.
    하지만 OCR 결과 bbox는 이미지 픽셀 좌표계로 나오므로, PDF좌표계와 맞지 않아 2차 정제에 문제가 생긴다.
    따라서 기존 np.ndarray만 넘겨주던 방식은 위험하다고 판단하여 추가한 클래스.
    """
    page: int
    image: "np.ndarray"
    scaleX: float
    scaleY: float
    pageRect: "fitz.Rect"


@dataclass
class MergedTextBlock:
    """
    2차 정제(병합) 결과 블록.

    - page          : 페이지 번호
    - block_id      : 병합 결과 블록에 부여하는 논리적 ID (예: p2_m1)
    - text          : 최종 병합된 텍스트
    - src_block_ids : 이 블록을 구성하는 원본 TextBlock들의 block_id 리스트
                      (PyMuPDF + OCR 혼합 가능)
    - debug_log     : Task 3에서 반환한 병합 로그 (merge_log 전체)
                      - list[ { src_block_id, action, reason } ]
    """
    page: int
    block_id: str
    text: str
    src_block_ids: list[str]
    debug_log: list[dict[str, Any]] | None = None
