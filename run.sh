#!/bin/sh
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python -m fastitch "$@"
fi
if [ -x .venv_win/Scripts/python.exe ]; then
  exec .venv_win/Scripts/python.exe -m fastitch "$@"
fi
if [ -x .venv_win/Scripts/python ]; then
  exec .venv_win/Scripts/python -m fastitch "$@"
fi
if command -v python3 >/dev/null 2>&1; then
  exec python3 -m fastitch "$@"
fi
exec python -m fastitch "$@"
