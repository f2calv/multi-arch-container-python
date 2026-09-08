"""Tests for layered application configuration."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

import pytest

from multi_arch_container_python.config import ConfigurationError, LogFormat, load_configuration

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_INTERVAL: Final = 3
OVERRIDDEN_INTERVAL: Final = 10


def test_load_configuration_uses_defaults_when_file_is_missing(tmp_path: Path) -> None:
    """Use typed defaults when no file or environment value exists."""
    settings = load_configuration(tmp_path / "missing.json", {})

    assert settings.app.greeting == "Hello from a multi-architecture container"
    assert settings.app.interval_seconds == DEFAULT_INTERVAL
    assert settings.app.log_format is LogFormat.TEXT
    assert settings.git_repository == "n/a"


def test_load_configuration_environment_overrides_file(tmp_path: Path) -> None:
    """Give environment variables precedence over file values."""
    config_path = tmp_path / "appsettings.json"
    config_path.write_text(
        json.dumps(
            {
                "app": {
                    "greeting": "from file",
                    "interval_seconds": 5,
                    "log_format": "text",
                }
            }
        ),
        encoding="utf-8",
    )

    settings = load_configuration(
        config_path,
        {
            "APP__GREETING": "from environment",
            "APP__INTERVAL_SECONDS": "10",
            "APP__LOG_FORMAT": "json",
            "GIT_REPOSITORY": "multi-arch-container-python",
        },
    )

    assert settings.app.greeting == "from environment"
    assert settings.app.interval_seconds == OVERRIDDEN_INTERVAL
    assert settings.app.log_format is LogFormat.JSON
    assert settings.git_repository == "multi-arch-container-python"


@pytest.mark.parametrize("value", ["0", "3601", "not-an-integer"])
def test_load_configuration_rejects_invalid_interval(tmp_path: Path, value: str) -> None:
    """Reject malformed and out-of-range worker intervals."""
    with pytest.raises(ConfigurationError):
        load_configuration(tmp_path / "missing.json", {"APP__INTERVAL_SECONDS": value})


@pytest.mark.parametrize(
    "environment",
    [
        {"APP__GREETING": " "},
        {"APP__LOG_FORMAT": "xml"},
    ],
)
def test_load_configuration_rejects_invalid_app_values(
    tmp_path: Path,
    environment: dict[str, str],
) -> None:
    """Reject empty greetings and unsupported log formats."""
    with pytest.raises(ConfigurationError):
        load_configuration(tmp_path / "missing.json", environment)


def test_load_configuration_rejects_malformed_json(tmp_path: Path) -> None:
    """Reject malformed JSON instead of silently using defaults."""
    config_path = tmp_path / "appsettings.json"
    config_path.write_text("{", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_configuration(config_path, {})
