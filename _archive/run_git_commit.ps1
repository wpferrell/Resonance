# Resonance — git commit and push all April 2026 fixes
# Run this once from PowerShell in the Resonance directory

Set-Location "C:\Users\Shadow\Documents\Resonance"

git add README.md
git add ETHICS.md
git add ROADMAP.md
git add Resonance_Dataset_Registry.md
git add scripts\prepare_data_v2.py
git add pyproject.toml

git commit -m "Fix all stale references: 6 frameworks, 10 active heads, v7/30 datasets, add SWMH + Reddit MH MDPI loaders, update pyproject description and keywords"

git push

Write-Host ""
Write-Host "Done. Check above for any errors."
Write-Host "If push succeeded, all fixes are live on GitHub."
