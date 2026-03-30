from pathlib import Path
# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.
# resonance/temporal_graph.py
# Step 8 — Temporal Graph
# Tracks emotional patterns over time across sessions.
# Stores emotion nodes and detects long-term patterns in SurrealDB.

from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from surrealdb import AsyncSurreal
from resonance.extractor import EmotionResult
from resonance.comparison import ComparisonResult


@dataclass
class TemporalPattern:
    """Summary of patterns detected across the graph."""
    total_nodes: int
    dominant_emotion: str
    average_valence: float
    average_arousal: float
    valence_trend: str
    hyperarousal_count: int
    hypoarousal_count: int
    reappraisal_ratio: float
    suppression_ratio: float
    spike_count: int
    wise_mind_ratio: float
    sessions_tracked: int


class TemporalGraph:

    def __init__(self, db_path: str = str(Path.home() / ".resonance" / "temporal")):
        self.db_path = db_path
        self._db: Optional[AsyncSurreal] = None

    async def connect(self):
        self._db = AsyncSurreal(f"file://{self.db_path}")
        await self._db.use("resonance", "temporal")

    async def close(self):
        if self._db:
            await self._db.close()

    async def add_node(
        self,
        emotion: EmotionResult,
        comparison: ComparisonResult,
        session_id: str = "default"
    ) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()

        record = {
            "session_id": session_id,
            "timestamp": timestamp,
            "primary_emotion": emotion.primary_emotion,
            "secondary_emotion": emotion.secondary_emotion,
            "valence": emotion.valence,
            "arousal": emotion.arousal,
            "dominance": emotion.dominance,
            "window_of_tolerance": emotion.window_of_tolerance,
            "wise_mind_signal": emotion.wise_mind_signal,
            "reappraisal_signal": emotion.reappraisal_signal,
            "suppression_signal": emotion.suppression_signal,
            "guilt_type": emotion.guilt_type,
            "alexithymia_flag": emotion.alexithymia_flag,
            "modality": emotion.modality,
            "trajectory": comparison.trajectory,
            "spike_detected": comparison.spike_detected,
            "spike_dimension": comparison.spike_dimension,
            "wot_crossing": comparison.wot_crossing,
            "wot_direction": comparison.wot_direction,
            "valence_delta": comparison.valence_delta,
            "arousal_delta": comparison.arousal_delta,
        }

        result = await self._db.create("emotion_node", record)

        if isinstance(result, list) and len(result) > 0:
            return str(result[0].get("id", "unknown"))
        elif isinstance(result, dict):
            return str(result.get("id", "unknown"))
        return "unknown"

    async def get_patterns(self, limit: int = 100) -> TemporalPattern:
        result = await self._db.query(
            f"SELECT * FROM emotion_node ORDER BY timestamp DESC LIMIT {limit};"
        )

        nodes = []
        if isinstance(result, list):
            for item in result:
                if isinstance(item, list):
                    nodes.extend(item)
                elif isinstance(item, dict):
                    if "result" in item:
                        r = item["result"]
                        if isinstance(r, list):
                            nodes.extend(r)
                    else:
                        nodes.append(item)

        if not nodes:
            return TemporalPattern(
                total_nodes=0,
                dominant_emotion="unknown",
                average_valence=0.0,
                average_arousal=0.0,
                valence_trend="stable",
                hyperarousal_count=0,
                hypoarousal_count=0,
                reappraisal_ratio=0.0,
                suppression_ratio=0.0,
                spike_count=0,
                wise_mind_ratio=0.0,
                sessions_tracked=0,
            )

        total = len(nodes)

        emotion_counts = {}
        for n in nodes:
            e = n.get("primary_emotion", "unknown")
            emotion_counts[e] = emotion_counts.get(e, 0) + 1
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)

        avg_valence = sum(n.get("valence", 0.0) for n in nodes) / total
        avg_arousal = sum(n.get("arousal", 0.0) for n in nodes) / total

        mid = total // 2
        if mid > 0:
            chronological = list(reversed(nodes))
            early_v = sum(n.get("valence", 0.0) for n in chronological[:mid]) / mid
            late_v = sum(n.get("valence", 0.0) for n in chronological[mid:]) / max(total - mid, 1)
            if late_v - early_v >= 0.10:
                valence_trend = "improving"
            elif early_v - late_v >= 0.10:
                valence_trend = "declining"
            else:
                valence_trend = "stable"
        else:
            valence_trend = "stable"

        hyperarousal_count = sum(1 for n in nodes if n.get("window_of_tolerance") == "hyperarousal")
        hypoarousal_count = sum(1 for n in nodes if n.get("window_of_tolerance") == "hypoarousal")
        reappraisal_ratio = sum(1 for n in nodes if n.get("reappraisal_signal")) / total
        suppression_ratio = sum(1 for n in nodes if n.get("suppression_signal")) / total
        spike_count = sum(1 for n in nodes if n.get("spike_detected"))
        wise_mind_ratio = sum(1 for n in nodes if n.get("wise_mind_signal") == "wise_mind") / total
        session_ids = set(n.get("session_id", "default") for n in nodes)

        return TemporalPattern(
            total_nodes=total,
            dominant_emotion=dominant_emotion,
            average_valence=round(avg_valence, 3),
            average_arousal=round(avg_arousal, 3),
            valence_trend=valence_trend,
            hyperarousal_count=hyperarousal_count,
            hypoarousal_count=hypoarousal_count,
            reappraisal_ratio=round(reappraisal_ratio, 3),
            suppression_ratio=round(suppression_ratio, 3),
            spike_count=spike_count,
            wise_mind_ratio=round(wise_mind_ratio, 3),
            sessions_tracked=len(session_ids),
        )
