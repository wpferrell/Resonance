import warnings
warnings.filterwarnings("ignore", message=".*sys.meta_path.*")

# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.

# resonance/__init__.py
# Package entry point.
# On import: checks for updates, runs first-time config prompt if needed,
# then exposes the main Resonance interface.

from .model_loader import ensure_model_downloaded
from .version import __version__, check_for_update
from .config import ensure_config
from .extractor import Extractor, EmotionResult
from .storage import Storage
from .temporal_graph import TemporalGraph
from .reinforcement import ReinforcementLoop
from .profile import ProfileEngine
from .injector import LLMContextInjector
from .feedback import record_feedback, record_trajectory, drain_queue
import uuid

# Run version check and config on import
check_for_update()
_config = ensure_config()

# Download model weights on first run
ensure_model_downloaded()

# Drain any queued feedback in the background
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

    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.feedback_enabled = _config.get("feedback_enabled", False)
        self.extractor = Extractor()
        self.storage = Storage()
        self.temporal_graph = TemporalGraph()
        self.reinforcement_loop = ReinforcementLoop()
        self.profile_engine = ProfileEngine(
            temporal_graph=self.temporal_graph,
            reinforcement_loop=self.reinforcement_loop
        )
        self.injector = LLMContextInjector(
            temporal_graph=self.temporal_graph,
            reinforcement_loop=self.reinforcement_loop
        )
        self._last_result = None
        self._session_id = str(uuid.uuid4())

    def process(self, message: str, modality: str = "text") -> "EmotionResult":
        """
        Process a message. Detect emotion, store it, update profile.
        Returns a context injector ready to pass to any LLM.
        Automatically tracks emotional trajectory between messages.
        """
        result = self.extractor.extract(message, modality=modality)
        self.storage.save(result, self.user_id, session_id=self._session_id)

        # Record individual detection feedback
        record_feedback(
            user_id=self.user_id,
            primary_emotion=result.primary_emotion,
            confidence=result.confidence,
            valence=result.valence,
            arousal=result.arousal,
            dominance=result.dominance,
            corrected_emotion=None,
            feedback_enabled=self.feedback_enabled,
        )

        # Record trajectory — the shift between this message and the last one
        if self._last_result is not None:
            record_trajectory(
                user_id=self.user_id,
                session_id=self._session_id,
                prev_emotion=self._last_result.primary_emotion,
                curr_emotion=result.primary_emotion,
                prev_valence=self._last_result.valence,
                curr_valence=result.valence,
                prev_arousal=self._last_result.arousal,
                curr_arousal=result.arousal,
                prev_dominance=self._last_result.dominance,
                curr_dominance=result.dominance,
                prev_wot=self._last_result.window_of_tolerance,
                curr_wot=result.window_of_tolerance,
                prev_wise_mind=self._last_result.wise_mind_signal or 0.0,
                curr_wise_mind=result.wise_mind_signal or 0.0,
                reappraisal_signal=result.reappraisal_signal or 0.0,
                suppression_signal=result.suppression_signal or 0.0,
                confidence=result.confidence,
                feedback_enabled=self.feedback_enabled,
            )

        self._last_result = result

        try:
            from .dashboard import push_update
            push_update(result)
        except Exception:
            pass

        return result

    def start_panel(self, port: int = 7731, open_browser: bool = True) -> str:
        """
        Start the Resonance panel in your browser.
        Returns the URL. Panel updates live with every process() call.

        Usage:
            r = Resonance(user_id="you")
            r.start_panel()  # opens http://localhost:7731
        """
        from .dashboard import start
        url = start(port=port, open_browser=open_browser)
        print(f"[Resonance] Panel running at {url}")
        return url

    def correct(self, detected: str, corrected: str, result: EmotionResult):
        """
        Record a user correction. Updates the reinforcement loop.
        If feedback is enabled, queues the correction for anonymous sharing.
        """
        record_feedback(
            user_id=self.user_id,
            primary_emotion=detected,
            confidence=result.confidence,
            valence=result.valence,
            arousal=result.arousal,
            dominance=result.dominance,
            corrected_emotion=corrected,
            feedback_enabled=self.feedback_enabled,
        )

    def set_feedback(self, enabled: bool):
        """Change feedback sharing setting at any time."""
        from .config import set_feedback
        set_feedback(enabled)
        self.feedback_enabled = enabled


__all__ = ["Resonance", "EmotionResult", "__version__"]
