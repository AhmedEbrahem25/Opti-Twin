"""
Structured logger for the Opti-Twin AI engine.

Provides:
  - Coloured console output  (visible in docker logs)
  - Redis publisher handler  (pushes to opti-twin.logs for backend aggregation)

Usage:
    from logger import setup_logging, get as log
    log = setup_logging(redis_client)
    log.info("AI engine started")
"""

from __future__ import annotations

import json
import logging
import os
import time

LOG_LEVEL    = os.getenv("LOG_LEVEL", "INFO").upper()
SERVICE_NAME = "ai-engine"

_COLOURS: dict[str, str] = {
    "DEBUG":    "\033[36m",
    "INFO":     "\033[32m",
    "WARNING":  "\033[33m",
    "ERROR":    "\033[31m",
    "CRITICAL": "\033[1;35m",
}
_RESET = "\033[0m"

_SKIP = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
})


def _ms_ts(record: logging.LogRecord) -> str:
    t = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
    return f"{t}.{int(record.msecs):03d}Z"


class _ColourConsole(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, "")
        ts     = time.strftime("%H:%M:%S", time.gmtime(record.created))
        level  = f"{colour}{record.levelname:8s}{_RESET}"
        loc    = f"\033[2m{record.module}:{record.lineno}{_RESET}"
        msg    = record.getMessage()
        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)
        return f"{ts} {level} \033[36m[{SERVICE_NAME}]{_RESET} {loc}  {msg}"


class _RedisPublisher(logging.Handler):
    """Publishes each log record to `opti-twin.logs` so the backend can aggregate it."""

    def __init__(self, redis_client) -> None:
        super().__init__()
        self._r = redis_client

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry: dict = {
                "ts":      _ms_ts(record),
                "level":   record.levelname,
                "service": SERVICE_NAME,
                "module":  record.module,
                "func":    record.funcName,
                "line":    record.lineno,
                "msg":     record.getMessage(),
            }
            for k, v in vars(record).items():
                if k not in _SKIP and not callable(v):
                    try:
                        json.dumps(v)
                        entry[k] = v
                    except (TypeError, ValueError):
                        pass
            if record.exc_info:
                entry["exc"] = self.formatException(record.exc_info)
            self._r.publish("opti-twin.logs", json.dumps(entry))
        except Exception:
            pass


_logger: logging.Logger | None = None


def setup_logging(redis_client=None) -> logging.Logger:
    global _logger
    numeric = getattr(logging, LOG_LEVEL, logging.INFO)

    _logger = logging.getLogger("ai")
    _logger.setLevel(numeric)
    _logger.handlers.clear()
    _logger.propagate = False

    ch = logging.StreamHandler()
    ch.setLevel(numeric)
    ch.setFormatter(_ColourConsole())
    _logger.addHandler(ch)

    if redis_client is not None:
        rh = _RedisPublisher(redis_client)
        rh.setLevel(numeric)
        _logger.addHandler(rh)

    return _logger


def get() -> logging.Logger:
    """Return the module logger (call after setup_logging)."""
    return _logger if _logger is not None else logging.getLogger("ai")
