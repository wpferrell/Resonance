# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.
"""
resonance/storage.py

The storage layer -- saves every EmotionResult to both databases.

Qdrant    -- stores the emotion as a vector for similarity search.
SurrealDB -- stores full records, current state snapshot, and graph.

Both embedded -- no server, no Docker, no external process.
Data lives in resonance_data/ inside your project folder.

v2: P3 fields added -- PERMA, SDT, wot_trajectory, scored floats for
    wise_mind/reappraisal/suppression. All new fields are optional with
    defaults so existing stored records are not broken.
"""

import asyncio
import atexit
from datetime import datetime, timezone
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from surrealdb import AsyncSurreal

from .extractor import EmotionResult

DATA_DIR = Path(__file__).parent / "resonance_data"
QDRANT_PATH = str(DATA_DIR / "qdrant")
SURREAL_PATH = str(DATA_DIR / "surreal.db").replace("\\", "/")

EMOTION_LABELS = [
    "joy", "sadness", "anger", "fear",
    "disgust", "surprise", "trust", "anticipation", "guilt",
]
VECTOR_DIM = 12


def _build_vector(result: EmotionResult) -> list:
    emotion_vec = [0.0] * len(EMOTION_LABELS)
    if result.primary_emotion in EMOTION_LABELS:
        idx = EMOTION_LABELS.index(result.primary_emotion)
        emotion_vec[idx] = result.arousal * result.confidence
    return [result.valence, result.arousal, result.dominance, *emotion_vec]


def _result_to_payload(result, user_id, session_id, topic, timestamp):
    """Build full payload from EmotionResult. Handles both current and P3 fields."""
    payload = {
        # Core identity
        "user_id": user_id,
        "session_id": session_id,
        "topic": topic,
        "timestamp": timestamp,
        # Original 19 EmotionResult fields
        "valence": result.valence,
        "arousal": result.arousal,
        "dominance": result.dominance,
        "primary_emotion": result.primary_emotion,
        "secondary_emotion": result.secondary_emotion,
        "window_of_tolerance": result.window_of_tolerance,
        "wot_triggered_by": result.wot_triggered_by,
        "wise_mind_signal": result.wise_mind_signal,
        "reappraisal_signal": result.reappraisal_signal,
        "suppression_signal": result.suppression_signal,
        "guilt_type": result.guilt_type,
        "confidence": result.confidence,
        "alexithymia_flag": result.alexithymia_flag,
        "modality": result.modality,
        "crisis_detected": result.crisis_detected,
        "sustained_distress": result.sustained_distress,
        "outward_reflection": result.outward_reflection,
        # P3 fields -- added as optional, default None/0.0
        # PERMA wellbeing (5 dimensions, scored floats [-1, 1])
        "perma_p": getattr(result, "perma_p", None),
        "perma_e": getattr(result, "perma_e", None),
        "perma_r": getattr(result, "perma_r", None),
        "perma_m": getattr(result, "perma_m", None),
        "perma_a": getattr(result, "perma_a", None),
        # SDT (3 dimensions, scored floats [0, 1])
        "autonomy_signal": getattr(result, "autonomy_signal", None),
        "competence_signal": getattr(result, "competence_signal", None),
        "relatedness_signal": getattr(result, "relatedness_signal", None),
        # WoT session trajectory
        "wot_trajectory": getattr(result, "wot_trajectory", None),
        # Scored floats (P3 converts these from booleans)
        "wise_mind_score": getattr(result, "wise_mind_score", None),
        "reappraisal_score": getattr(result, "reappraisal_score", None),
        "suppression_score": getattr(result, "suppression_score", None),
        # Session-level trajectory
        "session_trajectory": getattr(result, "session_trajectory", None),
    }
    # Remove None values to keep records clean (SurrealDB handles missing fields)
    return {k: v for k, v in payload.items() if v is not None}


class Storage:

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._qdrant = QdrantClient(path=QDRANT_PATH)
        self._ensure_collection()
        self._loop = asyncio.new_event_loop()
        self._db = None
        self._loop.run_until_complete(self._init_surreal())
        atexit.register(self._close)

    def _close(self):
        try:
            self._qdrant.close()
        except Exception:
            pass

    def __del__(self):
        pass

    def _ensure_collection(self):
        existing = [c.name for c in self._qdrant.get_collections().collections]
        if "resonance_emotions" not in existing:
            self._qdrant.create_collection(
                collection_name="resonance_emotions",
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            )

    async def _init_surreal(self):
        self._db = AsyncSurreal(f"file://{SURREAL_PATH}")
        await self._db.connect()
        await self._db.use("resonance", "resonance")

    def save(self, result: EmotionResult, user_id: str, session_id: str, topic: str = "general") -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        return self._loop.run_until_complete(
            self._save_async(result, user_id, session_id, topic, timestamp)
        )

    async def _save_async(self, result, user_id, session_id, topic, timestamp):
        vector = _build_vector(result)
        payload = _result_to_payload(result, user_id, session_id, topic, timestamp)

        point_id = int(datetime.now(timezone.utc).timestamp() * 1_000_000) % (2**53)
        self._qdrant.upsert(
            collection_name="resonance_emotions",
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )

        db_record = dict(payload)
        db_record["qdrant_id"] = point_id

        record = await self._db.create("emotion", db_record)
        record_id = record[0]["id"] if isinstance(record, list) else record["id"]

        # Current state snapshot -- always has latest values per user
        current_state = {
            "user_id": user_id,
            "last_updated": timestamp,
            "valence": result.valence,
            "arousal": result.arousal,
            "dominance": result.dominance,
            "primary_emotion": result.primary_emotion,
            "secondary_emotion": result.secondary_emotion,
            "window_of_tolerance": result.window_of_tolerance,
            "wise_mind_signal": result.wise_mind_signal,
            "reappraisal_signal": result.reappraisal_signal,
            "suppression_signal": result.suppression_signal,
            "guilt_type": result.guilt_type,
            "alexithymia_flag": result.alexithymia_flag,
            "modality": result.modality,
            "confidence": result.confidence,
            "crisis_detected": result.crisis_detected,
            "sustained_distress": result.sustained_distress,
            # P3 fields in current state snapshot
            "perma_p": getattr(result, "perma_p", None),
            "perma_e": getattr(result, "perma_e", None),
            "perma_r": getattr(result, "perma_r", None),
            "perma_m": getattr(result, "perma_m", None),
            "perma_a": getattr(result, "perma_a", None),
            "autonomy_signal": getattr(result, "autonomy_signal", None),
            "competence_signal": getattr(result, "competence_signal", None),
            "relatedness_signal": getattr(result, "relatedness_signal", None),
            "wot_trajectory": getattr(result, "wot_trajectory", None),
            "wise_mind_score": getattr(result, "wise_mind_score", None),
            "reappraisal_score": getattr(result, "reappraisal_score", None),
            "suppression_score": getattr(result, "suppression_score", None),
            "session_trajectory": getattr(result, "session_trajectory", None),
        }
        # Remove Nones
        current_state = {k: v for k, v in current_state.items() if v is not None}

        await self._db.upsert(f"current_state:{user_id}", current_state)

        return str(record_id)

    def get_current_state(self, user_id: str) -> dict:
        return self._loop.run_until_complete(self._get_state_async(user_id))

    async def _get_state_async(self, user_id):
        result = await self._db.select(f"current_state:{user_id}")
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return result if result else {}

    def get_recent(self, user_id: str, limit: int = 10) -> list:
        return self._loop.run_until_complete(self._get_recent_async(user_id, limit))

    async def _get_recent_async(self, user_id, limit):
        result = await self._db.query(
            "SELECT * FROM emotion WHERE user_id = $uid ORDER BY timestamp DESC LIMIT $lim",
            {"uid": user_id, "lim": limit},
        )
        if not result:
            return []
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            return result
        return []

    def close(self):
        self._loop.run_until_complete(self._db.close())
        self._qdrant.close()
        self._loop.close()
