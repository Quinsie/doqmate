# services/embedding/embedding.py

"""
embedding.py

functions:
    embedTexts   | 여러 문장을 임베딩 벡터로 변환
    embedText    | 단일 문장을 임베딩 벡터로 변환

helpers:
    _buildHeaders            | HTTP 요청 헤더 구성 헬퍼
    _parseEmbeddingsResponse | 임베딩 서버 응답 파싱 헬퍼

설명:
    - 로컬에서 구동 중인 임베딩 서버(services/embedding/embeddingServer.py)를 HTTP로 호출해
      텍스트를 벡터로 변환하는 클라이언트 레이어.
    - 기본 설정:
        EMBEDDING_BASE_URL   : http://localhost:11401
        EMBEDDING_MODEL_NAME : bge-m3
        EMBEDDING_TIMEOUT    : 30초
    - 요청 형식은 OpenAI 스타일 /v1/embeddings 엔드포인트 규칙을 따른다.
"""
import os
import logging
import requests
from typing import Any

logger = logging.getLogger(__name__)

EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "http://localhost:11401")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "bge-m3")
EMBEDDING_TIMEOUT = float(os.getenv("EMBEDDING_TIMEOUT", "30"))
EMBEDDING_URL = EMBEDDING_BASE_URL.rstrip("/") + "/v1/embeddings"


class EmbeddingError(RuntimeError):
    """
    임베딩 호출 실패 시 사용하는 예외 타입.
    """
    pass

def _buildHeaders() -> dict[str, str]:
    """
    helper: _buildHeaders
    입력: 없음
    출력: HTTP 요청 헤더 딕셔너리

    설명:
        - Content-Type: application/json
        - EMBEDDING_API_KEY가 설정되어 있으면 Authorization 헤더 추가.
    """
    headers: dict[str, str] = {
        "Content-Type": "application/json",
    }
    if EMBEDDING_API_KEY:
        headers["Authorization"] = f"Bearer {EMBEDDING_API_KEY}"
    return headers

def _parseEmbeddingsResponse(
    respJson: dict[str, Any],
    expectedLen: int,
) -> list[list[float]]:
    """
    helper: _parseEmbeddingsResponse
    입력:
        respJson    : 임베딩 서버에서 반환된 JSON 딕셔너리
        expectedLen : 요청한 입력 텍스트 개수
    출력:
        embeddings  : 각 입력 텍스트에 대응하는 임베딩 벡터 리스트

    설명:
        - OpenAI 스타일 응답: {"data": [{"embedding": [...]}, ...]}
        - 또는 단순화된 응답: {"embeddings": [[...], [...], ...]}
        - 두 형식을 모두 지원하며, 개수 불일치 시 EmbeddingError를 발생시킨다.
    """
    if "data" in respJson:
        data = respJson.get("data") or []
        embeddings: list[list[float]] = []

        for item in data:
            emb = item.get("embedding")
            if not isinstance(emb, list):
                raise EmbeddingError("응답 data[*].embedding 형식이 올바르지 않습니다.")
            embeddings.append(emb)

        if len(embeddings) != expectedLen:
            raise EmbeddingError(
                f"임베딩 개수가 일치하지 않습니다. expected={expectedLen}, got={len(embeddings)}"
            )
        return embeddings

    if "embeddings" in respJson:
        embeddings = respJson.get("embeddings") or []
        if not isinstance(embeddings, list):
            raise EmbeddingError("응답 embeddings 필드 형식이 올바르지 않습니다.")
        if len(embeddings) != expectedLen:
            raise EmbeddingError(
                f"임베딩 개수가 일치하지 않습니다. expected={expectedLen}, got={len(embeddings)}"
            )
        # embeddings가 이미 [[...], [...]] 형식이라고 가정
        return embeddings

    raise EmbeddingError("응답에 data 또는 embeddings 필드가 없습니다.")

def embedTexts(texts: list[str]) -> list[list[float]]:
    """
    function: embedTexts
    입력:
        texts : 임베딩 대상 문자열 리스트
    출력:
        List[List[float]] : 각 입력에 대한 임베딩 벡터

    설명:
        - 입력 리스트를 그대로 임베딩 서버에 전달해 배치 임베딩을 수행한다.
        - HTTP 오류, 상태코드 비정상, JSON 파싱 실패, 형식 오류 등은 EmbeddingError로 래핑된다.
    """
    if not texts:
        return []

    # 모두 str로 캐스팅 (예방 차원)
    payloadTexts = [str(t) for t in texts]

    body = {
        "model": EMBEDDING_MODEL_NAME,
        "input": payloadTexts,
    }

    try:
        resp = requests.post(
            EMBEDDING_URL,
            json=body,
            headers=_buildHeaders(),
            timeout=EMBEDDING_TIMEOUT,
        )
    except requests.RequestException as e:
        logger.exception("[Embedding] HTTP 요청 실패: %s", e)
        raise EmbeddingError(f"임베딩 서버 요청 실패: {e}") from e

    if resp.status_code != 200:
        # 오류 응답 내용 같이 로그 남기기
        try:
            txt = resp.text[:500]
        except Exception:
            txt = "<body decode error>"
        logger.error(
            "[Embedding] 비정상 응답 코드: %s, body=%r",
            resp.status_code,
            txt,
        )
        raise EmbeddingError(f"임베딩 서버 응답 코드가 200이 아닙니다: {resp.status_code}")

    try:
        respJson = resp.json()
    except ValueError as e:
        logger.exception("[Embedding] 응답 JSON 파싱 실패: %s", e)
        raise EmbeddingError("임베딩 서버 응답이 JSON 형식이 아닙니다.") from e

    embeddings = _parseEmbeddingsResponse(respJson, expectedLen=len(texts))
    return embeddings

def embedText(text: str) -> list[float]:
    """
    function: embedText
    입력:
        text : 단일 임베딩 대상 문자열
    출력:
        List[float] : 단일 텍스트에 대한 임베딩 벡터

    단일 문자열을 embedTexts에 위임해 임베딩한다. 빈 문자열은 EmbeddingError를 발생시킨다.
    """
    if not text:
        raise EmbeddingError("빈 문자열은 임베딩할 수 없습니다.")
    vecs = embedTexts([text])
    return vecs[0]

__all__ = [
    "EmbeddingError",
    "embedTexts",
    "embedText",
]