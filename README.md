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
