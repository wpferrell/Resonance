# Resonance -- Windows Install Script
# https://resonance-layer.com
# Run with: irm https://install.resonance-layer.com/install-win.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "+----------------------------------------------------------+"
Write-Host "|          Resonance -- Emotional Memory for AI            |"
Write-Host "+----------------------------------------------------------+"
Write-Host ""
Write-Host "Installing Resonance on Windows..."
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.(\d+)") {
        $minorVersion = [int]$matches[1]
        if ($minorVersion -lt 10) {
            Write-Host "ERROR: Python 3.10 or higher is required."
            Write-Host "  Download the latest from: https://www.python.org/downloads/"
            exit 1
        }
    }
    Write-Host "OK: $pythonVersion found"
} catch {
    Write-Host "ERROR: Python is required but not installed."
    Write-Host "  Download it from: https://www.python.org/downloads/"
    Write-Host "  Make sure to check 'Add Python to PATH' during install."
    exit 1
}

$venvDir = "$HOME\resonance"
Write-Host "Creating virtual environment at $venvDir..."
python -m venv $venvDir
Write-Host "OK: Virtual environment created"
Write-Host ""
Write-Host "Installing resonance-layer..."
Write-Host ""

$job = Start-Job -ScriptBlock {
    param($venvDir)
    & "$venvDir\Scripts\pip" install --quiet --disable-pip-version-check --upgrade resonance-layer 2>&1
} -ArgumentList $venvDir

$spinner = @('|', '/', '-', '\')
$i = 0
while ($job.State -eq 'Running') {
    Write-Host -NoNewline "  Installing... $($spinner[$i % 4])   "
    $i++
    Start-Sleep -Milliseconds 200
}

Receive-Job $job | Out-Null
Remove-Job $job
Write-Host "  [########################################] 100%  "
Write-Host ""
Write-Host "OK: Resonance installed"
Write-Host ""
Write-Host "Setting up Resonance (first run only)..."
Write-Host ""
& "$venvDir\Scripts\python" -c "from resonance import Resonance; Resonance(user_id='_setup')"
Write-Host ""
Write-Host "+----------------------------------------------------------+"
Write-Host "|                   Resonance is ready.                    |"
Write-Host "+----------------------------------------------------------+"
Write-Host ""
Write-Host "Resonance is installed and ready to use."
Write-Host ""
Write-Host "Add it to any Python project:"
Write-Host "  from resonance import Resonance"
Write-Host "  r = Resonance(user_id='your-user-id')"
Write-Host ""
Write-Host "Developer guide: https://resonance-layer.com/guide"
Write-Host "User guide:      https://resonance-layer.com/user-guide"
Write-Host ""
