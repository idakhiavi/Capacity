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
  python -m scripts.load_weekly_capacity --csv $CsvPath --truncate
} else {
  python -m scripts.load_weekly_capacity --csv $CsvPath
}

# Run the app
uvicorn app.main:app --reload
