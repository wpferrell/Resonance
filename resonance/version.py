# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.

# resonance/version.py
# Checks PyPI for newer versions of resonance-layer on startup.
# Notifies the user once per session if an update is available.

__version__ = "1.0.35"

def check_for_update():
    """Check PyPI for a newer version. Notify once per session if found."""
    try:
        import urllib.request
        import json

        url = "https://pypi.org/pypi/resonance-layer/json"
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read())
            latest = data["info"]["version"]

        if latest != __version__:
            from packaging.version import Version
            if Version(latest) > Version(__version__):
                print(f"\n┌─ Resonance Update Available ─────────────────────────┐")
                print(f"│  New version: {latest}  (you have {__version__})              │")
                print(f"│  pip install --upgrade resonance-layer                │")
                print(f"└───────────────────────────────────────────────────────┘\n")
    except Exception:
        # Never block startup due to version check failure
        pass




