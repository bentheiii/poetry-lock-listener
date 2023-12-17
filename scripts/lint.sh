#!/bin/sh
# run various linters
set -e
echo "running ruff..."
python -m ruff format poetry_lock_listener tests --check
python -m ruff poetry_lock_listener tests
echo "running mypy..."
python3 -m mypy --show-error-codes poetry_lock_listener
