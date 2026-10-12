# ClaimGuard-MCP PowerShell Startup Script
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "         ClaimGuard-MCP: Launching Streamlit Web Dashboard             " -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "[INFO] Activating virtual environment (.venv)..." -ForegroundColor Green
    & ".\.venv\Scripts\Activate.ps1"
} elseif (Test-Path ".\.venv\Scripts\python.exe") {
    Write-Host "[INFO] Using .venv Python..." -ForegroundColor Green
    $env:PATH = "$PSScriptRoot\.venv\Scripts;$env:PATH"
} else {
    Write-Host "[WARNING] .venv not found. Using system Python..." -ForegroundColor Yellow
}

Write-Host "[INFO] Starting Streamlit Application on http://localhost:8501..." -ForegroundColor Cyan
Write-Host ""

streamlit run src/ui/app.py
