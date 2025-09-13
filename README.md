Capacity Service

Quickstart
- Local (Windows PowerShell)
  1) Place `sailing_level_raw.csv` at the repo root.
  2) Run: `./scripts/dev_run.ps1 -Recreate`
     - Installs dependencies, loads the CSV into SQLite, and starts the API at `http://127.0.0.1:8000`.
  3) Try a request:
     - `http://127.0.0.1:8000/capacity?date_from=2024-01-15&date_to=2024-02-12`

- Docker (no PowerShell script needed)
  1) Build: `docker build -t capacity-service -f docker/Dockerfile .`
  2) Run with CSV auto-load (CSV present in repo root before build):
     - `docker run --rm -p 8000:8000 -e LOAD_CSV_ON_START=1 capacity-service`
     Or mount your repo (no rebuild):
     - `$pwdPath = (Resolve-Path .).Path`
     - `docker run --rm -p 8000:8000 -e LOAD_CSV_ON_START=1 -e CSV_PATH=/app/sailing_level_raw.csv -v "$pwdPath:/app" capacity-service`
  3) Try a request:
     - `http://127.0.0.1:8000/capacity?date_from=2024-01-15&date_to=2024-02-12`

Good date examples
- Mondays in range: `date_from=2024-01-15`, `date_to=2024-02-12` (5 weeks)
- Non-Mondays also work; prefer Mondays to align exactly with weekly rows.

Summary
- FastAPI microservice exposing weekly offered capacity (TEU) as a 4-week rolling average for corridor China Main -> North Europe Main.
- Rolling average computed in SQL; API returns one entry per week in the requested range.
- SQLite by default for zero-setup; compatible with MySQL 8+.

Features
- Endpoint: `GET /capacity?date_from&date_to` (YYYY-MM-DD) -> list of weeks with `week_start_date`, `week_no`, `offered_capacity_teu`.
- Health endpoint: `GET /health`.
- CSV loader to import the provided sailing-level dataset into a normalized weekly table.
- Docker image and CI workflow for easy clone, run, and verify.

Tech Stack & Dependencies
- Python 3.11, FastAPI, Uvicorn
- Pydantic v2, pydantic-settings
- SQLAlchemy 2.x
- SQLite by default; optional MySQL via `pymysql` (+ `cryptography`)
- Tests: `pytest`, `httpx`

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
  load_weekly_capacity.py # Import + aggregate CSV into weekly_capacity (id dedupe + latest origin departure)
  dev_run.ps1             # Windows helper: venv + install + load CSV + run app
docker/
  Dockerfile              # Container build
  entrypoint.sh           # Ensure schema and optional CSV load, then start Uvicorn
tests/
  test_unit/              # Service unit tests
  test_integration/       # API integration tests (SQLite; optional MySQL)
.github/workflows/ci.yml  # CI: smoke + tests (SQLite), optional MySQL
```

Getting Started

Prerequisites
- Windows PowerShell (recommended) or any shell
- Python 3.11+
- Docker Desktop (optional, for containerized runs)

Clone
```
git clone <your-public-repo-url>
cd Capacity
```

API
- Health
  - `GET /health` -> `{ "status": "ok" }`
- Capacity
  - `GET /capacity?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
  - Corridor is fixed to China Main -> North Europe Main (aliases resolved internally).
  - Example:
    - `http://127.0.0.1:8000/capacity?date_from=2024-01-15&date_to=2024-02-12`
  - Response fields mirror the task example per item:
    - `week_start_date` (ISO date, Monday of the ISO week)
    - `week_no` (1-53)
    - `offered_capacity_teu` (integer)

Healthy input hints
- Use ISO dates within the dataset’s expected period: 2024-01-01 to 2024-03-31.
- The API validates that `date_from <= date_to` and may reject very large ranges (> 3 years).
- Weeks are computed by ISO-week convention (Monday as start of week).

Week numbering
- `week_no` follows ISO-8601 numbering (1-53) based on `week_start_date` (the Monday of each week).
- The sample dataset only covers Jan-Mar 2024, so you will only see the subset of week numbers present in that period (roughly 1-13).
- Validation allows the full ISO range for generality; results still depend on the data loaded into the database.

How data import works
- `scripts/load_weekly_capacity.py` reads `sailing_level_raw.csv` and:
  - If present, deduplicates rows by the combined identifiers:
    `service_version_and_roundtrip_identfiers`, `origin_service_version_and_master`, `destination_service_version_and_master`.
  - For each unique id, uses the latest `ORIGIN_AT_UTC` from the origin region to determine the week.
  - Aggregates offered capacity per (corridor, ISO week start).
  - Upserts into table `weekly_capacity(corridor, week_start_date, offered_teu)`.
- The database schema is created automatically on app start (dev convenience) or by running the loader.

Testing
```
py -3 -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```
- Unit tests validate service logic and edge cases.
- Integration tests exercise the API with a seeded SQLite database.
- An optional MySQL test runs when `DATABASE_URL` is set in the environment (CI provides a MySQL service).

Configuration
- Default database: `sqlite+pysqlite:///./.data.sqlite`
- Environment variables:
  - `DATABASE_URL` (optional): e.g., `mysql+pymysql://user:pass@host:3306/dbname`
  - `LOG_LEVEL`: e.g., `INFO`, `DEBUG`
  - `CORRIDOR_ALIAS_FILE`: path to a JSON map (default `config/corridor_aliases.json`)
  - `LOAD_CSV_ON_START` (Docker entrypoint): `1` to auto-load CSV
  - `CSV_PATH` (Docker entrypoint): CSV path inside the container (default `sailing_level_raw.csv`)

Design Notes
- SQL first: 4-week rolling average computed in SQL using a window function (`ROWS BETWEEN 3 PRECEDING AND CURRENT ROW`).
- Correctness at the edges: to compute the first in-range week correctly, the query includes a 3-week buffer before `date_from`; the service then filters to the exact requested range.
- Simplicity of setup: SQLite by default, but SQL remains compatible with MySQL 8+ (proved by optional CI job).
- Separation of concerns: Repository (SQL), Service (validation/aliasing), Routes (I/O), Models (Pydantic).

Troubleshooting
- Docker Desktop errors on Windows: ensure Docker Desktop is running and using the WSL2 engine.
- Import errors when running scripts: use module mode (`python -m scripts.load_weekly_capacity`).
- MySQL auth error: ensure `cryptography` is installed (already listed in `requirements.txt`).
- PowerShell quoting: prefer the provided PowerShell scripts; when using `python -c`, prefer single-quoted outer strings.

