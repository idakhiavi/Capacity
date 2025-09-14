Capacity Service

Quickstart
- Local (Windows PowerShell)
  1) Place `sailing_level_raw.csv` at the repo root.
  2) Run: `./scripts/dev_run.ps1 -Recreate`
     - Installs dependencies, loads the CSV into SQLite, and starts the API at `http://127.0.0.1:8000`.
  3) Try a request: `http://127.0.0.1:8000/capacity?date_from=2024-01-15&date_to=2024-02-12`

- Docker (no PowerShell script needed)
  1) Build: `docker build -t capacity-service -f docker/Dockerfile .`
  2) Run with CSV auto-load (CSV present at repo root before build):
     `docker run --rm -p 8000:8000 -e LOAD_CSV_ON_START=1 capacity-service`
     Or mount your repo (no rebuild):
     `$pwdPath = (Resolve-Path .).Path`
     `docker run --rm -p 8000:8000 -e LOAD_CSV_ON_START=1 -e CSV_PATH=/app/sailing_level_raw.csv -v "$pwdPath:/app" capacity-service`
  3) Try a request: `http://127.0.0.1:8000/capacity?date_from=2024-01-15&date_to=2024-02-12`
  Notes:
  - Entry point uses POSIX `sh` (no Bash required). If you saw errors like `set: pipefail` or `$'\r': command not found`, rebuild the image after pulling latest changes.
  - The repo includes a `.gitattributes` to normalize line endings (LF for `.sh`, CRLF for `.ps1`). If you still hit line-ending issues, run a clean checkout.
  Notes:
  - Entry point uses POSIX `sh` (no Bash required). If you ever saw a `set: pipefail` error, rebuild the image to pick up the fix.

Dependencies
- Windows PowerShell (recommended) or any shell
- Python 3.11+
- Docker Desktop (optional, for containerized runs)

Environment (.env)
- Create a `.env` file at the repo root to override defaults. Example:
```
# App and logging
LOG_LEVEL=INFO

# Database (defaults to local SQLite file if unset)
DATABASE_URL=sqlite+pysqlite:///./.data.sqlite

# Corridor alias map (optional)
CORRIDOR_ALIAS_FILE=config/corridor_aliases.json

# Docker entrypoint options (optional)
LOAD_CSV_ON_START=1
CSV_PATH=/app/sailing_level_raw.csv
```
- Locally, the app reads `.env` automatically via pydantic-settings.
- With Docker, you can pass the file using `--env-file .env`.

Health Check
- `GET /health` → `{ "status": "ok" }`
- After starting the app, open: `http://127.0.0.1:8000/health`

Troubleshooting (common)
- Docker Desktop not running / wrong engine:
  - Start Docker Desktop and ensure WSL2 engine is enabled.
- Import errors when running scripts directly:
  - Use module mode: `python -m scripts.load_weekly_capacity`
- MySQL auth error about `cryptography`:
  - `cryptography` is in `requirements.txt`; reinstall deps if missing.
- PowerShell quoting issues with `python -c`:
  - Prefer the provided scripts or use single-quoted outer strings.

API
- Endpoint: `GET /capacity?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
  - Corridor is fixed to China Main -> North Europe Main (aliases resolved internally).
  - Example: `http://127.0.0.1:8000/capacity?date_from=2024-01-15&date_to=2024-02-12`
  - Response fields per item:
    - `week_start_date` (ISO date, Monday of the ISO week)
    - `week_no` (1-53)
    - `offered_capacity_teu` (integer)

Good date examples
- Mondays in range: `date_from=2024-01-15`, `date_to=2024-02-12` (5 weeks)
- Use ISO dates within the sample period: 2024-01-01 to 2024-03-31.

Week numbering
- `week_no` follows ISO-8601 numbering (1-53) based on `week_start_date` (the Monday).
- The sample dataset only covers Jan-Mar 2024; you’ll see week numbers in that subset (roughly 1-13).

Summary
- FastAPI microservice exposing weekly offered capacity (TEU) as a 4-week rolling average (computed in SQL) for corridor China Main -> North Europe Main.
- SQLite by default for zero-setup; compatible with MySQL 8+.

How data import works
- `scripts/load_weekly_capacity.py` reads `sailing_level_raw.csv` and:
  - If present, deduplicates rows by the combined identifiers: `service_version_and_roundtrip_identfiers`, `origin_service_version_and_master`, `destination_service_version_and_master`.
  - For each unique id, uses the latest `ORIGIN_AT_UTC` from the origin region to determine the week.
  - Aggregates offered capacity per (corridor, ISO week start) and upserts into `weekly_capacity(corridor, week_start_date, offered_teu)`.
- Schema is created automatically on app start or by running the loader.

Repository Layout
```
app/
  main.py                 # FastAPI app factory and router wiring
  config.py               # Settings, logging, engine factory, ensure_schema, alias map
  models/schemas.py       # Pydantic response models
  repositories/           # SQL access (rolling average via window function)
  services/               # Business logic (validation, aliasing, date filtering)
  routes/                 # API endpoints (/health, /capacity)
config/
  corridor_aliases.json   # Aliases: "ASIA-EUR" -> canonical corridor name
scripts/
  load_weekly_capacity.py # Import + aggregate CSV into weekly_capacity
  dev_run.ps1             # Windows helper: venv + install + load CSV + run app
docker/
  Dockerfile              # Container build
  entrypoint.sh           # Ensure schema and optional CSV load, then start Uvicorn
tests/
  test_unit/              # Service unit tests
  test_integration/       # API integration tests (SQLite; optional MySQL)
.github/workflows/ci.yml  # CI: smoke + tests (SQLite), optional MySQL
```

Testing
```
py -3 -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

Tech Stack & Tools
- FastAPI, Uvicorn, Pydantic v2, pydantic-settings
- SQLAlchemy 2.x, SQLite (default), MySQL (optional), PyMySQL, cryptography
- pytest, httpx

Configuration
- Default database: `sqlite+pysqlite:///./.data.sqlite`
- Environment variables:
  - `DATABASE_URL` (optional): e.g., `mysql+pymysql://user:pass@host:3306/dbname`
  - `LOG_LEVEL`: e.g., `INFO`, `DEBUG`
  - `CORRIDOR_ALIAS_FILE`: path to a JSON map (default `config/corridor_aliases.json`)
  - `LOAD_CSV_ON_START` (Docker entrypoint): `1` to auto-load CSV
  - `CSV_PATH` (Docker entrypoint): CSV path inside the container (default `sailing_level_raw.csv`)

Design Notes
- SQL-first: 4-week rolling average computed in SQL (`ROWS BETWEEN 3 PRECEDING AND CURRENT ROW`).
- Edge correctness: SQL includes up to 3 weeks before `date_from`; service filters to the requested interval.
- Separation of concerns: Repository (SQL), Service (validation/aliasing), Routes (I/O), Models (Pydantic).
