Capacity Service

Current Progress
- Repository initialized with Python `.gitignore`.
- Added minimal `requirements.txt` with FastAPI and Uvicorn.
- Scaffolded a minimal FastAPI app with `/health` endpoint and a smoke test.
- Added configuration (settings, logging), database engine, schema helper, and alias map.
- Implemented repository with SQL 4-week rolling average and service layer with validation; added unit tests.
- Set API models to include `week_no` and `offered_capacity_teu` to align with task wording.
- Wired `/capacity` endpoint (date_from, date_to) and added SQLite integration test with DI override.
- Added data loader script (`scripts/load_weekly_capacity.py`) and dev helper (`scripts/dev_run.ps1`).
- Enhanced CSV loader to deduplicate by unique identifiers when present and use latest origin departure.
- Added Dockerfile and entrypoint for simple containerized runs; optional MySQL integration test.
- Added pytest config and CI workflow; see USAGE.md for quickstart.

Quickstart
- Local (PowerShell): `./scripts/dev_run.ps1 -Recreate`
- Docker: `docker build -t capacity-service -f docker/Dockerfile . && docker run --rm -p 8000:8000 -e LOAD_CSV_ON_START=1 capacity-service`
- API: `http://127.0.0.1:8000/capacity?date_from=2024-01-15&date_to=2024-02-12`
