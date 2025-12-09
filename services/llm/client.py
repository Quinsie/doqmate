# services/llm/client.py

"""
client.py

functions:
    callQwen    | Qwen LLM 공통 호출 함수
    parseJson   | LLM 응답 텍스트에서 JSON 부분만 파싱하는 헬퍼

Qwen LLM 서버에 대한 공통 호출 레이어를 제공하는 스크립트.
모든 LLM 관련 TASK는 이 모듈의 callQwen을 통해 호출된다.
"""
from __future__ import annotations

import os
import json
import time
import logging
import re
import requests

from services.llm.prompt import (
    QWEN_SYSTEM_PROMPT,
    buildPromt,
)

logger = logging.getLogger(__name__)

# 환경 변수 기반 설정

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11400")
LLM_API_PATH = os.getenv("LLM_API_PATH", "/v1/chat/completions")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen2.5-7b-instruct")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60"))
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_URL = LLM_BASE_URL.rstrip("/") + LLM_API_PATH


def _buildHeaders() -> dict[str, str]:
    """
    helper: _buildHeaders
    입력: 없음, 출력: HTTP 헤더 딕셔너리

    LLM 서버 호출에 사용할 HTTP 헤더를 생성하는 헬퍼.
    - Content-Type은 항상 application/json
    - LLM_API_KEY가 설정된 경우 Authorization 헤더를 추가한다.
    """
    headers: dict[str, str] = {
        "Content-Type": "application/json",
    }
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    return headers


def callQwen(
    *,
    task_id: int,
    input_payload: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> str:
    """
    function: callQwen
    입력:
        - task_id: int, 수행할 태스크 ID (system.TASK_DESC_MAP 기준)
        - input_payload: str, INPUT 섹션에 들어갈 JSON 문자열
        - temperature: float, 샘플링 온도 (기본 0.2)
        - max_tokens: int, 최대 생성 토큰 수 (기본 4096)
    출력:
        - str: LLM이 생성한 message.content 문자열 (JSON 텍스트 포함)

    Qwen LLM 서버에 대한 공통 호출 함수.
    - user 프롬프트는 buildPromt(task_id, input_payload) 결과를 사용한다.
    - 시스템 프롬프트는 QWEN_SYSTEM_PROMPT를 사용한다.
    - 응답 포맷은 OpenAI 호환 /v1/chat/completions 형식을 가정한다.
    - 실패 시 RuntimeError를 발생시키며, 상세 내용은 로깅한다.
    """
    user_content = buildPromt(
        task_id=task_id,
        input_payload=input_payload,
    )

    body = {
        "model": LLM_MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": QWEN_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
    }

    start_ts = time.time()
    try:
        resp = requests.post(
            LLM_URL,
            headers=_buildHeaders(),
            json=body,
            timeout=LLM_TIMEOUT,
        )
    except requests.RequestException as e:
        logger.exception("[LLM] Qwen HTTP 호출 실패: %s", e)
        raise RuntimeError(f"Qwen 호출 실패: {e}") from e

    if resp.status_code != 200:
        try:
            body_preview = resp.text[:500]
        except Exception:
            body_preview = "<body decode error>"

        logger.error(
            "[LLM] Qwen 비정상 응답코드: %s, body=%r",
            resp.status_code,
            body_preview,
        )
        raise RuntimeError(f"Qwen 응답 코드가 200이 아닙니다: {resp.status_code}")

    try:
        resp_json = resp.json()
    except ValueError as e:
        logger.exception("[LLM] Qwen 응답 JSON 파싱 실패: %s", e)
        raise RuntimeError("Qwen 응답이 JSON 형식이 아닙니다.") from e

    try:
        content = resp_json["choices"][0]["message"]["content"]
    except Exception as e:
        logger.exception(
            "[LLM] Qwen 응답 포맷 예기치 못함: %s, resp=%r",
            e,
            resp_json,
        )
        raise RuntimeError("Qwen 응답 포맷이 예상과 다릅니다.") from e

    elapsed = (time.time() - start_ts) * 1000.0
    logger.info(
        "[LLM] Qwen 호출 성공 | task_id=%s | elapsed_ms=%.1f | req_len=%d | resp_len=%d",
        task_id,
        elapsed,
        len(user_content),
        len(content or ""),
    )

    return content or ""


def parseJson(raw: str) -> dict[str, object]:
    """
    function: parseJson
    입력:
        - raw: str, LLM이 반환한 전체 텍스트(message.content)
    출력:
        - dict[str, object]: 텍스트 안에서 추출한 JSON 객체 딕셔너리

    LLM이 반환한 텍스트에서 JSON 부분만 추출/파싱하는 헬퍼.

    처리 전략 (순서대로 시도):
    1) 전체가 곧바로 JSON 객체처럼 보이면 그대로 json.loads 시도
    2) ```json ... ``` 또는 ``` ... ``` 코드블록 내부에서 { ... } 구간만 추출해 파싱
    3) 텍스트 전체에서 첫 번째 '{' ~ 마지막 '}' 구간을 잘라 파싱 (기존 방식)
    4) 모든 시도가 실패하면 ValueError 발생

    이렇게 해두면:
    - 앞뒤에 설명 문장/불릿이 있어도
    - ```json 으로 감싼 코드블록이어도
    - 마지막에 요약 문장이 조금 붙어도
    웬만하면 JSON을 찾아서 파싱할 수 있도록 설계함.
    """
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("빈 응답입니다. JSON을 파싱할 수 없습니다.")

    # 1) 전체 문자열이 곧바로 JSON 객체처럼 보이는 경우
    if raw.startswith("{") and raw.endswith("}"):
        try:
            return json.loads(raw)
        except Exception as e:
            logger.warning(
                "[LLM] parseJson 전체 문자열 파싱 실패, 다음 단계 시도 예정 | error=%s | preview=%r",
                e,
                raw[:200],
            )

    # 2) ```json ... ``` 또는 ``` ... ``` 코드블록 내부에서 JSON 찾기
    #    - 가장 먼저 등장하는 코드블록 기준
    try:
        code_block_pattern = re.compile(
            r"```(?:json)?\s*(\{.*?\})\s*```",
            re.DOTALL | re.IGNORECASE,
        )
        m = code_block_pattern.search(raw)
        if m:
            json_str = m.group(1).strip()
            try:
                return json.loads(json_str)
            except Exception as e:
                logger.warning(
                    "[LLM] parseJson 코드블록 JSON 파싱 실패, 다음 단계 시도 예정 | error=%s | preview=%r",
                    e,
                    json_str[:200],
                )
    except Exception as e:
        # 정규식 단계에서의 예외는 치명적이지 않으니 다음 전략으로 진행
        logger.warning("[LLM] parseJson 코드블록 탐색 중 예외 발생: %s", e)

    # 3) 텍스트 전체에서 첫 '{' ~ 마지막 '}' 구간을 잘라 파싱 (fallback)
    first = raw.find("{")
    last = raw.rfind("}")
    if first == -1 or last == -1 or last <= first:
        logger.error(
            "[LLM] parseJson JSON 구간을 찾을 수 없음 | preview=%r",
            raw[:300],
        )
        raise ValueError("JSON 구간을 찾을 수 없습니다.")

    json_str = raw[first : last + 1].strip()

    # 혹시 뒤에 붙은 백틱이나 이상한 토큰이 섞인 경우를 한 번 더 정리
    # 예: '{"a":1}\n```' 같은 케이스
    trailing_backtick = json_str.rfind("```")
    if trailing_backtick != -1:
        json_str = json_str[:trailing_backtick].strip()

    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(
            "[LLM] parseJson 최종 JSON 파싱 실패 | error=%s | json_preview=%r | raw_preview=%r",
            e,
            json_str[:300],
            raw[:300],
        )
        raise ValueError("JSON 파싱에 실패했습니다.") from e


__all__ = [
    "callQwen",
    "parseJson",
]
