---
description: "Python 3.14 application, typing, logging, configuration, and validation conventions"
applyTo: "**/*.py"
---

# Python

## Style

* Use Python 3.14 syntax, built-in generic types, `X | None`, and complete type hints.
* Ruff formatting is authoritative. Do not hand-format around it.
* Keep mypy strict mode and Ruff's selected rules clean. Prefer correcting the code
  over suppressing a rule; scope necessary suppressions to the narrowest expression.
* Keep one focused responsibility per module: configuration in `config.py`, logging
  setup in `telemetry.py`, worker behavior in `worker.py`, and wiring in `__main__.py`.
* Keep `__main__.py` wiring-only: load configuration, configure logging, register
  signal handling, invoke the worker, and map terminal failures to exit codes.
* Keep the module API deliberate. Use a leading underscore for helper functions and
  types that are not imported outside their defining module; constants may use
  `SCREAMING_SNAKE_CASE` without an underscore.
* Use `pathlib.Path` for filesystem paths and context managers for owned resources.
* Use frozen slotted dataclasses for immutable configuration records and `StrEnum`
  for closed string values.
* Prefer early returns over deeply nested control flow.

## Error Handling

* Catch only exceptions that can be handled, translated, or enriched locally. Never
  use a bare `except` or silently discard an exception.
* Add operation context while preserving the cause with `raise DomainError(...) from
  error`; do not replace a useful traceback with an unrelated message.
* Use domain-specific exceptions such as `ConfigurationError` at boundaries. Keep
  their messages actionable and free of secrets, personal data, and paths containing
  user or media identifiers; generic relative configuration paths are safe context.
* Reserve process exit-code mapping for `main()`; reusable modules raise exceptions
  rather than calling `sys.exit()`.

## Logging

* Use module loggers and structured `extra` fields. Do not use `print` for diagnostics.
* Keep operational log messages constant and put varying values in structured fields
  so events group consistently. A deliberately configurable user-facing message, such
  as the worker greeting, may remain the message when that is part of the app contract.
* Use `snake_case` field names matching the sibling repositories, including
  `git_repository`, `interval_seconds`, and `process_architecture`.
* Configure root handlers once in `telemetry.py`; application modules only emit
  records through `logging.getLogger(__name__)`.
* Never log credentials, tokens, connection strings, paths containing user or media
  identifiers, or personally identifying values.

## Configuration

* Preserve precedence: typed defaults, optional `appsettings.json`, then environment
  variables. Environment values win.
* Give every application setting a default so the worker runs without a configuration
  file or environment overrides.
* Centralize environment access in `config.py`; never scatter `os.environ` reads
  through application modules.
* Keep file keys and environment suffixes in `snake_case`, using `__` as the section
  separator, for example `APP__INTERVAL_SECONDS`.
* Validate types, ranges, required values, and closed sets during process startup.
  Invalid configuration must fail before the worker starts.

## Shutdown and Concurrency

* Register SIGINT and SIGTERM handlers in `__main__.py`, where Python permits signal
  handling on the main thread.
* Pass a shared `threading.Event` cancellation signal into long-running workers.
  Every thread and loop must have a defined exit path.
* Use `Event.wait(timeout)` for interruptible delays; do not use `time.sleep()` in a
  cancellable worker loop.
* Do not hold locks while performing I/O or waiting for cancellation.

## Testing

* Test names describe behavior, not implementation details.
* Use Arrange, Act, Assert with blank lines between phases and test one behavior at a
  time.
* Use `pytest.mark.parametrize` for multiple meaningful inputs and pytest fixtures such
  as `tmp_path` and `monkeypatch` for isolated setup.
* Avoid shared mutable module state. Every test must be independently repeatable.
* Test public behavior rather than private helpers unless a helper contains genuinely
  complex logic.

## Documentation

* Keep public modules, classes, and functions documented with concise docstrings.
* Document constraints and rationale rather than restating the code.
* Preserve useful external links when refactoring comments or docstrings.

## Performance

* Measure with profiling before optimizing; prefer clear code in this demonstration
  application.
* Avoid unnecessary allocation in hot loops, but do not introduce caches or
  concurrency without a measured reason.
* Avoid unbounded field cardinality and oversized records in hot loops; serialization
  and output perform work even when the surrounding application logic is small.

## Dependencies and Tooling

* Default to the standard library. Add a runtime dependency only when it removes
  meaningful complexity.
* Declare dependencies in `pyproject.toml`, commit `uv.lock`, and use locked syncs so
  environments cannot silently drift.
* Keep development-only tools in the `dev` dependency group and out of the production
  image.
* Run uv, Ruff, mypy, and pytest only inside the repository devcontainer.
* Never run pytest automatically; ask first.
