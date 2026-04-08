# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.
# Resonance — extractor.py
# v3 — ethics safeguards: crisis_detected, sustained_distress, outward_reflection

import os
import json
import re
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from nrclex import NRCLex
from textblob import TextBlob
from empath import Empath
from resonance.perma_lexicon import score_perma

MODEL_PATH = Path.home() / ".resonance" / "model_cache"
if not MODEL_PATH.exists():
    _local = Path(__file__).parent / "model"
    if _local.exists():
        MODEL_PATH = _local

ENSEMBLE_THRESHOLD = 0.65

CRISIS_PHRASES = [
    "want to die", "want to kill myself", "kill myself", "end my life",
    "ending my life", "end it all", "suicide", "suicidal",
    "don't want to be here", "don't want to live", "no reason to live",
    "can't go on", "can't do this anymore", "rather be dead",
    "hurting myself", "hurt myself", "cutting myself", "self harm",
    "self-harm", "overdose", "nothing to live for", "better off dead",
    "better off without me", "no point in living", "wish i was dead",
    "wish i were dead",
]

DISTRESS_VALENCE_THRESHOLD  = -0.40
DISTRESS_AROUSAL_THRESHOLD  = 0.55
SUSTAINED_DISTRESS_COUNT    = 3

OUTWARD_VALENCE_THRESHOLD   = -0.30
OUTWARD_SESSION_COUNT       = 5

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
    crisis_detected: bool = False
    sustained_distress: bool = False
    outward_reflection: bool = False
    perma_p: float = 0.0
    perma_e: float = 0.0
    perma_r: float = 0.0
    perma_m: float = 0.0
    perma_a: float = 0.0

    def __str__(self):
        wot_flag = "✓in" if self.window_of_tolerance == "in" else "⚠OUT"
        crisis_flag = " 🚨CRISIS" if self.crisis_detected else ""
        distress_flag = " ⚠DISTRESS" if self.sustained_distress else ""
        return (
            f"EmotionResult(\n"
            f"  primary={self.primary_emotion} / secondary={self.secondary_emotion}{crisis_flag}{distress_flag}\n"
            f"  VAD: valence={self.valence:+.2f}  arousal={self.arousal:.2f}  dominance={self.dominance:.2f}\n"
            f"  WoT={wot_flag} [{self.wot_triggered_by}]\n"
            f"  wise_mind={self.wise_mind_signal}  reappraisal={self.reappraisal_signal}  suppression={self.suppression_signal}\n"
            f"  confidence={self.confidence:.2f}  alexithymia={self.alexithymia_flag}  modality={self.modality}\n"
            f"  crisis={self.crisis_detected}  sustained_distress={self.sustained_distress}  outward_reflection={self.outward_reflection}\n"
            f"  PERMA: P={self.perma_p:+.2f}  E={self.perma_e:+.2f}  R={self.perma_r:+.2f}  M={self.perma_m:+.2f}  A={self.perma_a:+.2f}\n"
            f")"
        )

    def to_prompt(self) -> str:
        """
        Returns a plain-English emotional context string ready to inject
        into any LLM system prompt. This is the core developer API.

        Usage:
            context = r.process("I've been so anxious about this")
            llm.chat(system=context.to_prompt(), message=message)
        """
        lines = []
        lines.append("[Resonance Emotional Context]")
        lines.append(f"Current emotion: {self.primary_emotion} (confidence: {self.confidence:.0%})")
        if self.secondary_emotion and self.secondary_emotion != self.primary_emotion:
            lines.append(f"Underlying emotion: {self.secondary_emotion}")
        lines.append(f"Mood (valence): {self.valence:+.2f}  Energy (arousal): {self.arousal:.2f}  Agency (dominance): {self.dominance:.2f}")
        lines.append(f"Window of Tolerance: {self.window_of_tolerance}")
        if self.wise_mind_signal:
            lines.append("Wise mind signal detected — person is balanced and grounded.")
        if self.reappraisal_signal:
            lines.append("Reappraisal detected — person is healthily reframing their emotion.")
        if self.suppression_signal:
            lines.append("Suppression detected — person may be holding back feelings.")
        if self.guilt_type:
            lines.append(f"Guilt type detected: {self.guilt_type}")
        if self.alexithymia_flag:
            lines.append("Low emotional vocabulary detected — person may struggle to name feelings directly.")
        if self.crisis_detected:
            lines.append("CRISIS DETECTED — surface appropriate support immediately.")
        if self.sustained_distress:
            lines.append("Sustained distress pattern detected — prioritise validation and care.")
        if self.perma_p < -0.3:
            lines.append(f"Positive emotion low (P={self.perma_p:+.2f}) - person may be struggling emotionally.")
        if self.perma_r < -0.3:
            lines.append(f"Loneliness or disconnection detected (R={self.perma_r:+.2f}) - prioritise warmth and connection.")
        if self.perma_m < -0.3:
            lines.append(f"Low sense of meaning or purpose (M={self.perma_m:+.2f}) - avoid hollow reassurance.")
        if self.perma_p > 0.3:
            lines.append(f"Positive emotion high (P={self.perma_p:+.2f}) - person is in a good place emotionally.")
        if self.perma_e > 0.3:
            lines.append(f"High engagement or flow detected (E={self.perma_e:+.2f}) - person is absorbed and motivated.")
        if self.perma_r > 0.3:
            lines.append(f"Strong connection or belonging signal (R={self.perma_r:+.2f}).")
        if self.perma_m > 0.3:
            lines.append(f"Strong sense of meaning or purpose (M={self.perma_m:+.2f}).")
        if self.perma_a > 0.3:
            lines.append(f"Accomplishment signal detected (A={self.perma_a:+.2f}) - acknowledge their effort or success.")
        lines.append("")
        lines.append("Respond to how this person actually feels, not just what they said.")
        lines.append("Validate before problem-solving. Never jump straight to fixing.")
        if self.window_of_tolerance == "hyperarousal":
            lines.append("Use calm, slow language — this person is overwhelmed.")
        elif self.window_of_tolerance == "hypoarousal":
            lines.append("Use warm, gently activating language — this person is withdrawn.")
        return "\n".join(lines)

VAD = {
    "joy":      (0.88, 0.60, 0.75),
    "anger":    (-0.60, 0.85, 0.65),
    "fear":     (-0.70, 0.80, 0.20),
    "sadness":  (-0.75, 0.25, 0.20),
    "surprise": (0.20, 0.75, 0.40),
    "shame":    (-0.65, 0.45, 0.15),
    "neutral":  (0.00, 0.20, 0.50),
}

NRC_TO_CLASS = {
    "anger":        "anger",
    "fear":         "fear",
    "joy":          "joy",
    "sadness":      "sadness",
    "surprise":     "surprise",
    "disgust":      "anger",
    "trust":        "joy",
    "anticipation": "neutral",
}

SECONDARY_MAP = {
    "joy":      ["contentment", "happiness", "pride", "optimism", "enthusiasm", "hope", "relief", "love", "affection", "longing"],
    "anger":    ["frustration", "irritability", "rage", "disgust", "envy", "contempt", "aggression"],
    "fear":     ["anxiety", "worry", "nervousness", "panic", "dread", "apprehension"],
    "sadness":  ["grief", "disappointment", "loneliness", "helplessness", "hopelessness", "regret", "guilt"],
    "surprise": ["amazement", "confusion", "awe", "disbelief"],
    "shame":    ["embarrassment", "humiliation", "remorse", "self-blame", "moral_guilt", "social_guilt"],
    "neutral":  ["neutral"],
}

GUILT_KEYWORDS = {
    "shame":       ["ashamed", "shameful", "humiliated", "disgrace", "embarrassed"],
    "self-blame":  ["my fault", "i failed", "i should have", "i didn't", "blame myself"],
    "moral_guilt": ["wrong", "shouldn't have", "regret", "i hurt", "i caused"],
    "social_guilt":["let down", "disappointed", "failed them", "i owe", "i neglected"],
}

DISTANCING_WORDS = ["one", "people", "they", "someone", "person", "you", "we", "it"]
FIRST_PERSON     = ["i", "me", "my", "myself", "i'm", "i've", "i'll", "i'd"]
NEGATIVE_AFFECT  = ["hate", "angry", "sad", "depressed", "anxious", "scared", "hurt", "upset", "crying", "pain"]

HYPER_WORDS = ["furious", "terrified", "panicking", "overwhelmed", "exploding", "screaming", "raging", "frantic", "desperate"]
HYPO_WORDS  = ["numb", "empty", "shutdown", "frozen", "disconnected", "blank", "nothing", "void", "dissociated"]

WISE_MIND_PHRASES = ["i understand", "i see both", "on one hand", "on the other hand", "makes sense", "i accept", "even though", "and yet", "both"]

EMOJI_MAP = {
    "😊": "joy", "😂": "joy", "❤️": "joy", "😍": "joy", "🥰": "joy",
    "😢": "sadness", "😭": "sadness", "💔": "sadness",
    "😡": "anger", "🤬": "anger", "😤": "anger",
    "😨": "fear", "😰": "fear", "😱": "fear",
    "😮": "surprise", "😲": "surprise",
    "😳": "shame", "🫣": "shame",
    "😐": "neutral", "🙂": "neutral",
}

class Extractor:
    def __init__(self):
        self.empath = Empath()
        self._confidence_profile = {}
        self._load_confidence_profile()
        self._load_model()

    def _load_confidence_profile(self):
        profile_path = MODEL_PATH / "confidence_profile.json"
        if profile_path.exists():
            try:
                with open(profile_path) as f:
                    self._confidence_profile = json.load(f)
            except Exception:
                self._confidence_profile = {}

    def _get_confidence_floor(self, emotion: str) -> float:
        if emotion in self._confidence_profile:
            return self._confidence_profile[emotion].get("confidence_floor", ENSEMBLE_THRESHOLD)
        return ENSEMBLE_THRESHOLD

    def _load_model(self):
        self._model = None
        self._tokenizer = None
        self._label_map = None
        try:
            label_map_path = MODEL_PATH / "label_map.json"
            if not label_map_path.exists():
                return
            with open(label_map_path) as f:
                self._label_map = {int(k): v for k, v in json.load(f).items()}
            import io
            from contextlib import redirect_stderr
            self._tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
            with redirect_stderr(io.StringIO()):
                self._model = AutoModelForSequenceClassification.from_pretrained(
                    str(MODEL_PATH), local_files_only=True
                )
            self._model.eval()
            if torch.cuda.is_available():
                self._model = self._model.cuda()
        except Exception:
            self._model = None

    def _predict_model(self, text: str):
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

    def _predict_nrc(self, nrc: dict):
        scores = {e: 0.0 for e in VAD}
        for nrc_emotion, score in nrc.items():
            mapped = NRC_TO_CLASS.get(nrc_emotion)
            if mapped and score > 0:
                scores[mapped] += score
        best = max(scores, key=scores.get)
        best_score = scores[best]
        if best_score == 0:
            return "neutral", 0.30
        return best, min(0.60, best_score / 5.0)

    def _predict_ensemble(self, text: str, nrc: dict):
        if self._model is None:
            return self._predict_nrc(nrc)
        model_emotion, model_conf = self._predict_model(text)
        floor = self._get_confidence_floor(model_emotion)
        if model_conf >= floor:
            return model_emotion, model_conf
        nrc_emotion, nrc_conf = self._predict_nrc(nrc)
        model_weight = model_conf / floor
        nrc_weight   = 1.0 - model_weight
        if model_emotion == nrc_emotion:
            blended_conf = (model_conf * model_weight) + (nrc_conf * nrc_weight)
            return model_emotion, round(blended_conf, 4)
        if (model_conf * model_weight) >= (nrc_conf * nrc_weight):
            return model_emotion, round(model_conf * model_weight, 4)
        else:
            return nrc_emotion, round(nrc_conf * nrc_weight, 4)

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
        fp   = sum(1 for w in words if w in FIRST_PERSON)
        dist = sum(1 for w in words if w in DISTANCING_WORDS)
        return dist > fp and len(words) > 5

    def _detect_suppression(self, text: str):
        words = text.lower().split()
        fp  = sum(1 for w in words if w in FIRST_PERSON)
        neg = sum(1 for w in words if w in NEGATIVE_AFFECT)
        return fp >= 2 and neg >= 1

    def _detect_wot(self, valence: float, arousal: float, text: str):
        lower = text.lower()
        has_hyper_word = any(w in lower for w in HYPER_WORDS)
        has_hypo_word  = any(w in lower for w in HYPO_WORDS)
        if has_hyper_word and arousal > 0.82:
            return "hyperarousal", "hyperarousal_words"
        if has_hypo_word or (valence < -0.60 and arousal < 0.25):
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

    def _detect_crisis(self, text: str) -> bool:
        lower = text.lower()
        return any(phrase in lower for phrase in CRISIS_PHRASES)

    def _detect_sustained_distress(self, history: List["EmotionResult"]) -> bool:
        if len(history) < SUSTAINED_DISTRESS_COUNT:
            return False
        recent = history[-SUSTAINED_DISTRESS_COUNT:]
        return all(
            r.valence <= DISTRESS_VALENCE_THRESHOLD and
            r.arousal >= DISTRESS_AROUSAL_THRESHOLD
            for r in recent
        )

    def _detect_outward_reflection(self, history: List["EmotionResult"]) -> bool:
        if len(history) < OUTWARD_SESSION_COUNT:
            return False
        recent = history[-OUTWARD_SESSION_COUNT:]
        return all(r.valence <= OUTWARD_VALENCE_THRESHOLD for r in recent)

    def extract(
        self,
        text: str,
        modality: str = "text",
        history: Optional[List["EmotionResult"]] = None
    ) -> "EmotionResult":
        if history is None:
            history = []

        if not text or not text.strip():
            return EmotionResult(modality=modality)

        nrc_obj = NRCLex(text)
        nrc_obj.load_raw_text(text)
        nrc    = nrc_obj.affect_frequencies
        empath = self.empath.analyze(text, normalize=True) or {}

        emoji_emotion = self._detect_emoji_emotion(text)
        if emoji_emotion:
            primary    = emoji_emotion
            confidence = 0.90
        else:
            primary, confidence = self._predict_ensemble(text, nrc)

        valence, arousal, dominance = VAD.get(primary, (0.0, 0.2, 0.5))
        blob_polarity = TextBlob(text).sentiment.polarity
        valence = (valence + blob_polarity) / 2

        secondary        = self._get_secondary(primary, text)
        wot, wot_trigger = self._detect_wot(valence, arousal, text)
        wise_mind        = self._detect_wise_mind(text)
        reappraisal      = self._detect_reappraisal(text)
        suppression      = self._detect_suppression(text)
        guilt_type       = self._detect_guilt(text)
        alexithymia      = self._detect_alexithymia(nrc, text)
        crisis           = self._detect_crisis(text)
        sustained        = self._detect_sustained_distress(history)
        outward          = self._detect_outward_reflection(history)
        perma            = score_perma(text)

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
            crisis_detected=crisis,
            sustained_distress=sustained,
            outward_reflection=outward,
            perma_p=round(perma["P"], 4),
            perma_e=round(perma["E"], 4),
            perma_r=round(perma["R"], 4),
            perma_m=round(perma["M"], 4),
            perma_a=round(perma["A"], 4),
        )
