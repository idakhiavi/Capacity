Param(
    [string]$CsvPath = "sailing_level_raw.csv",
    [switch]$Recreate
)

# Create venv if missing
if (-not (Test-Path .\.venv)) {
  py -3 -m venv .venv
}
. .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt | Out-Null

# Ensure schema and load data
if ($Recreate) {
  python .\scripts\load_weekly_capacity.py --csv $CsvPath --truncate
} else {
  python .\scripts\load_weekly_capacity.py --csv $CsvPath
}

# Run the app
uvicorn app.main:app --reload

