@echo off
echo ========================================================
echo Pushing sec-forensic-audit-system into LTM_Project
echo ========================================================

set CURRENT_DIR=%~dp0
set TARGET_REPO_URL=https://github.com/kishanptl951/LTM_Project.git
set TEMP_CLONE_DIR=%USERPROFILE%\Desktop\LTM_Project

echo.
echo Step 1: Checking if LTM_Project is already cloned on Desktop...
if not exist "%TEMP_CLONE_DIR%" (
    echo Cloning %TARGET_REPO_URL% to %TEMP_CLONE_DIR%...
    git clone %TARGET_REPO_URL% "%TEMP_CLONE_DIR%"
) else (
    echo %TEMP_CLONE_DIR% already exists. Pulling latest changes...
    cd /d "%TEMP_CLONE_DIR%"
    git pull
)

echo.
echo Step 2: Copying sec-forensic-audit-system into LTM_Project/sec-forensic-audit-system...
robocopy "%CURRENT_DIR%." "%TEMP_CLONE_DIR%\sec-forensic-audit-system" /E /XD .git .venv __pycache__ .pytest_cache /XF push_to_ltm.bat setup_and_push_to_ltm.ps1

echo.
echo Step 3: Committing and pushing to GitHub...
cd /d "%TEMP_CLONE_DIR%"
git add sec-forensic-audit-system
git status
git commit -m "Add sec-forensic-audit-system project"
git push origin HEAD

echo.
echo ========================================================
echo Done! Project pushed to https://github.com/kishanptl951/LTM_Project
echo ========================================================
pause
