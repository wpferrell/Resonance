# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.

# resonance/__init__.py
# Package entry point.
# On import: checks for updates, runs first-time config prompt if needed,
# then exposes the main Resonance interface.

from .version import __version__, check_for_update
from .config import ensure_config
from .extractor import EmotionExtractor, EmotionResult
from .storage import ResonanceStorage
from .profile import ProfileEngine
from .injector import ContextInjector
from .feedback import record_correction, drain_queue

# Run version check and config on import
check_for_update()
_config = ensure_config()

# Drain any queued feedback corrections in the background
if _config.get("feedback_enabled"):
    drain_queue()


class Resonance:
    """
    Main Resonance interface.
    Detects emotion, stores it, builds a profile,
    and injects emotional context into any LLM.

    Usage:
        from resonance import Resonance
        r = Resonance(user_id="123")
        context = r.process("I've been so anxious about this")
        llm.chat(system=context.to_prompt(), message=message)
    """

    def __init__(self, user_id: str, data_dir: str = "resonance_data"):
        self.user_id = user_id
        self.feedback_enabled = _config.get("feedback_enabled", False)
        self.extractor = EmotionExtractor()
        self.storage = ResonanceStorage(data_dir=data_dir)
        self.profile_engine = ProfileEngine(storage=self.storage)
        self.injector = ContextInjector()

    def process(self, message: str, modality: str = "text") -> "ContextInjector":
        """
        Process a message. Detect emotion, store it, update profile.
        Returns a context injector ready to pass to any LLM.
        """
        result = self.extractor.extract(message, modality=modality)
        self.storage.store(self.user_id, result)
        profile = self.profile_engine.build(self.user_id)
        return self.injector.prepare(result, profile)

    def correct(self, detected: str, corrected: str, result: EmotionResult):
        """
        Record a user correction. Updates the reinforcement loop.
        If feedback is enabled, queues the correction for anonymous sharing.
        """
        vad = {
            "valence": result.valence,
            "arousal": result.arousal,
            "dominance": result.dominance,
        }
        record_correction(
            detected=detected,
            corrected=corrected,
            vad=vad,
            confidence=result.confidence,
            feedback_enabled=self.feedback_enabled,
        )

    def set_feedback(self, enabled: bool):
        """Change feedback sharing setting at any time."""
        from .config import set_feedback
        set_feedback(enabled)
        self.feedback_enabled = enabled


__all__ = ["Resonance", "EmotionResult", "__version__"]
