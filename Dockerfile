# syntax=docker/dockerfile:1
#
# Multi-architecture container image built from a SINGLE Dockerfile.
#
# This file deliberately mirrors its sibling repositories stage-for-stage and
# comment-for-comment, so that a developer fluent in one language can learn the
# containerisation story of another by diffing the two files:
#
#   https://github.com/f2calv/multi-arch-container-dotnet
#   https://github.com/f2calv/multi-arch-container-go
#   https://github.com/f2calv/multi-arch-container-rust
#   https://github.com/f2calv/multi-arch-container-python   <- you are here
#
# ------------------------------------------------------------------------------
# Stage 1 of 2: build
#
# Pinned to $BUILDPLATFORM (the native architecture of the machine running the
# build). Python source and pure Python wheels are architecture-neutral, so one
# native build can be copied into every target-native runtime image without QEMU.
# ------------------------------------------------------------------------------
FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:0.12.10 AS uv

FROM --platform=$BUILDPLATFORM python:3.14-slim-bookworm AS build
WORKDIR /src

COPY --from=uv /uv /uvx /usr/local/bin/

ARG APP_NAME=multi-arch-container-python

# -- Dependency layer ----------------------------------------------------------
# Copy ONLY the files that influence dependency resolution so that editing a .py
# file reuses the cached install. The WebAssembly target admits universal wheels
# but no Linux native extensions, keeping this layer portable across all targets.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv export --locked --no-dev --no-emit-project --output-file /tmp/requirements.txt && \
    uv pip install \
        --target /out/site-packages \
        --python-platform wasm32-pyodide2024 \
        --only-binary :all: \
        --require-hashes \
        --requirements /tmp/requirements.txt

# -- Compile layer -------------------------------------------------------------
COPY src ./src

# buildx injects TARGETARCH/TARGETVARIANT automatically:
#   linux/amd64  -> TARGETARCH=amd64  TARGETVARIANT=
#   linux/arm64  -> TARGETARCH=arm64  TARGETVARIANT=
#   linux/arm/v7 -> TARGETARCH=arm    TARGETVARIANT=v7
# Concatenating the two gives a single flat token to switch on: amd64|arm64|armv7.
ARG TARGETARCH
ARG TARGETVARIANT
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked <<EOF
set -eux
case "${TARGETARCH}${TARGETVARIANT}" in
    amd64|arm64|armv7) ;;
    *) echo "unsupported platform: linux/${TARGETARCH}/${TARGETVARIANT}" >&2; exit 1 ;;
esac
uv build --wheel --out-dir /out
uv pip install --target /out/site-packages --no-deps /out/multi_arch_container_python-*.whl
if find /out/site-packages -type f \( -name '*.so' -o -name '*.pyd' -o -name '*.dll' \) -print -quit | grep -q .; then
    echo "runtime dependencies must not contain architecture-specific native extensions" >&2
    exit 1
fi
EOF

# ------------------------------------------------------------------------------
# Stage 2 of 2: final
#
# No --platform override here, so buildx resolves the base image for
# $TARGETPLATFORM and the resulting image is genuinely native to the target.
#
# distroless/python supports amd64 and arm64 but not arm/v7. The official slim
# image is the smallest maintained Python runtime that supports all three targets.
# ------------------------------------------------------------------------------
FROM python:3.14-slim-bookworm AS final
WORKDIR /app

COPY --from=build /out/site-packages /usr/local/lib/python3.14/site-packages
# Base configuration; every value can be overridden by an environment variable at runtime.
COPY appsettings.json .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# -- Provenance ----------------------------------------------------------------
# Supplied by the CI workflow (.github/workflows/ci.yml) or by build.sh/build.ps1.
ARG GIT_REPOSITORY=n/a
ENV GIT_REPOSITORY=$GIT_REPOSITORY
ARG GIT_BRANCH=n/a
ENV GIT_BRANCH=$GIT_BRANCH
ARG GIT_COMMIT=n/a
ENV GIT_COMMIT=$GIT_COMMIT
ARG GIT_TAG=n/a
ENV GIT_TAG=$GIT_TAG

ARG GITHUB_WORKFLOW=n/a
ENV GITHUB_WORKFLOW=$GITHUB_WORKFLOW
ARG GITHUB_RUN_ID=0
ENV GITHUB_RUN_ID=$GITHUB_RUN_ID
ARG GITHUB_RUN_NUMBER=0
ENV GITHUB_RUN_NUMBER=$GITHUB_RUN_NUMBER

# https://github.com/opencontainers/image-spec/blob/main/annotations.md
LABEL org.opencontainers.image.title="multi-arch-container-python" \
    org.opencontainers.image.description="Multi-architecture container build (amd64/arm64/armv7) w/Python" \
    org.opencontainers.image.source="https://github.com/f2calv/multi-arch-container-python" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.version="$GIT_TAG" \
    org.opencontainers.image.revision="$GIT_COMMIT"

# A numeric uid/gid works without mutating the target image or requiring a passwd entry.
USER 65532:65532

ENTRYPOINT ["python", "-m", "multi_arch_container_python"]
