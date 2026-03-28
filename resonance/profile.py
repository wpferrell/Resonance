# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.
# resonance/profile.py
# Step 10 — Profile Engine
# Reads temporal patterns and correction history.
# Builds a living emotional profile for this person.
# This profile feeds directly into the LLM context injector in Step 11.

from dataclasses import dataclass, field
from typing import Optional
from resonance.temporal_graph import TemporalGraph, TemporalPattern
from resonance.reinforcement import ReinforcementLoop


@dataclass
class EmotionalProfile:
    """
    A living snapshot of who this person is emotionally.
    Built fresh each time from all stored data.
    """

    # Overall emotional baseline
    baseline_valence: float = 0.0       # Their typical valence
    baseline_arousal: float = 0.0       # Their typical arousal
    emotional_tendency: str = "neutral" # Their most common emotion

    # Trajectory
    current_trend: str = "stable"       # improving | declining | stable | volatile

    # Window of Tolerance
    wot_stability: str = "stable"       # How often they leave the window
    hyperarousal_tendency: bool = False # Do they frequently go into hyperarousal?
    hypoarousal_tendency: bool = False  # Do they frequently go into hypoarousal?

    # Emotion regulation style
    regulation_style: str = "unknown"   # reappraisal | suppression | mixed | unknown
    reappraisal_ratio: float = 0.0
    suppression_ratio: float = 0.0

    # Wise mind
    wise_mind_ratio: float = 0.0        # How often they reach wise mind state

    # Alexithymia flag
    alexithymia_risk: bool = False      # Low emotional vocabulary detected

    # Learning — correction patterns
    total_corrections: int = 0
    most_corrected_emotion: Optional[str] = None
    correction_pairs: dict = field(default_factory=dict)
    model_reliability: str = "high"     # high | medium | low

    # Data depth
    sessions_tracked: int = 0
    total_nodes: int = 0
    profile_confidence: str = "low"     # low | medium | high


class ProfileEngine:

    def __init__(
        self,
        temporal_graph: TemporalGraph,
        reinforcement_loop: ReinforcementLoop,
    ):
        self.graph = temporal_graph
        self.loop = reinforcement_loop

    async def build_profile(self, limit: int = 200) -> EmotionalProfile:
        """
        Build a fresh emotional profile from all stored data.
        """
        profile = EmotionalProfile()

        # --- Pull data from both sources ---
        patterns: TemporalPattern = await self.graph.get_patterns(limit=limit)
        correction_summary = await self.loop.get_correction_summary()

        # --- Baseline VAD ---
        profile.baseline_valence = patterns.average_valence
        profile.baseline_arousal = patterns.average_arousal
        profile.emotional_tendency = patterns.dominant_emotion
        profile.current_trend = patterns.valence_trend
        profile.total_nodes = patterns.total_nodes
        profile.sessions_tracked = patterns.sessions_tracked

        # --- Window of Tolerance stability ---
        if patterns.total_nodes > 0:
            wot_exit_rate = (
                patterns.hyperarousal_count + patterns.hypoarousal_count
            ) / patterns.total_nodes

            if wot_exit_rate >= 0.40:
                profile.wot_stability = "unstable"
            elif wot_exit_rate >= 0.20:
                profile.wot_stability = "moderate"
            else:
                profile.wot_stability = "stable"

            profile.hyperarousal_tendency = (
                patterns.hyperarousal_count / patterns.total_nodes >= 0.25
            )
            profile.hypoarousal_tendency = (
                patterns.hypoarousal_count / patterns.total_nodes >= 0.25
            )

        # --- Emotion regulation style ---
        profile.reappraisal_ratio = patterns.reappraisal_ratio
        profile.suppression_ratio = patterns.suppression_ratio

        if patterns.reappraisal_ratio >= 0.40 and patterns.suppression_ratio < 0.20:
            profile.regulation_style = "reappraisal"
        elif patterns.suppression_ratio >= 0.40 and patterns.reappraisal_ratio < 0.20:
            profile.regulation_style = "suppression"
        elif patterns.reappraisal_ratio >= 0.20 and patterns.suppression_ratio >= 0.20:
            profile.regulation_style = "mixed"
        else:
            profile.regulation_style = "unknown"

        # --- Wise mind ---
        profile.wise_mind_ratio = patterns.wise_mind_ratio

        # --- Correction history ---
        profile.total_corrections = correction_summary["total_corrections"]
        profile.most_corrected_emotion = correction_summary["most_corrected_emotion"]
        profile.correction_pairs = correction_summary["correction_pairs"]

        # Model reliability based on correction rate
        if patterns.total_nodes > 0:
            correction_rate = profile.total_corrections / patterns.total_nodes
            if correction_rate >= 0.30:
                profile.model_reliability = "low"
            elif correction_rate >= 0.10:
                profile.model_reliability = "medium"
            else:
                profile.model_reliability = "high"

        # --- Profile confidence based on data depth ---
        if patterns.total_nodes >= 50:
            profile.profile_confidence = "high"
        elif patterns.total_nodes >= 10:
            profile.profile_confidence = "medium"
        else:
            profile.profile_confidence = "low"

        return profile

    def summarise(self, profile: EmotionalProfile) -> str:
        """
        Returns a plain English summary of the profile.
        This is what gets handed to the LLM in Step 11.
        """
        lines = []

        lines.append(f"Emotional baseline: {profile.emotional_tendency} "
                     f"(valence {profile.baseline_valence:+.2f}, "
                     f"arousal {profile.baseline_arousal:+.2f})")

        lines.append(f"Current trend: {profile.current_trend}")

        lines.append(f"Window of Tolerance stability: {profile.wot_stability}")

        if profile.hyperarousal_tendency:
            lines.append("Tendency toward hyperarousal — responds with urgency or intensity.")
        if profile.hypoarousal_tendency:
            lines.append("Tendency toward hypoarousal — can become withdrawn or flat.")

        lines.append(f"Emotion regulation style: {profile.regulation_style} "
                     f"(reappraisal {profile.reappraisal_ratio:.0%}, "
                     f"suppression {profile.suppression_ratio:.0%})")

        if profile.wise_mind_ratio >= 0.20:
            lines.append("Frequently reaches wise mind state — balanced and grounded.")

        if profile.total_corrections > 0:
            lines.append(f"Model has been corrected {profile.total_corrections} time(s). "
                         f"Most corrected emotion: {profile.most_corrected_emotion}.")

        lines.append(f"Profile confidence: {profile.profile_confidence} "
                     f"({profile.total_nodes} data points across "
                     f"{profile.sessions_tracked} session(s))")

        return "\n".join(lines)
