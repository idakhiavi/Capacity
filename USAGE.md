Quickstart

Local (Windows PowerShell)
- Create venv, install deps, load CSV, run server:
```
\scripts\dev_run.ps1 -Recreate
```
- Query the API:
```
http://127.0.0.1:8000/capacity?date_from=2024-01-15&date_to=2024-02-12
```

Run tests
```
py -3 -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

Docker
```
docker build -t capacity-service -f docker/Dockerfile .
docker run --rm -p 8000:8000 -e LOAD_CSV_ON_START=1 -e CSV_PATH=/app/sailing_level_raw.csv -v ${PWD}:/app capacity-service
```

Notes
- Default DB is SQLite file at `./.data.sqlite`.
- Schema is created automatically on startup.
- CSV loader expects `sailing_level_raw.csv` in repo root (path can be overridden).
