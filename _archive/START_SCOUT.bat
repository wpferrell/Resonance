@echo off
cd /d "C:\Users\Shadow\Documents\Resonance"
title Resonance Dataset Scout
echo.
echo ============================================================
echo  RESONANCE DATASET SCOUT
echo  Searching 18 sources every 4 hours
echo  Results: scout_results.md
echo  Windows notifications enabled
echo  Press Ctrl+C to stop safely
echo ============================================================
echo.
.venv\Scripts\python.exe scripts\dataset_scout.py
pause
