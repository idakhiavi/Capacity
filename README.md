Capacity Service

Summary
- FastAPI microservice that exposes weekly offered capacity (TEU) as a 4‑week rolling average for the corridor China Main --> North Europe Main.
- Computes the rolling average in SQL and returns one entry per week in the requested date range.
- Defaults to SQLite for zero‑setup local runs, compatible with MySQL 8+!!

Features
- Endpoint: `GET /capacity?date_from&date_to` (YYYY‑MM‑DD) --> list of weeks with `week_start_date`, `week_no`, `offered_capacity_teu`.
- Health endpoint: `GET /health`.
- CSV loader to import the provided sailing‑level dataset into a normalized weekly table.
- Docker image and CI workflow for easy cloning, running, and verification.

Tech Stack & Dependencies
- Python 3.11, FastAPI, Uvicorn
- Pydantic v2, pydantic‑settings
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
git clone https://github.com/idakhiavi/Capacity.git
cd capacity
```

Quickstart (Windows PowerShell)
- Place the provided dataset file at repo root as `sailing_level_raw.csv`.
- Then run:
```
./scripts/dev_run.ps1 -Recreate
```
- This will:
  - Create/activate a venv
  - Install dependencies
  - Load `sailing_level_raw.csv` into SQLite (`.data.sqlite`)
  - Start the API at `http://127.0.0.1:8000`

Docker (optional)
- You do NOT need `dev_run.ps1` when using Docker. The entrypoint creates schema and can auto‑load the CSV on start.

- Build the image:
```
docker build -t capacity-service -f docker/Dockerfile .
```

- Option A — CSV inside the image (place CSV at repo root before build):
```
docker run --rm -p 8000:8000 -e LOAD_CSV_ON_START=1 capacity-service
```

- Option B — Mount your repo (use local CSV without rebuilding):
```
$pwdPath = (Resolve-Path .).Path
docker run --rm -p 8000:8000 -e LOAD_CSV_ON_START=1 -e CSV_PATH=/app/sailing_level_raw.csv -v "$pwdPath:/app" capacity-service
```

- Notes:
  - `LOAD_CSV_ON_START=1` triggers the loader at startup.
  - `CSV_PATH` defaults to `/app/sailing_level_raw.csv`.
  - With Option B, `.data.sqlite` and app files persist in your host directory.

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
    - `week_no` (1–53)
    - `offered_capacity_teu` (integer)

Healthy input hints
- Use ISO dates within the dataset’s expected period: 2024‑01‑01 to 2024‑03‑31.
- The API validates that `date_from <= date_to` and may reject very large ranges (> 3 years).
- Weeks are computed by ISO‑week convention (Monday as start of week).

How data import works
- `scripts/load_weekly_capacity.py` reads `sailing_level_raw.csv` and:
  - If present, deduplicates rows by the combined identifiers:
    `service_version_and_roundtrip_identfiers`, `origin_service_version_and_master`, `destination_service_version_and_master`.
  - For each unique id, it uses the latest `ORIGIN_AT_UTC` from the origin region (as per task note) to determine the week.
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
  - `LOAD_CSV_ON_START` (Docker entrypoint): `1` to auto‑load CSV
  - `CSV_PATH` (Docker entrypoint): CSV path inside the container (default `sailing_level_raw.csv`)

Design Notes
- SQL first: 4‑week rolling average computed in SQL using a window function (`ROWS BETWEEN 3 PRECEDING AND CURRENT ROW`).
- Correctness at the edges: to compute the first in‑range week correctly, the query includes a 3‑week buffer before `date_from`; the service then filters to the exact requested range.
- Simplicity of setup: SQLite by default, but SQL remains compatible with MySQL 8+ (proved by optional CI job).
- Separation of concerns: Repository (SQL), Service (validation/aliasing), Routes (I/O), Models (Pydantic).

Troubleshooting
- Docker Desktop errors on Windows: ensure Docker Desktop is running and using the WSL2 engine.
- Import errors when running scripts: use module mode (`python -m scripts.load_weekly_capacity`).
- MySQL auth error: ensures `cryptography` is installed (already listed in `requirements.txt`).
- PowerShell quoting: prefer the provided PowerShell scripts; when using `python -c`, prefer single‑quoted outer strings.
