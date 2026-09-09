"""Process-wide structured logging configuration."""

from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final, cast

from opentelemetry import _logs, metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from multi_arch_container_python.config import UNKNOWN, AppConfig, LogFormat

if TYPE_CHECKING:
    from collections.abc import Mapping

    from multi_arch_container_python.config import Settings

APP_NAME: Final = "multi-arch-container-python"
_EVENT_FIELDS: Final = "_event_fields"
_LOG_LEVELS: Final = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


class TelemetryError(Exception):
    """Raised when OpenTelemetry cannot be initialized."""


@dataclass(slots=True)
class Telemetry:
    """Own the OpenTelemetry providers that must be flushed during shutdown."""

    log_handler: LoggingHandler
    logger_provider: LoggerProvider
    meter_provider: MeterProvider
    tracer_provider: TracerProvider

    def shutdown(self) -> None:
        """Detach the log bridge, flush telemetry, and stop every exporter."""
        logging.getLogger().removeHandler(self.log_handler)
        self.log_handler.close()
        try:
            self.logger_provider.shutdown()
        finally:
            try:
                self.meter_provider.shutdown()
            finally:
                self.tracer_provider.shutdown()


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


def initialize_telemetry(
    settings: Settings,
    environ: Mapping[str, str] | None = None,
) -> Telemetry | None:
    """Add OTLP/HTTP logs, metrics, and traces when an endpoint is configured."""
    environment = os.environ if environ is None else environ
    if not environment.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip():
        return None

    try:
        service_name = environment.get("OTEL_SERVICE_NAME") or APP_NAME
        service_version = settings.git_tag if settings.git_tag != UNKNOWN else "unknown"
        resource = Resource.create(
            {
                SERVICE_NAME: service_name,
                SERVICE_VERSION: service_version,
            }
        )
        logger_provider = LoggerProvider(resource=resource, shutdown_on_exit=False)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))

        meter_provider = MeterProvider(
            metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter())],
            resource=resource,
            shutdown_on_exit=False,
        )
        tracer_provider = TracerProvider(resource=resource, shutdown_on_exit=False)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    except Exception as error:
        message = "failed to initialize OpenTelemetry exporters"
        raise TelemetryError(message) from error

    _logs.set_logger_provider(logger_provider)
    metrics.set_meter_provider(meter_provider)
    trace.set_tracer_provider(tracer_provider)

    log_handler = LoggingHandler(logger_provider=logger_provider)
    log_handler.addFilter(_remove_event_field_marker)
    logging.getLogger().addHandler(log_handler)

    return Telemetry(log_handler, logger_provider, meter_provider, tracer_provider)


def event_fields(**fields: object) -> dict[str, object]:
    """Create a logging ``extra`` mapping for structured event fields."""
    return {**fields, _EVENT_FIELDS: tuple(fields)}


def _record_fields(record: logging.LogRecord) -> Mapping[str, object]:
    names = getattr(record, _EVENT_FIELDS, ())
    if not isinstance(names, tuple):
        return {}
    return {name: getattr(record, name) for name in cast("tuple[str, ...]", names)}


def _remove_event_field_marker(record: logging.LogRecord) -> bool:
    if hasattr(record, _EVENT_FIELDS):
        delattr(record, _EVENT_FIELDS)
    return True
