import logging
import json
import sys
from contextvars import ContextVar
from typing import Any, Dict
from .config import get_setting

_LOGGER: logging.Logger | None = None
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        record.request_id = request_id_var.get()  # type: ignore[attr-defined]
        return True

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        base: Dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if getattr(record, "request_id", None):
            base["request_id"] = record.request_id  # type: ignore[attr-defined]
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)

def get_logger(name: str = "BudgetBitesAPI") -> logging.Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER
    level_name = get_setting("app.log_level", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    fmt_choice = get_setting("app.log_format", "json")
    if fmt_choice == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s")
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())
    logger.addHandler(handler)
    logger.propagate = False

    _LOGGER = logger
    return logger

def set_request_id(rid: str | None) -> None:
    request_id_var.set(rid)
