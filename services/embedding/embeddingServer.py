# services/embedding/embeddingServer.py

"""
embeddingServer.py

functions:
    createApp        | FastAPI 애플리케이션 생성
    embedEndpoint    | /v1/embeddings 엔드포인트 핸들러

helpers:
    _getRootDir      | 프로젝트 루트 디렉토리 경로 계산 헬퍼
    _getModelPath    | 임베딩 모델 디렉토리 경로 계산 헬퍼
    _loadModel       | SentenceTransformer 모델 로딩 헬퍼
    _embedBatch      | 문자열 리스트를 임베딩 벡터 배치로 변환하는 헬퍼

설명:
    - BAAI/bge-m3 임베딩 모델을 로컬 디렉토리(models/bge-m3)에 두고 사용하는 HTTP 임베딩 서버.
    - 요청 형식은 OpenAI 스타일 /v1/embeddings 엔드포인트 규칙을 따른다.
      (body: { "model": "...", "input": ["...", ...] },
       응답: { "data": [ { "embedding": [...] }, ... ] })
    - services_embedding.embed_texts에서 호출하는 서버를 이 스크립트로 대체할 수 있다.
"""
import os
import logging
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer

from services.schemas.embeddingSchemas import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingResponseItem,
)

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "bge-m3")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cuda")
EMBEDDING_LOG_LEVEL = os.getenv("EMBEDDING_LOG_LEVEL", "INFO")

_model: SentenceTransformer | None = None

def _getRootDir() -> str:
    """
    helper: _getRootDir
    입력: 없음
    출력: 프로젝트 루트 디렉토리 절대 경로

    설명:
        - 현재 파일 위치(services/embedding/server.py)를 기준으로 상위 두 단계로 올라가
          ~/doqmate/doqmate 형태의 프로젝트 루트를 계산한다.
    """
    here = os.path.abspath(os.path.dirname(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    return root

def _getModelPath() -> str:
    """
    helper: _getModelPath
    입력: 없음
    출력: 로컬 임베딩 모델 디렉토리 경로

    설명:
        - 프로젝트 루트 기준 models/{EMBEDDING_MODEL_NAME} 경로를 반환한다.
        - 기본값 기준: models/bge-m3
    """
    root = _getRootDir()
    modelPath = os.path.join(root, "models", EMBEDDING_MODEL_NAME)
    return modelPath

# def _loadModel() -> SentenceTransformer:
#     """
#     helper: _loadModel
#     입력: 없음
#     출력: 로딩된 SentenceTransformer 인스턴스

#     설명:
#         - 전역 변수 _model에 캐싱된 인스턴스가 있으면 재사용.
#         - 없으면 models/{EMBEDDING_MODEL_NAME} 경로에서 SentenceTransformer를 로딩한다.
#         - EMBEDDING_DEVICE 환경변수에 따라 cuda/cpu 선택을 시도한다.
#     """
#     global _model

#     if _model is not None:
#         return _model

#     modelPath = _getModelPath()
#     logger.info(
#         "임베딩 모델 로딩 시작: model_name=%s path=%s device=%s",
#         EMBEDDING_MODEL_NAME,
#         modelPath,
#         EMBEDDING_DEVICE,
#     )

#     try:
#         _model = SentenceTransformer(modelPath, device=EMBEDDING_DEVICE)
#     except Exception as e:
#         logger.exception(
#             "임베딩 모델 로딩 실패: model_name=%s path=%s error=%s",
#             EMBEDDING_MODEL_NAME,
#             modelPath,
#             e,
#         )
#         raise

def _loadModel() -> SentenceTransformer:
    """
    helper: _loadModel
    입력: 없음
    출력: 로딩된 SentenceTransformer 인스턴스

    설명:
        - 전역 변수 _model에 캐싱된 인스턴스가 있으면 재사용.
        - 없으면 models/{EMBEDDING_MODEL_NAME} 경로에서 SentenceTransformer를 로딩한다.
        - EMBEDDING_DEVICE 환경변수에 따라 cuda/cpu 선택을 시도한다.
        - 현재는 VRAM 충돌을 피하기 위해 강제로 CPU만 사용.
        - 급한대로 CPU모드로 돌려놨는데 나중에 GPU모드로 수정할 필요 있어보입니다.
    """
    global _model

    if _model is not None:
        return _model

    modelPath = _getModelPath()
    device = "cpu"

    logger.info(
        "임베딩 모델 로딩 시작(강제 CPU 모드): model_name=%s path=%s device=%s",
        EMBEDDING_MODEL_NAME,
        modelPath,
        device,
    )

    try:
        _model = SentenceTransformer(modelPath, device=device)
    except Exception as e:
        logger.exception(
            "임베딩 모델 로딩 실패: model_name=%s path=%s error=%s",
            EMBEDDING_MODEL_NAME,
            modelPath,
            e,
        )
        raise

    return _model

def _embedBatch(texts: list[str]) -> list[list[float]]:
    """
    helper: _embedBatch
    입력:
        texts : 임베딩 대상 문자열 리스트
    출력:
        embeddings : 각 문자열에 대한 임베딩 벡터 리스트 (list[list[float]])

    설명:
        - 내부에서 SentenceTransformer.encode를 호출해 배치 임베딩을 수행하고,
          결과를 Python 리스트(list[list[float]]) 형태로 반환한다.
        - texts가 비어 있는 경우 빈 리스트를 그대로 반환한다.
    """
    if not texts:
        return []

    model = _loadModel()
    vectors = model.encode(texts, convert_to_numpy=True)
    embeddings: list[list[float]] = [vec.tolist() for vec in vectors]
    return embeddings

def createApp() -> FastAPI:
    """
    function: createApp
    입력: 없음
    출력:
        app : FastAPI 애플리케이션 인스턴스

    설명:
        - /v1/embeddings 엔드포인트를 제공하는 FastAPI 앱을 생성한다.
        - 실제 서버 실행은 uvicorn에서 담당하며, 이 함수는 ASGI 앱 객체만 반환한다.
    """
    app = FastAPI(
        title="Local Embedding Server",
        description="BAAI/bge-m3 기반 로컬 임베딩 서버 (OpenAI 스타일 /v1/embeddings)",
        version="1.0.0",
    )

    @app.post("/v1/embeddings", response_model=EmbeddingResponse)
    async def embedEndpoint(req: EmbeddingRequest) -> EmbeddingResponse:
        """
        function: embedEndpoint
        입력:
            req : EmbeddingRequest (model, input 리스트)
        출력:
            EmbeddingResponse : data 필드에 embedding 벡터 리스트를 담은 응답

        동작 개요:
            1) req.model이 현재 서버가 사용하는 EMBEDDING_MODEL_NAME과 다른 경우 경고 로그 출력 후 무시
            2) req.input 리스트를 _embedBatch로 임베딩
            3) OpenAI 스타일 {"data": [{"embedding": [...]}, ...]} 형태로 응답 구성
        """
        if not req.input:
            logger.warning("빈 input 리스트로 임베딩 요청 수신")
            return EmbeddingResponse(data=[])

        if req.model and req.model != EMBEDDING_MODEL_NAME:
            logger.warning(
                "요청 모델명이 서버 설정과 다릅니다: requested=%s server=%s",
                req.model,
                EMBEDDING_MODEL_NAME,
            )

        logger.info("임베딩 요청 수신: count=%d model=%s", len(req.input), req.model)

        try:
            embeddings = _embedBatch(req.input)
        except Exception as e:
            logger.exception("임베딩 계산 중 오류 발생: error=%s", e)
            raise

        items = [EmbeddingResponseItem(embedding=vec) for vec in embeddings]
        return EmbeddingResponse(data=items)

    return app

app = createApp()

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=getattr(logging, EMBEDDING_LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    uvicorn.run(
        "services.embedding.embeddingServer:app",
        host="0.0.0.0",
        port=11401,
        reload=False,
    )