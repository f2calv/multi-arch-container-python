#!/usr/bin/env bash

# Takes ownership of the .venv volume, which is created root-owned, then restores the locked
# development environment into it.

set -euo pipefail

echo "postCreateCommand.sh"
echo "--------------------"

sudo chown -R "$(id -u):$(id -g)" .venv
uv sync --locked --all-groups

# Note: the pre-commit git hook is deliberately NOT installed here. See .pre-commit-config.yaml
# for why, and for the opt-in pre-push alternative.

echo "Done"
