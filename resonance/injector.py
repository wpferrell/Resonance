# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.
# resonance/injector.py
# Step 11 — LLM Context Injector
# Takes the emotional profile and wraps it into a system prompt.
# This gets delivered to any LLM before every conversation.
# The LLM receives full emotional context about this person
# and instructions on how to respond based on all 8 psychology frameworks.

from resonance.profile import EmotionalProfile, ProfileEngine
from resonance.temporal_graph import TemporalGraph
from resonance.reinforcement import ReinforcementLoop


FRAMEWORK_INSTRUCTIONS = """
PSYCHOLOGY FRAMEWORK INSTRUCTIONS — follow these in every response:

1. VALIDATE BEFORE PROBLEM-SOLVING
   Always acknowledge the person's emotional state before offering advice or solutions.
   Never jump straight to fixing. Reflect first, then help.

2. SELF-DETERMINATION THEORY
   Preserve autonomy at all times. Offer options, never directives.
   Support competence — never make the person feel inadequate.
   Support relatedness — encourage human connection, never dependency on AI.

3. WINDOW OF TOLERANCE
   If the person is in hyperarousal: slow down, use calm language, reduce complexity.
   If the person is in hypoarousal: gently activate, use warm encouraging language.
   If they are in the window: engage fully and directly.

4. WISE MIND
   If emotional mind signals are strong: validate feelings, don't argue with logic.
   If reasonable mind signals are strong: engage intellectually, feelings are secondary.
   If wise mind is present: match their balanced tone, they are grounded.

5. NON-JUDGMENT
   Never imply the person should feel differently than they do.
   Never use language that pathologises normal emotional experience.
   All emotions are valid signals, not problems to fix.

6. REAPPRAISAL VS SUPPRESSION
   If reappraisal is detected: support the healthy processing — affirm their perspective shift.
   If suppression is building: gently create space for the feeling without forcing it.
   Never pressure emotional expression.

7. PERMA FLOURISHING
   Look for opportunities to reinforce positive emotion, engagement, relationships,
   meaning, and accomplishment — without forcing positivity on genuine distress.

8. EMOTIONAL VALIDATION
   Mirror the emotional tone before shifting it.
   If someone is angry, meet the anger with understanding before offering calm.
   If someone is sad, sit with the sadness before offering hope.
"""


class LLMContextInjector:

    def __init__(
        self,
        temporal_graph: TemporalGraph,
        reinforcement_loop: ReinforcementLoop,
    ):
        self.graph = temporal_graph
        self.loop = reinforcement_loop
        self._engine = ProfileEngine(temporal_graph, reinforcement_loop)

    async def build_system_prompt(
        self,
        base_prompt: str = "",
        include_frameworks: bool = True,
    ) -> str:
        """
        Build a complete system prompt that includes:
        - The emotional profile of this person
        - All 8 psychology framework instructions
        - Any optional base prompt from the application

        Pass this as the system prompt to any LLM before every conversation.
        """
        profile: EmotionalProfile = await self._engine.build_profile(limit=200)
        profile_summary = self._engine.summarise(profile)

        sections = []

        if base_prompt:
            sections.append(base_prompt)
            sections.append("")

        sections.append("=" * 60)
        sections.append("RESONANCE — EMOTIONAL CONTEXT FOR THIS PERSON")
        sections.append("=" * 60)
        sections.append("")
        sections.append(profile_summary)
        sections.append("")

        # Add specific warnings based on profile
        warnings = self._build_warnings(profile)
        if warnings:
            sections.append("IMPORTANT FLAGS:")
            sections.extend(warnings)
            sections.append("")

        if include_frameworks:
            sections.append("=" * 60)
            sections.append(FRAMEWORK_INSTRUCTIONS)

        return "\n".join(sections)

    def _build_warnings(self, profile: EmotionalProfile) -> list[str]:
        """
        Build specific warnings based on profile flags.
        These alert the LLM to handle this conversation with extra care.
        """
        warnings = []

        if profile.current_trend == "declining":
            warnings.append("⚠️  Emotional trend is declining — prioritise validation and support.")

        if profile.wot_stability == "unstable":
            warnings.append("⚠️  This person frequently leaves their Window of Tolerance — use regulated, calm language.")

        if profile.hyperarousal_tendency:
            warnings.append("⚠️  Hyperarousal tendency detected — avoid language that increases urgency or pressure.")

        if profile.hypoarousal_tendency:
            warnings.append("⚠️  Hypoarousal tendency detected — use warm, activating language gently.")

        if profile.regulation_style == "suppression":
            warnings.append("⚠️  Suppression pattern detected — create space for feelings without pressure to express.")

        if profile.model_reliability == "low":
            warnings.append("⚠️  Emotion detection reliability is low for this person — treat detections as approximate.")

        if profile.alexithymia_risk:
            warnings.append("⚠️  Low emotional vocabulary detected — this person may struggle to name feelings directly.")

        return warnings

    async def get_current_emotion_context(
        self,
        current_text: str,
    ) -> str:
        """
        Returns a short one-line emotional context string for the current message.
        Can be appended to any user message before sending to the LLM.
        """
        profile: EmotionalProfile = await self._engine.build_profile(limit=50)

        return (
            f"[Resonance: current emotional state — {profile.emotional_tendency}, "
            f"valence {profile.baseline_valence:+.2f}, "
            f"trend {profile.current_trend}, "
            f"WoT {profile.wot_stability}]"
        )
