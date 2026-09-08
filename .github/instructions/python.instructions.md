---
description: "Python 3.14 application, typing, logging, configuration, and validation conventions"
applyTo: "**/*.py"
---

# Python

* Use Python 3.14 syntax, built-in generic types, `X | None`, and complete type hints.
* Keep mypy strict mode clean and Ruff's selected rules clean without broad file-level
  suppressions.
* Use frozen slotted dataclasses for immutable configuration records and `StrEnum`
  for closed string values.
* Validate configuration at startup and raise `ConfigurationError` with actionable,
  non-sensitive messages.
* Use module loggers and structured `extra` fields. Do not use `print` for diagnostics.
* Keep dynamic values out of log message templates so events group consistently.
* Keep public modules, classes, and functions documented with concise docstrings.
* Default to the standard library. Add a runtime dependency only when it removes
  meaningful complexity.
* Run uv, Ruff, mypy, and pytest only inside the repository devcontainer.
* Never run pytest automatically; ask first.
