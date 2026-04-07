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
        # Connect async components
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._connect_async())
            else:
                loop.run_until_complete(self._connect_async())
        except Exception:
            pass

    async def _connect_async(self):
        """Connect TemporalGraph and ReinforcementLoop databases."""
        try:
            await self.temporal_graph.connect()
        except Exception:
            pass
        try:
            await self.reinforcement_loop.connect()
        except Exception:
            pass

    def process(self, message: str, modality: str = "text") -> "EmotionResult":
        """
        Process a message. Detect emotion, store it, update profile.
        Returns an EmotionResult with to_prompt() ready to pass to any LLM.

        Usage:
            context = r.process("I've been so anxious about this")
            llm.chat(system=context.to_prompt(), message=message)
        """
        result = self.extractor.extract(message, modality=modality)
        self.storage.save(result, self.user_id, session_id=self._session_id)

        # Record individual detection feedback -- includes P3 fields if present
        record_feedback(
            user_id=self.user_id,
            primary_emotion=result.primary_emotion,
            confidence=result.confidence,
            valence=result.valence,
            arousal=result.arousal,
            dominance=result.dominance,
            corrected_emotion=None,
            feedback_enabled=self.feedback_enabled,
            perma_p=getattr(result, "perma_p", None),
            perma_e=getattr(result, "perma_e", None),
            perma_r=getattr(result, "perma_r", None),
            perma_m=getattr(result, "perma_m", None),
            perma_a=getattr(result, "perma_a", None),
            autonomy_signal=getattr(result, "autonomy_signal", None),
            competence_signal=getattr(result, "competence_signal", None),
            relatedness_signal=getattr(result, "relatedness_signal", None),
            wise_mind_score=getattr(result, "wise_mind_score", None),
            reappraisal_score=getattr(result, "reappraisal_score", None),
            suppression_score=getattr(result, "suppression_score", None),
            wot_trajectory=getattr(result, "wot_trajectory", None),
            crisis_detected=result.crisis_detected,
            sustained_distress=result.sustained_distress,
        )

        # Record trajectory — the shift between this message and the last one
        if self._last_result is not None:
            # Use scored floats if available (P3+), fall back to boolean cast for current model
            _prev_wm = getattr(self._last_result, "wise_mind_score", None)
            if _prev_wm is None:
                _prev_wm = float(self._last_result.wise_mind_signal) if self._last_result.wise_mind_signal else 0.0
            _curr_wm = getattr(result, "wise_mind_score", None)
            if _curr_wm is None:
                _curr_wm = float(result.wise_mind_signal) if result.wise_mind_signal else 0.0
            _curr_reap = getattr(result, "reappraisal_score", None)
            if _curr_reap is None:
                _curr_reap = float(result.reappraisal_signal) if result.reappraisal_signal else 0.0
            _curr_supp = getattr(result, "suppression_score", None)
            if _curr_supp is None:
                _curr_supp = float(result.suppression_signal) if result.suppression_signal else 0.0

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
                prev_wise_mind=_prev_wm,
                curr_wise_mind=_curr_wm,
                reappraisal_signal=_curr_reap,
                suppression_signal=_curr_supp,
                confidence=result.confidence,
                feedback_enabled=self.feedback_enabled,
                wot_trajectory=getattr(result, "wot_trajectory", None),
                suppression_score=getattr(result, "suppression_score", None),
                reappraisal_score=getattr(result, "reappraisal_score", None),
                wise_mind_score=getattr(result, "wise_mind_score", None),
                session_trajectory=getattr(result, "session_trajectory", None),
                perma_p=getattr(result, "perma_p", None),
                perma_e=getattr(result, "perma_e", None),
                perma_r=getattr(result, "perma_r", None),
                perma_m=getattr(result, "perma_m", None),
                perma_a=getattr(result, "perma_a", None),
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
