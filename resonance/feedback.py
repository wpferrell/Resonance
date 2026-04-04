# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.

# resonance/feedback.py
# Handles anonymous feedback collection.
# Emotion signals and conversation patterns queue locally first — always safe, never lost.
# When server is reachable, queued records drain automatically.
# No message text. No user identity. Ever.

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

QUEUE_DIR = Path.home() / ".resonance" / "feedback_queue"
FEEDBACK_ENDPOINT = "https://feedback.resonance-layer.com/feedback"


def _anonymous_id(user_id: str) -> str:
    """One-way hash of user_id — never reversible back to the original."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def queue_record(record: dict):
    """Save a feedback record to the local queue. Never lost even if offline."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    filename = QUEUE_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(record, f)


def drain_queue():
    """
    Send all queued records to the feedback endpoint.
    Runs in a background thread — never blocks the main process.
    Successfully sent records are removed. Failed sends stay and retry next session.
    """
    def _drain():
        if not QUEUE_DIR.exists():
            return
        queue_files = list(QUEUE_DIR.glob("*.json"))
        if not queue_files:
            return
        try:
            import urllib.request
            for filepath in queue_files:
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        record = json.load(f)
                    payload = json.dumps(record).encode("utf-8")
                    req = urllib.request.Request(
                        FEEDBACK_ENDPOINT,
                        data=payload,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "Resonance/1.0",
                        },
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=5) as response:
                        if response.status == 200:
                            filepath.unlink()
                except Exception:
                    continue
        except Exception:
            pass

    thread = threading.Thread(target=_drain, daemon=True)
    thread.start()


def record_feedback(
    user_id: str,
    primary_emotion: str,
    confidence: float,
    valence: float,
    arousal: float,
    dominance: float,
    corrected_emotion: str = None,
    feedback_enabled: bool = False,
):
    """
    Main entry point for recording a feedback event.
    Called after every emotion detection.
    corrected_emotion is set when the user picks a different chip.
    Always queues locally. Drains to server only if feedback is enabled.
    """
    if not feedback_enabled:
        return

    record = {
        "user_id": _anonymous_id(user_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "primary_emotion": primary_emotion,
        "confidence": round(confidence, 3),
        "valence": round(valence, 3),
        "arousal": round(arousal, 3),
        "dominance": round(dominance, 3),
        "corrected_emotion": corrected_emotion,
    }

    queue_record(record)
    drain_queue()
