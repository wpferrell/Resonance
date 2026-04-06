Set oShell = CreateObject("WScript.Shell")
oShell.Run "powershell.exe -NoExit -Command ""cd 'C:\Users\Shadow\Documents\Resonance'; .\.venv\Scripts\Activate.ps1; python scripts\dataset_scout.py""", 1, False
