#!/bin/sh
set -e
coverage run --branch --include="poetry_lock_listener/*" -m pytest tests "$@"
coverage html
coverage report -m
coverage xml