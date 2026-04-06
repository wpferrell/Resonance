# Resonance Dataset Scout + Scholar Alerts Launcher
# Run this script — it starts the scout AND opens the Scholar alerts page
# 
# Usage: Right-click → Run with PowerShell
#        OR in PowerShell: .\scripts\launch_resonance_scout.ps1

$projectDir = "C:\Users\Shadow\Documents\Resonance"
$venvPython  = "$projectDir\.venv\Scripts\python.exe"
$scoutScript = "$projectDir\scripts\dataset_scout.py"
$alertsPage  = "$projectDir\Resonance_Scholar_Alerts.html"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        RESONANCE DATASET SCOUT + ALERTS          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 1. Open Scholar alerts page in browser
Write-Host "Opening Scholar alerts setup page..." -ForegroundColor Yellow
Start-Process $alertsPage
Start-Sleep -Seconds 2

# 2. Start the scout
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: venv not found at $venvPython" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Starting Dataset Scout..." -ForegroundColor Green
Write-Host "Results  → $projectDir\scout_results.md" -ForegroundColor Gray
Write-Host "Log      → $projectDir\scout.log" -ForegroundColor Gray
Write-Host "Seen     → $projectDir\scout_seen.json" -ForegroundColor Gray
Write-Host ""
Write-Host "You will get a Windows notification when a dataset is found." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the scout safely." -ForegroundColor Gray
Write-Host ""

Set-Location $projectDir
& $venvPython $scoutScript
