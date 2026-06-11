# Start the TradingView -> Zerodha webhook executor on Windows.
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\start-executor.ps1
# Expose publicly for TradingView with:  ngrok http 8080
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path ".venv")) {
    Write-Host "Run scripts\start-jarvis.ps1 first to set up the environment." -ForegroundColor Yellow
    exit 1
}

& .venv\Scripts\uvicorn jarvis.trading.webhook_listener:app --host 0.0.0.0 --port 8080
