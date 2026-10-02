#!/bin/bash
# Double-click to start the dashboard on macOS.
cd "$(dirname "$0")"
open http://127.0.0.1:8765
exec python3 scripts/serve.py
