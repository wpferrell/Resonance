# Start dataset scout in a new visible PowerShell window
# Runs independently — close the window or Ctrl+C to stop

$project = "C:\Users\Shadow\Documents\Resonance"
$python  = "$project\.venv\Scripts\python.exe"
$script  = "$project\scripts\dataset_scout.py"

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$project'; & '$python' '$script'"
) -WindowStyle Normal
