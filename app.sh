#!/usr/bin/env bash
# Domino App entry point. Domino runs this file and serves whatever listens on 0.0.0.0:8888.
# Starts the dashboard (full version at /, simplified at /simple.html) with the data-edit API.
# Only the Python standard library is needed (Python 3.9+).
set -e
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python)
exec "$PY" scripts/serve.py 8888 --host 0.0.0.0
