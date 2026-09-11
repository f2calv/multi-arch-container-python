"""Typed, layered application configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final, cast

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

UNKNOWN: Final = "n/a"
DEFAULT_GREETING: Final = "Hello from a multi-architecture container"
DEFAULT_INTERVAL_SECONDS: Final = 3
MAX_INTERVAL_SECONDS: Final = 3600


class ConfigurationError(ValueError):
    """Raised when application configuration is invalid."""


class LogFormat(StrEnum):
    """Supported console log formats."""

    TEXT = "text"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Settings from the ``app`` configuration section."""

    greeting: str = DEFAULT_GREETING
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS
    log_format: LogFormat = LogFormat.TEXT


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings and flat build provenance values."""

    app: AppConfig
    git_repository: str = UNKNOWN
    git_branch: str = UNKNOWN
    git_commit: str = UNKNOWN
    git_tag: str = UNKNOWN
    github_workflow: str = UNKNOWN
    github_run_id: str = UNKNOWN
    github_run_number: str = UNKNOWN


def load_configuration(
    path: Path,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    """Load defaults, an optional JSON file, then environment overrides.

    The sibling .NET repository layers one extra source, an optional
    ``appsettings.{DOTNET_ENVIRONMENT}.json``, because its host provides that for free. It is
    deliberately not reimplemented here.
    """
    environment = os.environ if environ is None else environ
    file_values = _load_json(path)
    app_values = _mapping_value(file_values.get("app", {}), "app")

    greeting = _string_value(
        environment.get("APP__GREETING", app_values.get("greeting", DEFAULT_GREETING)),
        "app.greeting",
    )
    if not greeting.strip():
        message = "app.greeting must not be empty"
        raise ConfigurationError(message)

    interval_seconds = _integer_value(
        environment.get(
            "APP__INTERVAL_SECONDS",
            app_values.get("interval_seconds", DEFAULT_INTERVAL_SECONDS),
        ),
        "app.interval_seconds",
    )
    if not 1 <= interval_seconds <= MAX_INTERVAL_SECONDS:
        message = f"app.interval_seconds must be between 1 and {MAX_INTERVAL_SECONDS}"
        raise ConfigurationError(message)

    log_format_value = _string_value(
        environment.get("APP__LOG_FORMAT", app_values.get("log_format", LogFormat.TEXT)),
        "app.log_format",
    )
    try:
        log_format = LogFormat(log_format_value.lower())
    except ValueError as error:
        message = "app.log_format must be 'text' or 'json'"
        raise ConfigurationError(message) from error

    return Settings(
        app=AppConfig(
            greeting=greeting,
            interval_seconds=interval_seconds,
            log_format=log_format,
        ),
        git_repository=environment.get("GIT_REPOSITORY", UNKNOWN),
        git_branch=environment.get("GIT_BRANCH", UNKNOWN),
        git_commit=environment.get("GIT_COMMIT", UNKNOWN),
        git_tag=environment.get("GIT_TAG", UNKNOWN),
        github_workflow=environment.get("GITHUB_WORKFLOW", UNKNOWN),
        github_run_id=environment.get("GITHUB_RUN_ID", UNKNOWN),
        github_run_number=environment.get("GITHUB_RUN_NUMBER", UNKNOWN),
    )


def _load_json(path: Path) -> Mapping[str, object]:
    if not path.exists():
        return {}

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        message = f"unable to load {path}: {error}"
        raise ConfigurationError(message) from error

    return _mapping_value(value, str(path))


def _mapping_value(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        message = f"{name} must be a JSON object"
        raise ConfigurationError(message)
    return cast("dict[str, object]", value)


def _string_value(value: object, name: str) -> str:
    if not isinstance(value, str):
        message = f"{name} must be a string"
        raise ConfigurationError(message)
    return value


def _integer_value(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        message = f"{name} must be an integer"
        raise ConfigurationError(message)

    try:
        return int(value)
    except ValueError as error:
        message = f"{name} must be an integer"
        raise ConfigurationError(message) from error
