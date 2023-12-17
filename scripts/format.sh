#!/bin/sh
# run various linters
set -e
echo "formatting..."
python -m ruff format poetry_lock_listener tests
echo "sorting import with ruff..."
python -m ruff poetry_lock_listener tests --select I,F401 --fix --show-fixes