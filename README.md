Capacity Service

Run this project quickly with either local PowerShell or Docker. Copy/paste the commands as-is from your repo root.

Quickstart (Local, Windows PowerShell)
1) Create and activate a virtual environment, then install dependencies
```
py -3 -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Load the sample CSV into SQLite and start the API
```
./scripts/dev_run.ps1 -Recreate
```

3) Check the API
```
http://127.0.0.1:8000/health
http://127.0.0.1:8000/capacity?date_from=2024-01-15&date_to=2024-02-12
```

Quickstart (Docker)
1) Build the image
```
docker build -t capacity-service -f docker/Dockerfile .
```

2) Run and auto-load CSV (CSV file at repo root)
```
docker run --rm -p 8000:8000 -e LOAD_CSV_ON_START=1 capacity-service
```

Or mount your repo (no rebuild)
```
$pwdPath = (Resolve-Path .).Path
docker run --rm -p 8000:8000 -e LOAD_CSV_ON_START=1 -e CSV_PATH=/app/sailing_level_raw.csv -v "$pwdPath:/app" capacity-service
```

3) Check the API
```
http://127.0.0.1:8000/health
http://127.0.0.1:8000/capacity?date_from=2024-01-15&date_to=2024-02-12
```

Healthy date examples
- Mondays align best with weekly rows. Example: `date_from=2024-01-15`, `date_to=2024-02-12` (5 weeks).
- Use dates within the sample period: 2024-01-01 to 2024-03-31.

.env (optional)
Create a `.env` file at repo root to override defaults. The app reads it automatically.
```
LOG_LEVEL=INFO
DATABASE_URL=sqlite+pysqlite:///./.data.sqlite
CORRIDOR_ALIAS_FILE=config/corridor_aliases.json
LOAD_CSV_ON_START=1
CSV_PATH=/app/sailing_level_raw.csv
```
With Docker, pass it using:
```
docker run --rm --env-file .env -p 8000:8000 capacity-service
```

Troubleshooting
- Docker Desktop required for Docker commands; ensure WSL2 engine is enabled on Windows.
- If you previously saw errors like `set: pipefail` or `$'\r': command not found`, rebuild the image (entrypoint uses POSIX sh and line endings are normalized).
- If `ModuleNotFoundError` occurs locally, ensure your venv is activated and run:
```
pip install -r requirements.txt
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
