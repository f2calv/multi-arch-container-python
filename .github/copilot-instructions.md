# Copilot Instructions

## Shared Instructions

Shared Copilot instructions, skills and prompts are maintained centrally in the [.github](https://github.com/f2calv/.github) repository, under `.github/instructions/`, `.github/skills/` and `.github/prompts/`. They are deliberately not copied into this repository, so a change there takes effect everywhere without a pull request here.

To load them, clone that repository and either add it to this VS Code workspace, or link its folders into `~/.copilot/`. Its README explains both.

If those shared files are not visible, stop and tell the user rather than guessing the conventions — this repository depends on them.

Everything below is specific to this repository.

## Sibling Repositories (alignment is a hard requirement)

Four repositories implement the *same* trivial worker application in four languages:

- [multi-arch-container-dotnet](https://github.com/f2calv/multi-arch-container-dotnet)
- [multi-arch-container-go](https://github.com/f2calv/multi-arch-container-go)
- [multi-arch-container-rust](https://github.com/f2calv/multi-arch-container-rust)
- [multi-arch-container-python](https://github.com/f2calv/multi-arch-container-python) (this one)

Their premise is that a developer fluent in one language can learn another language's containerisation story by diffing two repositories. **Any change made here must be considered for the other three.** Keep the following as close to identical as possible:

- Repository layout and file names.
- `Dockerfile` stage names (`build`, `final`), section comment banners and ordering.
- The `ARG`/`ENV` provenance block and OCI `LABEL` block.
- Environment variable names consumed by the application — both the flat `GIT_*`/`GITHUB_*` provenance variables and the `APP__*` configuration overrides.
- Application file responsibilities: configuration model, logging setup, worker loop, entry-point wiring.
- `.github/workflows/ci.yml` job names and structure.
- `.editorconfig` common section, `.pre-commit-config.yaml`, `.devcontainer/`, `.vscode/extensions.json`.
- `build.sh` / `build.ps1` are byte-identical (all values are derived from git).
- `README.md` section headings.

Python convention would normally place the package directly under `src/`. The nested `src/multi_arch_container_python/` layout is used deliberately to mirror the sibling repositories, and is bound to the build backend through `module-name` / `module-root` in `pyproject.toml`. Do not "fix" it.

## No Helm Charts

These repositories are **application code only**. Kubernetes packaging lives in the standalone [f2calv/helm-charts](https://github.com/f2calv/helm-charts) repository, which provides a single multi-purpose chart used by all deployments. Do not reintroduce a `charts/` directory or a `chart` job in `ci.yml`.

## Development Environment

- Keep every repository-specific dependency inside the VS Code devcontainer. Do not install Python, uv, Ruff, mypy or pytest on the host.
- The interpreter version is pinned in `.python-version` and must agree with `requires-python`, `[tool.ruff] target-version` and `[tool.mypy] python_version`. Changing it means changing all four.
- uv owns dependency resolution, locking, synchronisation, execution and builds. Run `uv sync --locked --all-groups` after any dependency change.
- `.venv` lives on the named Docker volume configured by `devcontainer.json`; never commit it or copy it into an image.

Two devcontainer deviations from the siblings are deliberate:

- **`.devcontainer/Dockerfile`** exists because uv is not present in the base Python image and has no official Feature. Copying the binary from the pinned `ghcr.io/astral-sh/uv` image matches how the production `Dockerfile` obtains it, and Dependabot tracks that pin through the `docker` ecosystem.
- **`.devcontainer/postCreateCommand.sh`** exists because `.venv` is a named volume that is created root-owned. It takes ownership and then restores the locked environment. The siblings need neither step.

## Configuration Key Casing

Configuration keys are **snake_case** in both `appsettings.json` and the environment. This is deliberate: it is what the sibling .NET, Go and Rust repositories use, so the same key resolves identically across all four languages. Do not "correct" them to camelCase or PascalCase. The keys themselves are documented in the [README](../README.md#configuration).

## Container Conventions

- The final image is a **target-native official Python runtime**, not distroless. `gcr.io/distroless/python` publishes no `linux/arm/v7` manifest, and that is a supported platform here.
- The `build` stage is pinned to `$BUILDPLATFORM` and does **not** emulate the target, because the artifacts are pure Python and need no cross-compilation.
- The final image runs as numeric uid/gid `65532`.
- Validate `amd64`, `arm64` and `armv7` explicitly. `linux/arm/v7` is the leg that breaks when a base image or a wheel is unavailable.

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

## Open Divergence

`__main__.py` returns three exit codes (success, error, configuration error) where Go and Rust return two and .NET lets the exception propagate. This is a known inconsistency across the four siblings; one contract should be agreed rather than each repository drifting further.
