# resonance/reinforcement.py
# Step 9 — Reinforcement Loop
# Stores user corrections, learns personal emotion patterns,
# and adjusts confidence scores based on correction history.

from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from surrealdb import AsyncSurreal
from resonance.extractor import EmotionResult


@dataclass
class Correction:
    """A single user correction — what Resonance said vs what the user actually felt."""
    original_text: str
    detected_emotion: str
    corrected_emotion: str
    detected_valence: float
    detected_arousal: float
    timestamp: str
    session_id: str


@dataclass
class ReinforcementSignal:
    """
    Returned after checking correction history against a new detection.
    Tells the pipeline whether to trust this detection or flag it.
    """
    should_flag: bool           # True if this detection has been wrong before
    confidence_adjustment: float  # Negative number — reduces confidence score
    similar_corrections: int    # How many past corrections match this pattern
    suggested_emotion: Optional[str]  # Most common correction for this pattern


class ReinforcementLoop:
    """
    Manages the correction history and personal learning layer in SurrealDB.
    """

    def __init__(self, db_path: str = "C:/Users/Shadow/Documents/Resonance/resonance/resonance_data/reinforcement"):
        self.db_path = db_path
        self._db: Optional[AsyncSurreal] = None

    async def connect(self):
        self._db = AsyncSurreal(f"file://{self.db_path}")
        await self._db.use("resonance", "reinforcement")

    async def close(self):
        if self._db:
            await self._db.close()

    async def store_correction(
        self,
        original_text: str,
        emotion_result: EmotionResult,
        corrected_emotion: str,
        session_id: str = "default"
    ) -> None:
        """
        Store a user correction.
        Called when the user says the detection was wrong.
        """
        record = {
            "original_text": original_text,
            "detected_emotion": emotion_result.primary_emotion,
            "corrected_emotion": corrected_emotion,
            "detected_valence": emotion_result.valence,
            "detected_arousal": emotion_result.arousal,
            "detected_dominance": emotion_result.dominance,
            "modality": emotion_result.modality,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._db.create("correction", record)

    async def check_detection(
        self,
        emotion_result: EmotionResult,
    ) -> ReinforcementSignal:
        """
        Before finalising a detection, check if this pattern has been
        corrected before. If so, flag it and suggest the correction.
        """
        detected = emotion_result.primary_emotion

        # Get all past corrections where Resonance detected the same emotion
        result = await self._db.query(
            f"SELECT * FROM correction WHERE detected_emotion = '{detected}';"
        )

        corrections = []
        if isinstance(result, list):
            for item in result:
                if isinstance(item, list):
                    corrections.extend(item)
                elif isinstance(item, dict):
                    if "result" in item:
                        r = item["result"]
                        if isinstance(r, list):
                            corrections.extend(r)
                    else:
                        corrections.append(item)

        if not corrections:
            return ReinforcementSignal(
                should_flag=False,
                confidence_adjustment=0.0,
                similar_corrections=0,
                suggested_emotion=None,
            )

        total = len(corrections)

        # Find the most common correction for this detected emotion
        correction_counts = {}
        for c in corrections:
            ce = c.get("corrected_emotion", "unknown")
            correction_counts[ce] = correction_counts.get(ce, 0) + 1

        most_common = max(correction_counts, key=correction_counts.get)
        most_common_count = correction_counts[most_common]

        # Only flag if this pattern has been corrected multiple times
        if total < 2:
            return ReinforcementSignal(
                should_flag=False,
                confidence_adjustment=-0.05 * total,
                similar_corrections=total,
                suggested_emotion=most_common,
            )

        # Confidence adjustment — the more corrections, the lower the confidence
        # Capped at -0.40 so we never zero out confidence entirely
        adjustment = min(-0.10 * total, -0.40)

        return ReinforcementSignal(
            should_flag=True,
            confidence_adjustment=adjustment,
            similar_corrections=total,
            suggested_emotion=most_common,
        )

    async def get_correction_summary(self) -> dict:
        """
        Returns a summary of all corrections stored so far.
        Useful for the dashboard and profile engine later.
        """
        result = await self._db.query("SELECT * FROM correction;")

        corrections = []
        if isinstance(result, list):
            for item in result:
                if isinstance(item, list):
                    corrections.extend(item)
                elif isinstance(item, dict):
                    if "result" in item:
                        r = item["result"]
                        if isinstance(r, list):
                            corrections.extend(r)
                    else:
                        corrections.append(item)

        if not corrections:
            return {
                "total_corrections": 0,
                "most_corrected_emotion": None,
                "correction_pairs": {},
            }

        # Build correction pairs — detected → corrected
        pairs = {}
        for c in corrections:
            detected = c.get("detected_emotion", "unknown")
            corrected = c.get("corrected_emotion", "unknown")
            key = f"{detected} → {corrected}"
            pairs[key] = pairs.get(key, 0) + 1

        # Most corrected emotion
        detected_counts = {}
        for c in corrections:
            d = c.get("detected_emotion", "unknown")
            detected_counts[d] = detected_counts.get(d, 0) + 1
        most_corrected = max(detected_counts, key=detected_counts.get)

        return {
            "total_corrections": len(corrections),
            "most_corrected_emotion": most_corrected,
            "correction_pairs": pairs,
        }