"""Tests for logging and OpenTelemetry setup."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from multi_arch_container_python.config import AppConfig, LogFormat, Settings
from multi_arch_container_python.telemetry import (
    configure_logging,
    event_fields,
    initialize_telemetry,
)

if TYPE_CHECKING:
    import pytest


def test_initialize_telemetry_is_disabled_without_endpoint() -> None:
    """Leave the OpenTelemetry providers unconfigured by default."""
    settings = Settings(app=AppConfig())

    telemetry = initialize_telemetry(settings, {})

    assert telemetry is None


def test_json_logging_renders_structured_fields_flat(capsys: pytest.CaptureFixture[str]) -> None:
    """Keep structured fields flat in console output for the OTLP log bridge."""
    configure_logging(AppConfig(log_format=LogFormat.JSON), {})

    logging.getLogger(__name__).info("worker event", extra=event_fields(iteration=1))

    output = capsys.readouterr().out
    event = json.loads(output)
    assert event["message"] == "worker event"
    assert event["iteration"] == 1
    assert "_event_fields" not in event
