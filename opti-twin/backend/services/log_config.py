"""
Centralised structured logging for the Opti-Twin backend.

Sets up:
  - Coloured console handler  (human-readable, for docker logs / dev)
  - InMemoryHandler           (ring-buffer, served via /api/v1/logs)

Anything pushed into the root logger is captured by both handlers.
External service logs (AI engine, simulator) that arrive over the
`opti-twin.logs` Redis channel can be injected via push_external().
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import deque
from typing import Optional

LOG_LEVEL    = os.getenv("LOG_LEVEL", "INFO").upper()
SERVICE_NAME = os.getenv("SERVICE_NAME", "backend")
MAX_RECORDS  = int(os.getenv("LOG_BUFFER_SIZE", "500"))

_COLOURS: dict[str, str] = {
    "DEBUG":    "\033[36m",
    "INFO":     "\033[32m",
    "WARNING":  "\033[33m",
    "ERROR":    "\033[31m",
    "CRITICAL": "\033[1;35m",
}
_RESET = "\033[0m"

_SKIP_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
})


def _ms_ts(record: logging.LogRecord) -> str:
    t = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
    return f"{t}.{int(record.msecs):03d}Z"


def _safe_extras(record: logging.LogRecord) -> dict:
    extras: dict = {}
    for k, v in vars(record).items():
        if k in _SKIP_ATTRS or callable(v):
            continue
        try:
            json.dumps(v)
            extras[k] = v
        except (TypeError, ValueError):
            pass
    return extras


class _ColourConsole(logging.Formatter):
    def __init__(self, service: str) -> None:
        super().__init__()
        self._svc = service

    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, "")
        ts     = time.strftime("%H:%M:%S", time.gmtime(record.created))
        level  = f"{colour}{record.levelname:8s}{_RESET}"
        svc    = f"\033[34m[{self._svc}]{_RESET}"
        loc    = f"\033[2m{record.module}.{record.funcName}:{record.lineno}{_RESET}"
        msg    = record.getMessage()
        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)
        return f"{ts} {level} {svc} {loc}  {msg}"


class InMemoryHandler(logging.Handler):
    """Thread-safe deque that stores the last MAX_RECORDS log entries as dicts."""

    def __init__(self, service: str, maxlen: int = MAX_RECORDS) -> None:
        super().__init__()
        self._svc = service
        self._buf: deque[dict] = deque(maxlen=maxlen)

    # ── Ingestion ──────────────────────────────────────────────────────────────

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = {
                "ts":      _ms_ts(record),
                "level":   record.levelname,
                "service": self._svc,
                "logger":  record.name,
                "module":  record.module,
                "func":    record.funcName,
                "line":    record.lineno,
                "msg":     record.getMessage(),
            }
            entry.update(_safe_extras(record))
            if record.exc_info:
                entry["exc"] = self.formatException(record.exc_info)
            self._buf.append(entry)
        except Exception:
            self.handleError(record)

    def push_external(self, entry: dict) -> None:
        """Accept a pre-built dict from another service (via Redis opti-twin.logs)."""
        if isinstance(entry, dict) and "msg" in entry:
            self._buf.append(entry)

    # ── Query ──────────────────────────────────────────────────────────────────

    def query(
        self,
        level: Optional[str] = None,
        service: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 200,
    ) -> list[dict]:
        results: list[dict] = []
        for entry in reversed(list(self._buf)):
            if level and entry.get("level") != level.upper():
                continue
            if service and entry.get("service") != service:
                continue
            if q and q.lower() not in entry.get("msg", "").lower():
                continue
            results.append(entry)
            if len(results) >= limit:
                break
        return results

    def stats(self) -> dict:
        snap = list(self._buf)
        by_level: dict[str, int] = {}
        services: set[str] = set()
        for e in snap:
            lv = e.get("level", "INFO")
            by_level[lv] = by_level.get(lv, 0) + 1
            services.add(e.get("service", "?"))
        return {
            "total":    len(snap),
            "by_level": by_level,
            "services": sorted(services),
        }


# ── Module-level singleton ─────────────────────────────────────────────────────
_mem_handler: Optional[InMemoryHandler] = None


def setup_logging(service: str = SERVICE_NAME, level: str = LOG_LEVEL) -> InMemoryHandler:
    global _mem_handler
    numeric = getattr(logging, level, logging.INFO)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(numeric)

    # Coloured console output
    ch = logging.StreamHandler()
    ch.setLevel(numeric)
    ch.setFormatter(_ColourConsole(service))
    root.addHandler(ch)

    # In-memory ring buffer
    _mem_handler = InMemoryHandler(service=service)
    _mem_handler.setLevel(numeric)
    root.addHandler(_mem_handler)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "uvicorn.error", "fastapi", "redis",
                  "asyncio", "websockets"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    return _mem_handler


def get_memory_handler() -> Optional[InMemoryHandler]:
    return _mem_handler
