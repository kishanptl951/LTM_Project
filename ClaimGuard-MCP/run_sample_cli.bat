@echo off
title ClaimGuard-MCP - Run Sample CLI Claim
echo =======================================================================
echo          ClaimGuard-MCP: Running Sample Claim Package Evaluation
echo =======================================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment (.venv)...
    call .venv\Scripts\activate.bat
)

echo [INFO] Executing pipeline for sample claim dossier: data/sample_claims/realistic_package
echo.

python -m src.app --package data/sample_claims/realistic_package --claim-id CLM-001

echo.
pause
