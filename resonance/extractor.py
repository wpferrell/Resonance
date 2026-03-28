# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.
# Resonance — extractor.py
# Step 5C: Upgraded with trained ModernBERT emotion model (92% accuracy)
# All 8 psychology frameworks preserved. Same interface as before.

import os
import json
import re
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from nrclex import NRCLex
from textblob import TextBlob
from empath import Empath

# ── Model path ─────────────────────────────────────────────────
MODEL_PATH = Path(__file__).parent / "resonance" / "model"
if not MODEL_PATH.exists():
    MODEL_PATH = Path(__file__).parent / "model"

# ── EmotionResult ──────────────────────────────────────────────
@dataclass
class EmotionResult:
    valence: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.0
    primary_emotion: str = "neutral"
    secondary_emotion: str = "neutral"
    window_of_tolerance: str = "in"
    wot_triggered_by: str = "none"
    wise_mind_signal: bool = False
    reappraisal_signal: bool = False
    suppression_signal: bool = False
    guilt_type: Optional[str] = None
    confidence: float = 0.0
    alexithymia_flag: bool = False
    modality: str = "text"
    raw_nrc_scores: dict = field(default_factory=dict)
    raw_empath_scores: dict = field(default_factory=dict)

    def __str__(self):
        wot_flag = "✓in" if self.window_of_tolerance == "in" else "⚠OUT"
        return (
            f"EmotionResult(\n"
            f"  primary={self.primary_emotion} / secondary={self.secondary_emotion}\n"
            f"  VAD: valence={self.valence:+.2f}  arousal={self.arousal:.2f}  dominance={self.dominance:.2f}\n"
            f"  WoT={wot_flag} [{self.wot_triggered_by}]\n"
            f"  wise_mind={self.wise_mind_signal}  reappraisal={self.reappraisal_signal}  suppression={self.suppression_signal}\n"
            f"  confidence={self.confidence:.2f}  alexithymia={self.alexithymia_flag}  modality={self.modality}\n"
            f")"
        )

# ── VAD lookup ─────────────────────────────────────────────────
VAD = {
    "joy":      (0.88, 0.60, 0.75),
    "anger":    (-0.60, 0.85, 0.65),
    "fear":     (-0.70, 0.80, 0.20),
    "sadness":  (-0.75, 0.25, 0.20),
    "surprise": (0.20, 0.75, 0.40),
    "shame":    (-0.65, 0.45, 0.15),
    "neutral":  (0.00, 0.20, 0.50),
}

# ── Secondary emotion map (TONE/Parrott ontology) ──────────────
SECONDARY_MAP = {
    "joy":      ["contentment", "happiness", "pride", "optimism", "enthusiasm", "hope", "relief", "love", "affection", "longing"],
    "anger":    ["frustration", "irritability", "rage", "disgust", "envy", "contempt", "aggression"],
    "fear":     ["anxiety", "worry", "nervousness", "panic", "dread", "apprehension"],
    "sadness":  ["grief", "disappointment", "loneliness", "helplessness", "hopelessness", "regret", "guilt"],
    "surprise": ["amazement", "confusion", "awe", "disbelief"],
    "shame":    ["embarrassment", "humiliation", "remorse", "self-blame", "moral_guilt", "social_guilt"],
    "neutral":  ["neutral"],
}

# ── Guilt keywords (PoliGuilt 2025) ───────────────────────────
GUILT_KEYWORDS = {
    "shame":       ["ashamed", "shameful", "humiliated", "disgrace", "embarrassed"],
    "self-blame":  ["my fault", "i failed", "i should have", "i didn't", "blame myself"],
    "moral_guilt": ["wrong", "shouldn't have", "regret", "i hurt", "i caused"],
    "social_guilt":["let down", "disappointed", "failed them", "i owe", "i neglected"],
}

# ── Reappraisal / suppression markers ─────────────────────────
DISTANCING_WORDS = ["one", "people", "they", "someone", "person", "you", "we", "it"]
FIRST_PERSON     = ["i", "me", "my", "myself", "i'm", "i've", "i'll", "i'd"]
NEGATIVE_AFFECT  = ["hate", "angry", "sad", "depressed", "anxious", "scared", "hurt", "upset", "crying", "pain"]

# ── WoT clinical word lists ────────────────────────────────────
HYPER_WORDS = ["furious", "terrified", "panicking", "overwhelmed", "exploding", "screaming", "raging", "frantic", "desperate"]
HYPO_WORDS  = ["numb", "empty", "shutdown", "frozen", "disconnected", "blank", "nothing", "void", "dissociated"]

# ── Wise mind markers ─────────────────────────────────────────
WISE_MIND_PHRASES = ["i understand", "i see both", "on one hand", "on the other hand", "makes sense", "i accept", "even though", "and yet", "both"]

# ── Emoji map ─────────────────────────────────────────────────
EMOJI_MAP = {
    "😊": "joy", "😂": "joy", "❤️": "joy", "😍": "joy", "🥰": "joy",
    "😢": "sadness", "😭": "sadness", "💔": "sadness",
    "😡": "anger", "🤬": "anger", "😤": "anger",
    "😨": "fear", "😰": "fear", "😱": "fear",
    "😮": "surprise", "😲": "surprise",
    "😳": "shame", "🫣": "shame",
    "😐": "neutral", "🙂": "neutral",
}

# ── Extractor class ────────────────────────────────────────────
class Extractor:
    def __init__(self):
        self.empath = Empath()
        self._load_model()

    def _load_model(self):
        """Load trained ModernBERT model if available."""
        self._model = None
        self._tokenizer = None
        self._label_map = None

        try:
            label_map_path = MODEL_PATH / "label_map.json"
            if not label_map_path.exists():
                print("[Resonance] No trained model found — using rule-based fallback.")
                return

            with open(label_map_path) as f:
                self._label_map = {int(k): v for k, v in json.load(f).items()}

            self._tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
            self._model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_PATH))
            self._model.eval()

            if torch.cuda.is_available():
                self._model = self._model.cuda()

            print(f"[Resonance] Trained model loaded from {MODEL_PATH}")
            print(f"[Resonance] Classes: {list(self._label_map.values())}")
            print(f"[Resonance] Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")

        except Exception as e:
            print(f"[Resonance] Model load failed ({e}) — using rule-based fallback.")
            self._model = None

    def _predict_model(self, text: str):
        """Run trained model inference. Returns (emotion, confidence)."""
        inputs = self._tokenizer(
            text, return_tensors="pt", truncation=True,
            max_length=128, padding=True
        )
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            logits = self._model(**inputs).logits
            probs  = torch.softmax(logits, dim=1)[0]
            idx    = int(probs.argmax())

        return self._label_map[idx], float(probs[idx])

    def _predict_rules(self, text: str, nrc: dict):
        """Rule-based fallback when model is unavailable."""
        scores = {e: 0.0 for e in VAD}
        for emotion, score in nrc.items():
            if emotion in scores:
                scores[emotion] += score
        best = max(scores, key=scores.get)
        return best, min(0.5, scores[best] / 5.0) if scores[best] > 0 else ("neutral", 0.3)

    def _detect_emoji_emotion(self, text: str):
        for emoji, emotion in EMOJI_MAP.items():
            if emoji in text:
                return emotion
        return None

    def _get_secondary(self, primary: str, text: str):
        candidates = SECONDARY_MAP.get(primary, ["neutral"])
        lower = text.lower()
        for candidate in candidates:
            if candidate.replace("_", " ") in lower:
                return candidate
        return candidates[0]

    def _detect_guilt(self, text: str):
        lower = text.lower()
        for guilt_type, keywords in GUILT_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                return guilt_type
        return None

    def _detect_reappraisal(self, text: str):
        words = text.lower().split()
        fp = sum(1 for w in words if w in FIRST_PERSON)
        dist = sum(1 for w in words if w in DISTANCING_WORDS)
        return dist > fp and len(words) > 5

    def _detect_suppression(self, text: str):
        words = text.lower().split()
        fp = sum(1 for w in words if w in FIRST_PERSON)
        neg = sum(1 for w in words if w in NEGATIVE_AFFECT)
        return fp >= 2 and neg >= 1

    def _detect_wot(self, valence: float, arousal: float, text: str):
        lower = text.lower()
        if any(w in lower for w in HYPER_WORDS) or arousal > 0.80:
            return "hyperarousal", "hyperarousal_words"
        if any(w in lower for w in HYPO_WORDS) or (valence < -0.60 and arousal < 0.25):
            return "hypoarousal", "hypoarousal_words"
        return "in", "none"

    def _detect_wise_mind(self, text: str):
        lower = text.lower()
        return any(phrase in lower for phrase in WISE_MIND_PHRASES)

    def _detect_alexithymia(self, nrc: dict, text: str):
        emotion_word_count = sum(1 for v in nrc.values() if v > 0)
        words = text.split()
        density = emotion_word_count / max(len(words), 1)
        return density < 0.02 and len(words) > 10

    def extract(self, text: str, modality: str = "text") -> EmotionResult:
        if not text or not text.strip():
            return EmotionResult(modality=modality)

        # ── NRC and Empath scores ──────────────────────────────
        nrc_obj = NRCLex(text); nrc_obj.load_raw_text(text)
        nrc     = nrc_obj.affect_frequencies
        empath  = self.empath.analyze(text, normalize=True) or {}

        # ── Primary emotion ────────────────────────────────────
        emoji_emotion = self._detect_emoji_emotion(text)

        if emoji_emotion:
            primary    = emoji_emotion
            confidence = 0.90
        elif self._model is not None:
            primary, confidence = self._predict_model(text)
        else:
            primary, confidence = self._predict_rules(text, nrc)

        # ── VAD ────────────────────────────────────────────────
        valence, arousal, dominance = VAD.get(primary, (0.0, 0.2, 0.5))

        # ── TextBlob valence refinement ────────────────────────
        blob_polarity = TextBlob(text).sentiment.polarity
        valence = (valence + blob_polarity) / 2

        # ── Secondary emotion ──────────────────────────────────
        secondary = self._get_secondary(primary, text)

        # ── Psychology frameworks ──────────────────────────────
        wot, wot_trigger     = self._detect_wot(valence, arousal, text)
        wise_mind            = self._detect_wise_mind(text)
        reappraisal          = self._detect_reappraisal(text)
        suppression          = self._detect_suppression(text)
        guilt_type           = self._detect_guilt(text)
        alexithymia          = self._detect_alexithymia(nrc, text)

        return EmotionResult(
            valence=round(valence, 4),
            arousal=round(arousal, 4),
            dominance=round(dominance, 4),
            primary_emotion=primary,
            secondary_emotion=secondary,
            window_of_tolerance=wot,
            wot_triggered_by=wot_trigger,
            wise_mind_signal=wise_mind,
            reappraisal_signal=reappraisal,
            suppression_signal=suppression,
            guilt_type=guilt_type,
            confidence=round(confidence, 4),
            alexithymia_flag=alexithymia,
            modality=modality,
            raw_nrc_scores=dict(nrc),
            raw_empath_scores={k: v for k, v in empath.items() if v and v > 0},
        )

