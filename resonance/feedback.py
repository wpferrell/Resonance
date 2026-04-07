# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.

# resonance/feedback.py
# Handles anonymous feedback collection.
# Emotion signals and conversation patterns queue locally first -- always safe, never lost.
# When server is reachable, queued records drain automatically.
# No message text. No user identity. Ever.
#
# v2: P3 fields added -- PERMA, SDT, wot_trajectory, scored floats.
# All new fields are optional with defaults so existing queue files still drain correctly.

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

QUEUE_DIR = Path.home() / ".resonance" / "feedback_queue"
FEEDBACK_ENDPOINT = "https://feedback.resonance-layer.com/feedback"
TRAJECTORY_ENDPOINT = "https://feedback.resonance-layer.com/trajectory"


def _anonymous_id(user_id: str) -> str:
    """One-way hash of user_id -- never reversible back to the original."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def queue_record(record: dict, prefix: str = "fb"):
    """Save a feedback record to the local queue. Never lost even if offline."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    filename = QUEUE_DIR / f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(record, f)


def drain_queue():
    """
    Send all queued records to the feedback endpoint.
    Runs in a background thread -- never blocks the main process.
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
                    endpoint = TRAJECTORY_ENDPOINT if record.get("record_type") == "trajectory" else FEEDBACK_ENDPOINT
                    payload = json.dumps(record).encode("utf-8")
                    req = urllib.request.Request(
                        endpoint,
                        data=payload,
                        headers={"Content-Type": "application/json", "User-Agent": "Resonance/1.0"},
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
    # P3 fields -- all optional, default None
    perma_p: float = None,
    perma_e: float = None,
    perma_r: float = None,
    perma_m: float = None,
    perma_a: float = None,
    autonomy_signal: float = None,
    competence_signal: float = None,
    relatedness_signal: float = None,
    wise_mind_score: float = None,
    reappraisal_score: float = None,
    suppression_score: float = None,
    wot_trajectory: str = None,
    crisis_detected: bool = None,
    sustained_distress: bool = None,
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
        "record_type": "feedback",
        "user_id": _anonymous_id(user_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "primary_emotion": primary_emotion,
        "confidence": round(confidence, 3),
        "valence": round(valence, 3),
        "arousal": round(arousal, 3),
        "dominance": round(dominance, 3),
        "corrected_emotion": corrected_emotion,
    }

    # Add P3 fields if present
    p3_fields = {
        "perma_p": perma_p, "perma_e": perma_e, "perma_r": perma_r,
        "perma_m": perma_m, "perma_a": perma_a,
        "autonomy_signal": autonomy_signal, "competence_signal": competence_signal,
        "relatedness_signal": relatedness_signal, "wise_mind_score": wise_mind_score,
        "reappraisal_score": reappraisal_score, "suppression_score": suppression_score,
        "wot_trajectory": wot_trajectory, "crisis_detected": crisis_detected,
        "sustained_distress": sustained_distress,
    }
    record.update({k: round(v, 3) if isinstance(v, float) else v
                   for k, v in p3_fields.items() if v is not None})

    queue_record(record, prefix="fb")
    drain_queue()


def record_trajectory(
    user_id: str,
    session_id: str,
    prev_emotion: str,
    curr_emotion: str,
    prev_valence: float,
    curr_valence: float,
    prev_arousal: float,
    curr_arousal: float,
    prev_dominance: float,
    curr_dominance: float,
    prev_wot: str,
    curr_wot: str,
    prev_wise_mind: float,
    curr_wise_mind: float,
    reappraisal_signal: float,
    suppression_signal: float,
    confidence: float,
    feedback_enabled: bool = False,
    # P3 trajectory fields -- all optional
    wot_trajectory: str = None,
    suppression_score: float = None,
    reappraisal_score: float = None,
    wise_mind_score: float = None,
    session_trajectory: str = None,
    perma_p: float = None,
    perma_e: float = None,
    perma_r: float = None,
    perma_m: float = None,
    perma_a: float = None,
):
    """
    Record the emotional shift between two consecutive messages.
    Called automatically by r.process() after every second message.
    Zero developer work required -- happens silently in the background.
    """
    if not feedback_enabled:
        return

    record = {
        "record_type": "trajectory",
        "user_id": _anonymous_id(user_id),
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prev_emotion": prev_emotion,
        "curr_emotion": curr_emotion,
        "valence_shift": round(curr_valence - prev_valence, 3),
        "arousal_shift": round(curr_arousal - prev_arousal, 3),
        "dominance_shift": round(curr_dominance - prev_dominance, 3),
        "prev_wot": prev_wot,
        "curr_wot": curr_wot,
        "wise_mind_shift": round(curr_wise_mind - prev_wise_mind, 3),
        "reappraisal_signal": round(reappraisal_signal, 3),
        "suppression_signal": round(suppression_signal, 3),
        "confidence": round(confidence, 3),
    }

    # Add P3 trajectory fields if present
    p3_fields = {
        "wot_trajectory": wot_trajectory,
        "suppression_score": suppression_score,
        "reappraisal_score": reappraisal_score,
        "wise_mind_score": wise_mind_score,
        "session_trajectory": session_trajectory,
        "perma_p": perma_p, "perma_e": perma_e,
        "perma_r": perma_r, "perma_m": perma_m, "perma_a": perma_a,
    }
    record.update({k: round(v, 3) if isinstance(v, float) else v
                   for k, v in p3_fields.items() if v is not None})

    queue_record(record, prefix="traj")
    drain_queue()
