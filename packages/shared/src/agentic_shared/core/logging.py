import logging
import sys

APP_LOGGER_NAMES = (
    "agentic_shared",
    "agentic_api",
    "agentic_chat",
    "agentic_admin",
    "agentic_indexing",
)

_NOISY_LOGGERS = ("httpx", "httpcore", "sqlalchemy.engine", "llama_index", "openai")


def _parse_log_level(level: str) -> int:
    names = logging.getLevelNamesMapping()
    return names.get(level.upper(), logging.INFO)


def _host_handlers() -> list[logging.Handler]:
    """Reuse the process host logger: uvicorn for HTTP, celery for workers."""
    uvicorn_handlers = logging.getLogger("uvicorn").handlers
    if uvicorn_handlers:
        return list(uvicorn_handlers)
    celery_handlers = logging.getLogger("celery").handlers
    if celery_handlers:
        return list(celery_handlers)
    root_handlers = logging.getLogger().handlers
    if root_handlers:
        return list(root_handlers)
    return []


def setup_logging(level: str = "INFO") -> None:
    """Route app logs through the host process logger.

    Uvicorn and Celery configure logging before the app lifespan / worker is
    ready. We reuse their handlers on the package root loggers instead of
    calling dictConfig, so app logs share the host format and stream.

    Preference: uvicorn handlers, then celery, then root (Celery's default
    hijack of the root logger), then a plain stdout handler for tests/scripts.
    """
    log_level = _parse_log_level(level)
    handlers = _host_handlers()
    if not handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
        handlers = [handler]

    for name in APP_LOGGER_NAMES:
        app_logger = logging.getLogger(name)
        app_logger.setLevel(log_level)
        app_logger.propagate = False
        app_logger.handlers = list(handlers)

    for logger_name in _NOISY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
