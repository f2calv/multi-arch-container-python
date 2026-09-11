# Copilot Instructions

## Repository Purpose

This repository demonstrates a Python worker packaged as one multi-architecture
container image for `linux/amd64`, `linux/arm64`, and `linux/arm/v7`. It is one of
four deliberately aligned implementations:

* [multi-arch-container-dotnet](https://github.com/f2calv/multi-arch-container-dotnet)
* [multi-arch-container-go](https://github.com/f2calv/multi-arch-container-go)
* [multi-arch-container-rust](https://github.com/f2calv/multi-arch-container-rust)
* [multi-arch-container-python](https://github.com/f2calv/multi-arch-container-python)

Any change here must be considered for the other implementations. Keep repository
layout, Dockerfile stages and comments, provenance variables, configuration keys,
CI jobs, build scripts, and README headings as close to identical as the languages
allow.

## Development Environment

* Keep every repository-specific dependency inside the VS Code devcontainer.
* Do not install Python, uv, Ruff, mypy, pytest, pre-commit, or package dependencies
  on the host.
* Use Python 3.14 as pinned by `.python-version`.
* Use uv for dependency resolution, locking, synchronization, execution, and builds.
* Keep `.venv` on the named Docker volume configured by `devcontainer.json`; never
  commit or copy it into an image.
* Run `uv sync --locked --all-groups` after dependency changes.
* Never auto-install a Git commit hook. Run pre-commit manually, or opt into the
  lower-frequency pre-push hook.

## Application Contract

* Keep entry-point wiring in `__main__.py`, configuration in `config.py`, logging
  setup in `telemetry.py`, and the loop in `worker.py`.
* Keep runtime dependencies empty unless the standard library cannot provide the
  required behavior cleanly.
* Preserve configuration precedence: defaults, optional `appsettings.json`, then
  environment variables.
* Preserve `APP__GREETING`, `APP__INTERVAL_SECONDS`, and `APP__LOG_FORMAT`.
* Preserve the flat `GIT_*` and `GITHUB_*` provenance environment variables.
* Keep text and newline-delimited JSON logging behavior aligned with the siblings.
* Handle SIGINT and SIGTERM and stop the worker promptly.

## Container Contract

Detailed Dockerfile conventions live in `.github/instructions/docker.instructions.md`.

* Keep one two-stage `Dockerfile` with stages named `build` and `final`.
* Pin the build stage to `$BUILDPLATFORM`; do not emulate target architectures for
  pure Python artifacts.
* Validate `amd64`, `arm64`, and `armv7` explicitly.
* Use a target-native official Python runtime because the distroless Python image
  does not publish arm/v7.
* Run the final image as numeric uid/gid 65532.
* Keep Dockerfile heredocs and all shell files on LF line endings.
* Do not add Helm charts. Kubernetes packaging belongs in the universal chart
  repository.

## Validation

Run validation inside the devcontainer:

```bash
uv lock --check
uv run --no-sync ruff format --check .
uv run --no-sync ruff check .
uv run --no-sync mypy
```

Never run tests automatically. Ask before running `uv run --no-sync pytest`.

Build the production image after Dockerfile or packaging changes:

```bash
docker buildx build --platform linux/amd64 --load -t multi-arch-container-python:validation .
```
