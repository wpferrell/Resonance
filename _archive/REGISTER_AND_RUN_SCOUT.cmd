@echo off
REM Register and immediately run the Resonance Dataset Scout as a scheduled task
REM Run this file as Administrator if needed

schtasks /delete /tn "ResonanceScout" /f >nul 2>&1

schtasks /create /tn "ResonanceScout" /xml "C:\Users\Shadow\Documents\Resonance\scout_task.xml" /f

schtasks /run /tn "ResonanceScout"

echo.
echo Resonance Scout is now running in the background.
echo Check C:\Users\Shadow\Documents\Resonance\scout_results.md for findings.
echo Check C:\Users\Shadow\Documents\Resonance\scout.log for progress.
echo.
echo To stop: schtasks /end /tn "ResonanceScout"
pause
