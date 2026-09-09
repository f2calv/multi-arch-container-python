"""Application entry point."""

from __future__ import annotations

import logging
import signal
import sys
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Final

from multi_arch_container_python.config import ConfigurationError, load_configuration
from multi_arch_container_python.telemetry import (
    TelemetryError,
    configure_logging,
    initialize_telemetry,
)
from multi_arch_container_python.worker import run_worker

if TYPE_CHECKING:
    from types import FrameType

CONFIG_FILE: Final = Path("appsettings.json")
EXIT_SUCCESS: Final = 0
EXIT_ERROR: Final = 1
EXIT_CONFIGURATION_ERROR: Final = 2


def main() -> int:
    """Load configuration and run the worker until SIGINT or SIGTERM."""
    try:
        settings = load_configuration(CONFIG_FILE)
    except ConfigurationError as error:
        sys.stderr.write(f"configuration error: {error}\n")
        return EXIT_CONFIGURATION_ERROR

    configure_logging(settings.app)
    telemetry_error: TelemetryError | None = None
    try:
        telemetry = initialize_telemetry(settings)
    except TelemetryError as error:
        telemetry = None
        telemetry_error = error
    if telemetry_error is not None:
        logging.getLogger(__name__).error("telemetry initialization failed: %s", telemetry_error)
        return EXIT_ERROR

    stop_event = Event()

    def request_shutdown(_signum: int, _frame: FrameType | None) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    logging.getLogger(__name__).info("Hit Ctrl-C to exit....")
    try:
        run_worker(stop_event, settings)
    finally:
        if telemetry is not None:
            telemetry.shutdown()
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
