@echo off
title ClaimGuard-MCP - Multimodal Insurance Claim Consistency & Fraud Arbiter
echo =======================================================================
echo          ClaimGuard-MCP: Launching Streamlit Web Dashboard
echo =======================================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment (.venv)...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] .venv not found. Using system Python...
)

echo [INFO] Starting Streamlit Application on http://localhost:8501...
echo.

streamlit run src/ui/app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Streamlit encountered an issue or was terminated.
    pause
)
