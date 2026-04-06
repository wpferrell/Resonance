# Resonance Dataset Scout — Background Launcher
# Double-click this file, or run from PowerShell, to start the scout.
# It runs in a new minimised window so it doesn't get in the way.
# Close the window or press Ctrl+C in it to stop safely.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
$venvPython = Join-Path $projectDir ".venv\Scripts\python.exe"
$scoutScript = Join-Path $scriptDir "dataset_scout.py"

# Verify python exists
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: venv python not found at $venvPython" -ForegroundColor Red
    Write-Host "Make sure the venv exists: python -m venv .venv" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "Starting Resonance Dataset Scout..." -ForegroundColor Cyan
Write-Host "Results -> $projectDir\scout_results.md" -ForegroundColor Green
Write-Host "Log     -> $projectDir\scout.log" -ForegroundColor Green
Write-Host "You will get a Windows notification whenever a dataset is found." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the scout safely." -ForegroundColor Gray
Write-Host ""

# Run the scout — stays in this window so you can see live output
& $venvPython $scoutScript
