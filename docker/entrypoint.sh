#!/bin/sh
set -eu

# Ensure schema (especially for SQLite)
python - <<'PY'
from app.config import ensure_schema
ensure_schema()
PY

# Optionally load CSV on start
if [ "${LOAD_CSV_ON_START:-0}" = "1" ]; then
  CSV_PATH="${CSV_PATH:-sailing_level_raw.csv}"
  if [ -f "$CSV_PATH" ]; then
    echo "Loading CSV: $CSV_PATH"
    python -m scripts.load_weekly_capacity --csv "$CSV_PATH"
  else
    echo "CSV not found at $CSV_PATH; skipping load" >&2
  fi
fi

exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
