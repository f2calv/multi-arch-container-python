"""Periodic worker loop."""

from __future__ import annotations

import logging
import platform
import sys
from typing import TYPE_CHECKING, Final

from multi_arch_container_python.telemetry import event_fields

if TYPE_CHECKING:
    from threading import Event

    from multi_arch_container_python.config import Settings

APP_NAME: Final = "multi-arch-container-python"
logger = logging.getLogger(__name__)


def run_worker(stop_event: Event, settings: Settings) -> None:
    """Log runtime and provenance information until shutdown is requested."""
    app = settings.app
    logger.info(
        "worker started",
        extra=event_fields(
            greeting=app.greeting,
            interval_seconds=app.interval_seconds,
            log_format=app.log_format,
        ),
    )

    while not stop_event.is_set():
        logger.info(
            app.greeting,
            extra=event_fields(
                app_name=APP_NAME,
                process_architecture=_process_architecture(),
                os_description=platform.system().lower(),
                python_version=platform.python_version(),
            ),
        )
        logger.info(
            "git provenance",
            extra=event_fields(
                git_repository=settings.git_repository,
                git_branch=settings.git_branch,
                git_commit=settings.git_commit,
                git_tag=settings.git_tag,
            ),
        )
        logger.info(
            "github provenance",
            extra=event_fields(
                github_workflow=settings.github_workflow,
                github_run_id=settings.github_run_id,
                github_run_number=settings.github_run_number,
            ),
        )
        stop_event.wait(app.interval_seconds)

    logger.info("worker stopping")


def _process_architecture() -> str:
    machine = platform.machine().lower()
    return {
        "aarch64": "arm64",
        "armv7l": "armv7",
        "x86_64": "amd64",
    }.get(machine, machine or sys.platform)
