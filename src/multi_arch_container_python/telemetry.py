"""Process-wide structured logging configuration."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final, cast

from multi_arch_container_python.config import AppConfig, LogFormat

if TYPE_CHECKING:
    from collections.abc import Mapping

_EVENT_FIELDS: Final = "event_fields"
_LOG_LEVELS: Final = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


class JsonFormatter(logging.Formatter):
    """Format records as newline-delimited JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format one log record as JSON."""
        event: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
        }
        event.update(_record_fields(record))
        return json.dumps(event, separators=(",", ":"), ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Format records as compact human-readable key-value text."""

    def format(self, record: logging.LogRecord) -> str:
        """Format one log record as key-value text."""
        fields = " ".join(
            f"{key}={json.dumps(value, ensure_ascii=False)}"
            for key, value in _record_fields(record).items()
        )
        prefix = f"level={record.levelname.lower()} message={json.dumps(record.getMessage())}"
        return f"{prefix} {fields}" if fields else prefix


def configure_logging(config: AppConfig, environ: Mapping[str, str] | None = None) -> None:
    """Install the process-wide text or JSON log handler."""
    environment = os.environ if environ is None else environ
    level = _LOG_LEVELS.get(environment.get("LOG_LEVEL", "info").lower(), logging.INFO)
    formatter: logging.Formatter = (
        JsonFormatter() if config.log_format is LogFormat.JSON else TextFormatter()
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)


def event_fields(**fields: object) -> dict[str, Mapping[str, object]]:
    """Create a logging ``extra`` mapping for structured event fields."""
    return {_EVENT_FIELDS: fields}


def _record_fields(record: logging.LogRecord) -> Mapping[str, object]:
    value = getattr(record, _EVENT_FIELDS, {})
    return cast("dict[str, object]", value) if isinstance(value, dict) else {}
