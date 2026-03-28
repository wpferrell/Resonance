# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.

# resonance/feedback.py
# Handles anonymous correction data collection.
# Corrections queue locally first — always safe, never lost.
# When server is live, queued corrections drain automatically on startup.
# No message text. No user identity. Corrections only.

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

QUEUE_DIR = Path("resonance_data/feedback_queue")

# Stub URL — replaced with live endpoint in Phase 6
FEEDBACK_ENDPOINT = "http://192.168.0.159:8000/corrections"


def queue_correction(detected: str, corrected: str, vad: dict, confidence: float):
    """
    Save a correction to the local queue.
    Called any time a user corrects a detected emotion.
    Always saves locally first — never lost even if offline.
    """
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detected": detected,
        "corrected": corrected,
        "valence": round(vad.get("valence", 0.0), 3),
        "arousal": round(vad.get("arousal", 0.0), 3),
        "dominance": round(vad.get("dominance", 0.0), 3),
        "confidence": round(confidence, 3),
    }

    # Each correction is its own file — no conflicts, no data loss
    filename = QUEUE_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(record, f)


def drain_queue():
    """
    Attempt to send all queued corrections to the feedback endpoint.
    Runs in a background thread — never blocks the main process.
    Successfully sent corrections are removed from the queue.
    Failed sends stay in the queue and are retried next session.
    """
    def _drain():
        if not QUEUE_DIR.exists():
            return

        queue_files = list(QUEUE_DIR.glob("*.json"))
        if not queue_files:
            return

        try:
            import urllib.request
            import urllib.error

            sent = 0
            for filepath in queue_files:
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        record = json.load(f)

                    payload = json.dumps(record).encode("utf-8")
                    req = urllib.request.Request(
                        FEEDBACK_ENDPOINT,
                        data=payload,
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )

                    with urllib.request.urlopen(req, timeout=5) as response:
                        if response.status == 200:
                            filepath.unlink()  # Remove after successful send
                            sent += 1

                except Exception:
                    # Leave in queue — retry next session
                    continue

        except Exception:
            pass  # Never surface feedback errors to the user

    thread = threading.Thread(target=_drain, daemon=True)
    thread.start()


def record_correction(detected: str, corrected: str, vad: dict, confidence: float, feedback_enabled: bool):
    """
    Main entry point for recording a correction.
    Always queues locally. Drains to server if feedback is enabled.
    """
    if feedback_enabled:
        queue_correction(detected, corrected, vad, confidence)
        drain_queue()
