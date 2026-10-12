# PowerShell Script to copy sec-forensic-audit-system into LTM_Project and push to GitHub
$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Push sec-forensic-audit-system into LTM_Project repo " -ForegroundColor Cyan
Write-Host " Target: https://github.com/kishanptl951/LTM_Project " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$CurrentDir = $PSScriptRoot
$DesktopDir = [System.Environment]::GetFolderPath("Desktop")
$TargetRepoUrl = "https://github.com/kishanptl951/LTM_Project.git"
$TargetDir = Join-Path $DesktopDir "LTM_Project"

Write-Host "`n[1/3] Setting up local clone of LTM_Project..." -ForegroundColor Yellow
if (-not (Test-Path $TargetDir)) {
    Write-Host "Cloning $TargetRepoUrl to $TargetDir..."
    git clone $TargetRepoUrl $TargetDir
} else {
    Write-Host "Repo directory $TargetDir already exists. Pulling latest..."
    Push-Location $TargetDir
    try { git pull } catch { Write-Warning "Pull failed or repo is empty, continuing..." }
    Pop-Location
}

Write-Host "`n[2/3] Copying files into $TargetDir\sec-forensic-audit-system..." -ForegroundColor Yellow
$DestProjectDir = Join-Path $TargetDir "sec-forensic-audit-system"
if (-not (Test-Path $DestProjectDir)) {
    New-Item -ItemType Directory -Path $DestProjectDir -Force | Out-Null
}

# Use robocopy to exclude .git, .venv, pycache
$robocopyArgs = @(
    $CurrentDir,
    $DestProjectDir,
    "/E",
    "/XD", ".git", ".venv", "__pycache__", ".pytest_cache",
    "/XF", "push_to_ltm.bat", "push_to_ltm.ps1"
)
& robocopy @robocopyArgs | Out-Null
if ($LASTEXITCODE -ge 8) {
    Write-Error "Robocopy encountered an error with exit code $LASTEXITCODE"
} else {
    Write-Host "Files copied successfully (excluding .venv and .git)!" -ForegroundColor Green
}

Write-Host "`n[3/3] Committing and pushing to GitHub..." -ForegroundColor Yellow
Push-Location $TargetDir
try {
    git add sec-forensic-audit-system
    $status = git status --porcelain
    if (-not $status) {
        Write-Host "No changes to commit. Everything is up to date." -ForegroundColor Cyan
    } else {
        git commit -m "Add sec-forensic-audit-system project"
        # Push to remote branch
        git push origin HEAD
        Write-Host "`nSuccessfully pushed to https://github.com/kishanptl951/LTM_Project!" -ForegroundColor Green
    }
} catch {
    Write-Error "Git commit/push failed: $_"
} finally {
    Pop-Location
}

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host " Complete! Check https://github.com/kishanptl951/LTM_Project" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
