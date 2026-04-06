@echo off
cd /d "C:\Users\Shadow\Documents\Resonance"
echo Activating venv...
call .venv\Scripts\activate.bat
echo.
echo Staging files...
git add README.md
git add ETHICS.md
git add ROADMAP.md
git add Resonance_Dataset_Registry.md
git add scripts\prepare_data_v2.py
git add pyproject.toml
echo.
echo Committing...
git commit -m "Fix all stale references: 6 frameworks, 10 active heads, v7/30 datasets, add SWMH + Reddit MH MDPI loaders, update pyproject description and keywords"
echo.
echo Pushing...
git push
echo.
echo ========================================
echo DONE. Check output above for any errors.
echo ========================================
pause
