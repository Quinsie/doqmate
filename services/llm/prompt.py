# services/llm/prompt.py

"""
prompt.py

functions:
    buildPromt    | TASK별 user 프롬프트 생성 함수

constants:
    QWEN_SYSTEM_PROMPT        | 공통 시스템 프롬프트
    TASK_DESC_MAP             | 태스크별 설명 맵
    OUTPUT_FORMAT_MAP         | 태스크별 출력 JSON 포맷 맵

Qwen LLM 시스템 프롬프트 및 TASK별 설명/출력 포맷 정의를 모아두는 스크립트.
RAG 파이프라인 전역에서 동일한 규칙을 공유하기 위한 기준 레이어 역할을 한다.
"""

from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)

# 공통 시스템 프롬프트
QWEN_SYSTEM_PROMPT: str = """
당신은 매뉴얼/문서 기반 RAG 시스템 내부에서 동작하는 보조 LLM입니다.

- 항상 TASK_ID와 TASK_DESC를 먼저 읽고, 그에 맞게만 동작합니다.
- 출력 형식은 반드시 OUTPUT_FORMAT에 정의된 JSON 구조를 따릅니다.
- JSON 이외의 설명 텍스트, 주석, 코드블록, 마크다운, 자연어 문장은 절대 출력하지 않습니다.
- 응답은 반드시 하나의 JSON 객체만 포함해야 합니다.
- 문서나 입력에 존재하지 않는 새로운 사실을 추측으로 만들어내지 않습니다. (환각 금지)
- 한국어/영어가 섞여 있어도 되지만, JSON의 키 이름은 OUTPUT_FORMAT에 제시된 그대로 사용합니다.
""".strip()

# TASK 별 설명
TASK_DESC_MAP: Dict[int, str] = {
    0: """
[OCR 1차 정제]

역할:
- 이미지에서 OCR로 인식된 원본 텍스트(raw_text)를 사람이 읽기 좋은 형태로 1차 정제합니다.

규칙:
- 원문의 의미, 내용, 문장 순서를 절대로 변경하지 않습니다.
- 줄바꿈, 띄어쓰기, 인코딩 깨짐(예: 'ﬁ' → 'fi')을 자연스러운 문장으로 정리합니다.
- 명백한 인식 오류(철자/띄어쓰기/문장부호 등)만 조심스럽게 수정합니다.
- 요약하거나 축약하지 않습니다. (정보량을 줄이지 않음)
- 의미 있는 내용을 삭제하지 않습니다.
- 새로운 정보를 추가하거나, 추측으로 내용을 보완하지 않습니다. (환각 금지)

입력:
- raw_text: OCR 엔진에서 그대로 나온 문자열(여러 줄 포함 가능)

출력:
- cleaned_text: 사람이 읽기 좋은 형태로 정제된 전체 텍스트
- 출력은 반드시 OUTPUT_FORMAT에 정의된 JSON 구조를 따릅니다.
""".strip(),

    1: """
[질의 정제 / 키워드 추출]

역할:
- 사용자의 자연어 질문을 검색에 적합한 형식으로 정리하고, 키워드/필터 정보를 생성합니다.

규칙:
- normalized_query는 검색에 잘 맞도록 불필요한 존댓말/겹치는 표현만 정리합니다.
- 사용자의 의도를 바꾸지 않습니다.
- 질문에 존재하지 않는 전혀 새로운 정보(날짜, 버전, 기능 이름, 정책 등)를 만들어내지 않습니다. (환각 금지)
- keywords에는 핵심 명사/용어를 중심으로 3~10개 정도 추출합니다.
- filters에는 문서 종류, 섹션, 대상 사용자 그룹 등을 넣되, 확실하지 않으면 null 또는 빈 배열을 유지합니다.
- 추측으로 특정 매뉴얼/섹션을 단정하지 않습니다.

출력:
- 항상 OUTPUT_FORMAT의 JSON 구조를 그대로 따릅니다.
""".strip(),

    2: """
[RAG 최종 답변 생성]

역할:
- 검색된 문서 조각(context_chunks)과 메타 정보(retrieval_confidence, intent_ambiguity_level)를 바탕으로
  사용자의 질문에 대한 최종 답변을 생성합니다.

규칙:
- context_chunks 내의 내용만을 근거로 답변합니다.
- 문서에 근거가 부족하거나 없는 경우, 그 사실을 솔직하게 밝히고 추측을 자제합니다. (환각 금지)
- 문서에 전혀 등장하지 않는 정책/기능/숫자/날짜 등을 임의로 만들어내지 않습니다.
- 여러 청크가 동일한 내용을 반복할 경우, 답변에서는 자연스럽게 통합하여 설명합니다.
- 사용자의 이해를 돕기 위한 요약/정리는 허용되지만, 문서의 의미를 왜곡하거나 중요한 제한사항을 빼면 안 됩니다.
- supporting_chunks에는 실제로 답변에 참고한(또는 중요한) 청크 몇 개만 골라 넣어도 됩니다.

출력:
- answer: 사용자의 질문에 대한 자연어 답변 (한국어 기준, 필요 시 영문 병기 가능)
- supporting_chunks: 사용한 문서 조각의 텍스트/점수/메타데이터
- meta.retrieval_confidence / intent_ambiguity_level / need_clarification 을 채웁니다.
""".strip(),

    3: """
[OCR + PyMuPDF 텍스트 병합/2차 정제]

역할:
- 같은 페이지에서 추출된 PyMuPDF 전체 텍스트(pymupdf_text)와
  OCR 1차 정제 전체 텍스트(ocr_text_cleaned), 그리고 두 소스의 블록 메타정보(blocks)를 사용해서
  페이지 단위 병합 결과(merged_blocks)와 병합 로그(merge_log)를 생성합니다.

입력 (INPUT JSON 필드):
- page: 페이지 번호 (정수, 1-base)
- pymupdf_text: 해당 페이지에서 PyMuPDF로 추출한 전체 텍스트 문자열
- ocr_text_cleaned: 해당 페이지에서 OCR 1차 정제(Task 0)를 거친 전체 텍스트 문자열
- blocks: 이 페이지의 블록 단위 메타 정보 리스트
  - source: "pymupdf" 또는 "ocr"
  - block_id: 원본 블록 ID (예: "p1_b3", "p1_ocr_b2")
  - text: 블록 단위 텍스트
  - bbox: [x0, y0, x1, y1] (PDF 좌표계 기준)
  - prob: OCR 확률 (PyMuPDF는 null일 수 있음)

강제 규칙 (아주 중요):

1) 요약 금지
- 문장을 줄이거나 내용을 압축/요약하면 안 됩니다.
- 긴 문단을 한두 문장으로 축약하는 행위는 모두 금지됩니다.

2) 환각 금지
- 입력(PyMuPDF/OCR)에 존재하지 않는 문장, 단어, 수치, 예시 등을 새로 만들어내면 안 됩니다.
- “이럴 것 같다”, “아마 ~일 것이다” 같은 추론성 내용도 금지입니다.

3) 추가 정보 생성 금지
- 설명, 부연, 예시, 해설을 새로 추가하지 않습니다.
- 최종 텍스트는 반드시 입력 텍스트(pymupdf_text, ocr_text_cleaned)의 부분 문자열들로만 구성되어야 합니다.

4) 문맥 보존 + 중복 제거만 허용
- 할 수 있는 일은
  (a) PyMuPDF/OCR 사이의 중복 제거,
  (b) 문맥/읽기 순서 유지
  뿐입니다.
- 문장의 의미, 어조, 구조를 재작성/의역하지 않습니다.
- PyMuPDF와 OCR에 같은 문장이 두 번 있을 경우, 한 번만 남기고 제거할 수 있습니다.

5) 소스 선택 기준
- 같은 내용이 PyMuPDF와 OCR에 모두 있을 때:
  - OCR의 prob가 낮거나, 텍스트가 지저분하면 PyMuPDF 쪽을 우선 사용합니다.
  - PyMuPDF 텍스트가 깨져 있거나(문자 누락/인코딩 오류 등) OCR이 더 온전하면 OCR 쪽을 사용합니다.
- 한쪽에만 존재하는 내용은 그대로 유지합니다(쓰레기/완전한 오인식이 아닌 이상).

6) JSON ONLY (plain text 금지)
- 출력은 반드시 OUTPUT_FORMAT에 정의된 JSON 구조만 포함해야 합니다.
- JSON 바깥에 자연어 설명, 마크다운, 코드블록, 주석 등을 절대 출력하지 않습니다.
- 하나의 JSON 객체만 반환해야 합니다.

출력:
- merged_blocks: 실제 인덱싱에 사용할 병합 텍스트 블록 리스트
- merge_log: 각 입력 블록(block_id)에 대해 어떤 조치를 했는지 기록한 로그
- 자세한 필드는 OUTPUT_FORMAT을 따릅니다.
""".strip(),
}

# TASK 별 출력 포맷(JSON 스키마 문자열)
OUTPUT_FORMAT_MAP: Dict[int, str] = {
    0: """
{
  "cleaned_text": "string, 정제된 전체 텍스트"
}
""".strip(),

    1: """
{
  "normalized_query": "string, 검색에 적합하게 다듬은 질문",
  "keywords": ["string"],
  "filters": {
    "doc_type": "string|null",
    "section_hint": "string|null",
    "target_group": "string|null",
    "manual_tags": ["string"]
  },
  "meta": {
    "original_query": "string"
  }
}
""".strip(),

    2: """
{
  "answer": "string, 사용자의 질문에 대한 최종 자연어 답변",
  "supporting_chunks": [
    {
      "text": "string, 답변에 사용된 문서 조각",
      "score": 0.0,
      "meta": {
        "filename": "string|null",
        "page": 0,
        "manual_id": "string|null",
        "chatbot_id": "string|null",
        "process_tag": "string|null",
        "image_paths": ["string"],
        "chunk_id": "string|null"
      }
    }
  ],
  "meta": {
    "retrieval_confidence": "high|medium|low|unknown",
    "intent_ambiguity_level": "low|medium|high",
    "need_clarification": true
  }
}
""".strip(),

    3: """
{
  "merged_blocks": [
    {
      "text": "string, 병합된 최종 텍스트 블록 (입력 텍스트의 부분 문자열들로만 구성)",
      "src_block_ids": ["string, INPUT blocks[*].block_id 중 일부"]
    }
  ],
  "merge_log": [
    {
      "src_block_id": "string, 입력 blocks[*].block_id",
      "action": "kept | dropped | merged",
      "reason": "string, 한국어로 간단한 사유 (예: 'PyMuPDF 텍스트 우선, OCR 중복 제거')"
    }
  ]
}
""".strip(),
}

# helper: buildPromt
def buildPromt(task_id: int, input_payload: str) -> str:
    """
    function: buildPromt
    입력: task_id, input_payload(JSON 문자열)
    출력: user 메시지로 사용할 프롬프트 문자열

    TASK_ID, TASK_DESC, OUTPUT_FORMAT, INPUT을 하나의 user 프롬프트 문자열로 합치는 헬퍼.
    LLM 호출 레이어(services/llm/client.py 등)에서 공통으로 사용한다.
    """
    task_desc = TASK_DESC_MAP.get(task_id, "")
    output_format = OUTPUT_FORMAT_MAP.get(task_id, "")

    user_prompt = f"""
[TASK_ID]
{task_id}

[TASK_DESC]
{task_desc}

[INPUT]
{input_payload}

[OUTPUT_FORMAT]
{output_format}
""".strip()

    logger.debug(
        "Qwen user prompt 생성: task_id=%d input_len=%d",
        task_id,
        len(input_payload or ""),
    )

    return user_prompt

__all__ = [
    "QWEN_SYSTEM_PROMPT",
    "TASK_DESC_MAP",
    "OUTPUT_FORMAT_MAP",
    "buildPromt",
]
