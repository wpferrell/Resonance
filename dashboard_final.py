# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 - see LICENSE for details.
# resonance/dashboard.py
# Live panel server - serves the Resonance panel with real-time updates.

import asyncio
import threading
import webbrowser
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO

# Silence all server logs
for _n in ['werkzeug', 'engineio', 'socketio', 'flask']:
    logging.getLogger(_n).setLevel(logging.CRITICAL)

_TEMPLATE_DIR = str(Path(__file__).parent / 'templates')
_app = Flask(__name__, template_folder=_TEMPLATE_DIR)
_app.config['SECRET_KEY'] = 'resonance-panel'
_socketio = SocketIO(_app, cors_allowed_origins="*", async_mode='threading', logger=False, engineio_logger=False)

_latest_result = None
_server_thread = None
_port = 7731


def _get_dashboard_data_sync():
    emotion_map = {
        "joy":      {"word": "happy",     "color": "#68d391", "emoji": "😊", "short": "Lighter today."},
        "anger":    {"word": "angry",     "color": "#fc8181", "emoji": "😡", "short": "Something's been crossed."},
        "fear":     {"word": "anxious",   "color": "#f6ad55", "emoji": "😟", "short": "On edge right now."},
        "sadness":  {"word": "sad",       "color": "#a0aec0", "emoji": "😔", "short": "Something's weighing on you."},
        "surprise": {"word": "surprised", "color": "#f6ad55", "emoji": "😮", "short": "Didn't see that coming."},
        "shame":    {"word": "ashamed",   "color": "#ed93b1", "emoji": "😳", "short": "Something feels wrong inside."},
        "neutral":  {"word": "okay",      "color": "#4fd1c5", "emoji": "🙂", "short": "Getting by."},
    }

    dominant = _latest_result.primary_emotion if _latest_result else "neutral"
    pill = emotion_map.get(dominant, {"word": dominant, "color": "#4fd1c5", "emoji": "🙂", "short": "Here with you."})

    mood_pct = int((_latest_result.valence + 1) / 2 * 100) if _latest_result else 50
    energy_pct = int(_latest_result.arousal * 100) if _latest_result else 30

    mood_word = "very low" if mood_pct < 20 else "low" if mood_pct < 40 else "moderate" if mood_pct < 60 else "good" if mood_pct < 80 else "very high"
    energy_word = "very low" if energy_pct < 20 else "low" if energy_pct < 40 else "moderate" if energy_pct < 60 else "high" if energy_pct < 80 else "very high"
    mood_color = "#fc8181" if mood_pct < 35 else "#f6ad55" if mood_pct < 55 else "#4fd1c5" if mood_pct < 75 else "#68d391"
    energy_color = "#a0aec0" if energy_pct < 35 else "#f6ad55" if energy_pct < 65 else "#fc8181"

    senses_map = {
        "improving": "Something is shifting. The weight is lifting slowly.",
        "declining":  "Things feel harder than they did. Something is building.",
        "volatile":   "Up and down. Hard to find solid ground right now.",
        "stable":     "Holding steady. Whatever this is, it is consistent.",
    }
    senses_text = senses_map.get("stable", "Here with you in whatever this is.")

    chip_map = {
        "happy":    [{"e":"😊","n":"happy","d":True},{"e":"😌","n":"calm"},{"e":"😁","n":"excited"},{"e":"🙂","n":"just okay"}],
        "angry":    [{"e":"😡","n":"angry","d":True},{"e":"😤","n":"frustrated"},{"e":"🥺","n":"hurt underneath"},{"e":"😒","n":"irritated"}],
        "fear":     [{"e":"😟","n":"worried","d":True},{"e":"😰","n":"overwhelmed"},{"e":"😓","n":"stressed"},{"e":"😬","n":"uneasy"}],
        "sadness":  [{"e":"😔","n":"sad","d":True},{"e":"😶","n":"empty"},{"e":"🥺","n":"hurt"},{"e":"😑","n":"done"}],
        "neutral":  [{"e":"🙂","n":"okay","d":True},{"e":"😌","n":"calm"},{"e":"😐","n":"numb"},{"e":"😔","n":"a little down"}],
        "shame":    [{"e":"😳","n":"ashamed","d":True},{"e":"🫣","n":"embarrassed"},{"e":"😞","n":"guilty"},{"e":"😔","n":"regretful"}],
        "anger":    [{"e":"😡","n":"angry","d":True},{"e":"😤","n":"frustrated"},{"e":"😒","n":"irritated"},{"e":"😠","n":"upset"}],
        "surprise": [{"e":"😮","n":"surprised","d":True},{"e":"😕","n":"confused"},{"e":"😲","n":"shocked"},{"e":"🤔","n":"unsure"}],
        "joy":      [{"e":"😊","n":"happy","d":True},{"e":"😁","n":"excited"},{"e":"😌","n":"calm"},{"e":"🙂","n":"content"}],
    }
    chips = chip_map.get(dominant, [
        {"e":"🙂","n":dominant,"d":True},
        {"e":"😌","n":"calm"},
        {"e":"😔","n":"sad"},
        {"e":"😟","n":"anxious"}
    ])

    live = {}
    if _latest_result:
        live = {
            "emotion": _latest_result.primary_emotion,
            "confidence": round(_latest_result.confidence * 100),
        }

    return {
        "pill": pill,
        "mood": {"pct": mood_pct, "word": mood_word, "color": mood_color},
        "energy": {"pct": energy_pct, "word": energy_word, "color": energy_color},
        "senses": senses_text,
        "chips": chips,
        "live": live,
    }


@_app.route("/")
def index():
    return render_template("dashboard.html")


@_app.route("/api/state")
def state():
    try:
        data = _get_dashboard_data_sync()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@_socketio.on('connect')
def on_connect():
    pass


def push_update(result):
    global _latest_result
    _latest_result = result
    try:
        _socketio.emit('update', {
            "emotion": result.primary_emotion,
            "secondary": result.secondary_emotion,
            "confidence": round(result.confidence * 100),
            "valence": round(result.valence, 2),
            "arousal": round(result.arousal, 2),
            "wot": result.window_of_tolerance,
            "wise_mind": result.wise_mind_signal,
        })
    except Exception:
        pass


def start(port=7731, open_browser=True):
    global _server_thread, _port
    _port = port

    def _run():
        from werkzeug.serving import make_server
        srv = make_server('127.0.0.1', port, _app)
        srv.serve_forever()

    _server_thread = threading.Thread(target=_run, daemon=True)
    _server_thread.start()

    import time
    time.sleep(1.5)

    if open_browser:
        webbrowser.open(f"http://localhost:{port}")

    return f"http://localhost:{port}"
