# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.
# resonance/comparison.py
# Step 7 — Comparison Engine
# Detects emotional change between the current message and recent history.
# Outputs ComparisonResult with delta, trajectory, spike flags, and WoT crossing.

from dataclasses import dataclass, field
from typing import Optional
import statistics
from resonance.extractor import EmotionResult


@dataclass
class ComparisonResult:
    # How much each VAD dimension shifted from the previous message
    valence_delta: float = 0.0
    arousal_delta: float = 0.0
    dominance_delta: float = 0.0

    # Direction of travel over last N messages
    # "improving" | "declining" | "stable" | "volatile"
    trajectory: str = "stable"

    # Did any single dimension jump hard in one message?
    spike_detected: bool = False
    spike_dimension: Optional[str] = None  # "valence" | "arousal" | "dominance"

    # Did the person just cross into or out of Window of Tolerance?
    wot_crossing: bool = False
    wot_direction: Optional[str] = None  # "into_hyper" | "into_hypo" | "into_window"

    # Is reappraisal signal trending up (healthy processing)?
    reappraisal_trending: bool = False

    # Is suppression signal building?
    suppression_building: bool = False

    # How many recent messages were used for comparison
    history_depth: int = 0

    # Raw recent VAD values used for trajectory calculation
    recent_valence: list = field(default_factory=list)
    recent_arousal: list = field(default_factory=list)


# Thresholds — tuned to VAD scale of -1.0 to 1.0
SPIKE_THRESHOLD = 0.35       # single-message jump this large = spike
VOLATILE_THRESHOLD = 0.20    # std dev this high = volatile trajectory
STABLE_THRESHOLD = 0.08      # std dev this low = stable trajectory
REAPPRAISAL_WINDOW = 10      # messages to check for reappraisal trend
SUPPRESSION_WINDOW = 10      # messages to check for suppression build


def compare(
    current: EmotionResult,
    history: list[EmotionResult]
) -> ComparisonResult:
    """
    Compare current EmotionResult against recent history.
    history = list of EmotionResult, oldest first, most recent last.
    Returns a ComparisonResult.
    """
    result = ComparisonResult()
    result.history_depth = len(history)

    if not history:
        return result

    # --- Delta from previous message ---
    prev = history[-1]
    result.valence_delta = current.valence - prev.valence
    result.arousal_delta = current.arousal - prev.arousal
    result.dominance_delta = current.dominance - prev.dominance

    # --- Spike detection ---
    for dim, delta in [
        ("valence", result.valence_delta),
        ("arousal", result.arousal_delta),
        ("dominance", result.dominance_delta),
    ]:
        if abs(delta) >= SPIKE_THRESHOLD:
            result.spike_detected = True
            result.spike_dimension = dim
            break

    # --- Trajectory over recent history ---
    valence_series = [e.valence for e in history] + [current.valence]
    arousal_series = [e.arousal for e in history] + [current.arousal]

    result.recent_valence = valence_series
    result.recent_arousal = arousal_series

    if len(valence_series) >= 3:
        v_std = statistics.stdev(valence_series)
        a_std = statistics.stdev(arousal_series)
        combined_std = (v_std + a_std) / 2

        if combined_std >= VOLATILE_THRESHOLD:
            result.trajectory = "volatile"
        elif combined_std <= STABLE_THRESHOLD:
            result.trajectory = "stable"
        else:
            mid = len(valence_series) // 2
            early_mean = statistics.mean(valence_series[:mid])
            late_mean = statistics.mean(valence_series[mid:])
            if late_mean - early_mean >= 0.10:
                result.trajectory = "improving"
            elif early_mean - late_mean >= 0.10:
                result.trajectory = "declining"
            else:
                result.trajectory = "stable"

    # --- Window of Tolerance crossing ---
    prev_wot = prev.window_of_tolerance
    curr_wot = current.window_of_tolerance

    if prev_wot != curr_wot:
        result.wot_crossing = True
        if curr_wot == "hyperarousal":
            result.wot_direction = "into_hyper"
        elif curr_wot == "hypoarousal":
            result.wot_direction = "into_hypo"
        else:
            result.wot_direction = "into_window"

    # --- Reappraisal trending (last N messages) ---
    recent_window = history[-REAPPRAISAL_WINDOW:]
    if len(recent_window) >= 3:
        reappraisal_scores = [
            1 if e.reappraisal_signal else 0
            for e in recent_window
        ]
        mid = len(reappraisal_scores) // 2
        if sum(reappraisal_scores[mid:]) > sum(reappraisal_scores[:mid]):
            result.reappraisal_trending = True

    # --- Suppression building (last N messages) ---
    recent_window = history[-SUPPRESSION_WINDOW:]
    if len(recent_window) >= 3:
        suppression_scores = [
            1 if e.suppression_signal else 0
            for e in recent_window
        ]
        mid = len(suppression_scores) // 2
        if sum(suppression_scores[mid:]) > sum(suppression_scores[:mid]):
            result.suppression_building = True

    return result
