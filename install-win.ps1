# Resonance -- Windows Install Script
# https://resonance-layer.com
# Run with: irm https://install.resonance-layer.com/install-win.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "+----------------------------------------------------------+"
Write-Host "|          Resonance -- Emotional Memory for AI           |"
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

Write-Host "Installing resonance-layer..."
& "$venvDir\Scripts\pip" install --quiet resonance-layer
Write-Host "OK: Resonance installed"

Write-Host ""
Write-Host "+----------------------------------------------------------+"
Write-Host "|                  Installation Complete                  |"
Write-Host "+----------------------------------------------------------+"
Write-Host ""
Write-Host "To activate Resonance:"
Write-Host "  $venvDir\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Then in your Python project:"
Write-Host "  from resonance import Resonance"
Write-Host "  r = Resonance(user_id='your-user-id')"
Write-Host ""
Write-Host "The first time you use Resonance, it will:"
Write-Host "  - Ask you one question about data sharing"
Write-Host "  - Download the emotion model (one time only)"
Write-Host "  - Be ready to use"
Write-Host ""
Write-Host "Developer guide: https://resonance-layer.com/guide"
Write-Host "User guide:      https://resonance-layer.com/user-guide"
Write-Host ""
