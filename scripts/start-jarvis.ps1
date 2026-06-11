# Start the Jarvis voice UI (Chainlit) on Windows.
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\start-jarvis.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    & .venv\Scripts\python -m pip install --upgrade pip
    & .venv\Scripts\pip install -r requirements.txt
}

if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host ".env created from template — fill in your API keys, then re-run." -ForegroundColor Yellow
    exit 1
}

& .venv\Scripts\python -m jarvis.doctor
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& .venv\Scripts\chainlit run app.py -w
