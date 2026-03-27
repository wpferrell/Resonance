# resonance/dashboard.py
# Phase 4 — Dashboard
# Lightweight Flask server that reads live emotional data
# from Qdrant and SurrealDB and serves the Resonance panel.

import asyncio
import threading
from flask import Flask, render_template, jsonify
from resonance.temporal_graph import TemporalGraph
from resonance.reinforcement import ReinforcementLoop
from resonance.profile import ProfileEngine

app = Flask(__name__)

graph = TemporalGraph()
loop = ReinforcementLoop()
engine = ProfileEngine(graph, loop)

def run_async(coro):
    """Run an async coroutine from a sync Flask route."""
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    try:
        return new_loop.run_until_complete(coro)
    finally:
        new_loop.close()

async def get_dashboard_data():
    await graph.connect()
    await loop.connect()

    profile = await engine.build_profile(limit=200)
    summary = engine.summarise(profile)
    patterns = await graph.get_patterns(limit=1)
    corrections = await loop.get_correction_summary()

    await graph.close()
    await loop.close()

    # Map dominant emotion to pill state
    emotion_map = {
        "joy":        {"word": "happy",      "color": "#68d391", "emoji": "😊", "short": "Lighter today."},
        "anger":      {"word": "angry",       "color": "#fc8181", "emoji": "😡", "short": "Something's been crossed."},
        "fear":       {"word": "anxious",     "color": "#f6ad55", "emoji": "😟", "short": "On edge right now."},
        "sadness":    {"word": "sad",         "color": "#a0aec0", "emoji": "😔", "short": "Something's weighing on you."},
        "surprise":   {"word": "surprised",   "color": "#f6ad55", "emoji": "😮", "short": "Didn't see that coming."},
        "disgust":    {"word": "frustrated",  "color": "#fc8181", "emoji": "😤", "short": "Something feels wrong."},
        "neutral":    {"word": "okay",        "color": "#4fd1c5", "emoji": "🙂", "short": "Getting by."},
        "anxiety":    {"word": "anxious",     "color": "#f6ad55", "emoji": "😟", "short": "Mind won't stop."},
        "frustration":{"word": "frustrated",  "color": "#fc8181", "emoji": "😤", "short": "Blocked. Can't move forward."},
        "calm":       {"word": "calm",        "color": "#4fd1c5", "emoji": "😌", "short": "Settled. Steady."},
        "happiness":  {"word": "happy",       "color": "#68d391", "emoji": "😊", "short": "Lighter today."},
        "loneliness": {"word": "lonely",      "color": "#85b7eb", "emoji": "😪", "short": "Missing connection."},
    }

    dominant = profile.emotional_tendency.lower()
    pill = emotion_map.get(dominant, {
        "word": dominant,
        "color": "#4fd1c5",
        "emoji": "🙂",
        "short": "Here with you."
    })

    # Mood and energy from VAD
    mood_pct = int((profile.baseline_valence + 1) / 2 * 100)
    energy_pct = int(profile.baseline_arousal * 100)

    mood_word = "very low" if mood_pct < 20 else "low" if mood_pct < 40 else "moderate" if mood_pct < 60 else "good" if mood_pct < 80 else "very high"
    energy_word = "very low" if energy_pct < 20 else "low" if energy_pct < 40 else "moderate" if energy_pct < 60 else "high" if energy_pct < 80 else "very high"

    mood_color = "#fc8181" if mood_pct < 35 else "#f6ad55" if mood_pct < 55 else "#4fd1c5" if mood_pct < 75 else "#68d391"
    energy_color = "#a0aec0" if energy_pct < 35 else "#f6ad55" if energy_pct < 65 else "#fc8181"

    # Senses reflection
    senses_map = {
        "improving":  "Something is shifting. The weight is lifting slowly.",
        "declining":  "Things feel harder than they did. Something is building.",
        "volatile":   "Up and down. Hard to find solid ground right now.",
        "stable":     "Holding steady. Whatever this is, it's consistent.",
    }
    senses_text = senses_map.get(profile.current_trend, "Here with you in whatever this is.")

    # Correction chips — 4 most relevant alternatives
    chip_map = {
        "happy":      [{"e":"😊","n":"happy","d":True},{"e":"😌","n":"calm"},{"e":"😁","n":"excited"},{"e":"🙂","n":"just okay"}],
        "angry":      [{"e":"😡","n":"angry","d":True},{"e":"😤","n":"frustrated"},{"e":"🥺","n":"hurt underneath"},{"e":"😒","n":"irritated"}],
        "anxious":    [{"e":"😟","n":"worried","d":True},{"e":"😰","n":"overwhelmed"},{"e":"😓","n":"stressed"},{"e":"😬","n":"uneasy"}],
        "sad":        [{"e":"😔","n":"sad","d":True},{"e":"😶","n":"empty"},{"e":"🥺","n":"hurt"},{"e":"😑","n":"done"}],
        "neutral":    [{"e":"🙂","n":"okay","d":True},{"e":"😌","n":"calm"},{"e":"😐","n":"numb"},{"e":"😔","n":"a little down"}],
        "calm":       [{"e":"😌","n":"calm","d":True},{"e":"😐","n":"numb"},{"e":"😬","n":"uneasy"},{"e":"🙂","n":"just okay"}],
    }
    chips = chip_map.get(dominant, [
        {"e":"🙂","n":dominant,"d":True},
        {"e":"😌","n":"calm"},
        {"e":"😔","n":"sad"},
        {"e":"😟","n":"anxious"}
    ])

    return {
        "pill": pill,
        "mood": {"pct": mood_pct, "word": mood_word, "color": mood_color},
        "energy": {"pct": energy_pct, "word": energy_word, "color": energy_color},
        "senses": senses_text,
        "chips": chips,
        "profile": {
            "total_nodes": profile.total_nodes,
            "sessions": profile.sessions_tracked,
            "confidence": profile.profile_confidence,
            "corrections": profile.total_corrections,
        }
    }


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/state")
def state():
    try:
        data = run_async(get_dashboard_data())
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run():
    print("\n✅ Resonance dashboard running at http://localhost:5050\n")
    app.run(port=5050, debug=False, use_reloader=False)


if __name__ == "__main__":
    run()