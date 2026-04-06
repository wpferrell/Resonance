"""
Uses the git credential store to push all updated files to GitHub.
Run from: C:\Users\Shadow\Documents\Resonance
With venv active: .venv\Scripts\Activate.ps1
Then: python push_all_files.py
"""
import subprocess
import sys
import os

os.chdir(r"C:\Users\Shadow\Documents\Resonance")

files = [
    "README.md",
    "ETHICS.md",
    "ROADMAP.md",
    "Resonance_Dataset_Registry.md",
    "scripts/prepare_data_v2.py",
    "pyproject.toml",
]

print("Staging files...")
for f in files:
    result = subprocess.run(["git", "add", f], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR staging {f}: {result.stderr}")
    else:
        print(f"  staged: {f}")

print("\nCommitting...")
msg = "Fix all stale references: 6 frameworks, 10 active heads, v7/30 datasets, add SWMH + Reddit MH MDPI loaders, update pyproject"
result = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print("COMMIT ERROR:", result.stderr)
    sys.exit(1)

print("Pushing...")
result = subprocess.run(["git", "push"], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print("PUSH ERROR:", result.stderr)
    sys.exit(1)

print("\n✅ All done. Changes are live on GitHub.")
print("Note: PyPI publish only triggers on version tag pushes (v*).")
print("To publish to PyPI, bump version and run:")
print("  git tag v1.0.34 && git push origin v1.0.34")
