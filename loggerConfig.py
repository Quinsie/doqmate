# loggerConfig.py

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from contextlib import contextmanager
import contextvars

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
LOG_ROOT = os.path.join(PROJECT_ROOT, "data", "logs", "services")
os.makedirs(LOG_ROOT, exist_ok=True)

current_service: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_service",
    default=None,
)

def setup_root_logging(level: int = logging.INFO) -> None:
    """
    root logger 기본 설정.
    - 콘솔 출력만 담당하는 기본 핸들러를 설정합니다.
    - 서비스별 파일 핸들러는 아래 setup_service_file_handlers()에서 추가합니다.
    """
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        )
    else:
        logging.getLogger().setLevel(level)

class ServiceFilter(logging.Filter):
    """
    current_service 컨텍스트 변수를 보고,
    해당 서비스에서 발생한 로그만 통과시키는 필터.
    """

    def __init__(self, target_service: str) -> None:
        super().__init__()
        self.target_service = target_service

    def filter(self, record: logging.LogRecord) -> bool:
        svc = current_service.get()
        return svc == self.target_service

def _create_service_file_handler(service_name: str) -> TimedRotatingFileHandler:
    """
    특정 service_name(documentService, queryService 등)에 대한
    TimedRotatingFileHandler를 생성합니다.
    """
    today = datetime.now().strftime("%Y_%m_%d")
    log_dir = os.path.join(LOG_ROOT, service_name)
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{today}.log")

    handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        encoding="utf-8",
        backupCount=30,
    )
    handler.suffix = "%Y_%m_%d"

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)

    handler.addFilter(ServiceFilter(service_name))

    return handler

_service_handlers_initialized = False

def setup_service_file_handlers() -> None:
    """
    documentService / queryService용 파일 핸들러를
    root logger에 한 번만 붙입니다.
    """
    global _service_handlers_initialized
    if _service_handlers_initialized:
        return

    root_logger = logging.getLogger()

    for service_name in ["documentService", "queryService"]:
        handler = _create_service_file_handler(service_name)
        root_logger.addHandler(handler)

    _service_handlers_initialized = True

@contextmanager
def service_log_context(service_name: str):
    """
    with 블록 안에서 current_service를 service_name으로 설정했다가,
    블록 종료 시 원래 값으로 복원합니다.

    예:
        with service_log_context("documentService"):
            ...  # 여기서 발생하는 모든 로그는 documentService용 파일에 기록
    """
    token = current_service.set(service_name)
    try:
        yield
    finally:
        current_service.reset(token)