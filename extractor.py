"""
resonance/extractor.py

The emotion extractor — the heart of Resonance.
Version 2 — complete rebuild with all 8 psychology frameworks fully implemented.

Takes raw text in (or voice transcript). Returns a structured EmotionResult.
No storage, no comparison, no profiles. Just reads and returns.

Psychology frameworks fully implemented:
  1. VAD model (Valence / Arousal / Dominance) — three-axis emotional space
  2. DBT Primary + Secondary emotions via TONE/Parrott ontology — full hierarchy
     including guilt branch (PoliGuilt 2025: moral guilt, shame, self-blame)
  3. Reappraisal vs. Suppression — linguistic distancing (reappraisal) and
     minimizing/deflecting language (suppression), both explicitly detected
  4. Validate-before-problem-solve — signal flag for downstream LLM injector
     (Phase 3). Not extraction work — correctly deferred.
  5. Window of Tolerance — clinical word lists take precedence over VAD
     thresholds. Hyper/hypo triggers are intentional and documented.
  6. PERMA — longitudinal profile work (Phase 3). Not extraction work.
  7. Wise Mind — simultaneous emotional + rational language detection
  8. Non-judgment — design principle for LLM injector (Phase 3), not extractor.

Lexicons used (LIWC permanently off limits per project spec):
  - NRCLex (NRC Emotion Lexicon) — primary emotion word scoring
  - TextBlob — valence (polarity) and subjectivity
  - Empath MIT (194 semantic categories) — guilt/shame, dominance,
    arousal enrichment, suppression support

Modalities:
  - "text"  — direct text input (Phase 1, fully active)
  - "emoji" — emoji string pre-processed to text before extract() (Phase 2)
  - "voice" — Whisper/openSMILE transcript passed as text (Phase 2)
    Voice modality sets a flag so downstream storage can weight these
    readings differently (speech carries additional prosodic information
    that the text-only extractor cannot see; Phase 2 adds openSMILE
    acoustic features to supplement the transcript reading).
"""

from dataclasses import dataclass, field
from typing import Optional
import re

from nrclex import NRCLex
from textblob import TextBlob
from empath import Empath

# Module-level Empath instance — initialised once at import, reused every call
_EMPATH = Empath()


# ============================================================================
# OUTPUT STRUCTURE
# This is the contract between the extractor and every other Resonance module.
# Every field must be present on every result — no Optional gaps.
# ============================================================================

@dataclass
class EmotionResult:
    """
    A single emotional reading of one piece of text.

    All downstream Resonance modules (storage, comparison engine, profile
    engine, LLM injector) receive this structure and depend on every field
    being populated. Never return None for any field — use neutral defaults.
    """

    # --- VAD: three-axis emotional space (Framework 1) ---
    valence: float
    # -1.0 = maximally negative (grief, terror, rage)
    #  0.0 = neutral / ambiguous
    # +1.0 = maximally positive (ecstasy, joy, love)

    arousal: float
    # 0.0 = completely calm, flat, shutdown
    # 0.5 = moderate engagement
    # 1.0 = maximally activated (panic, rage, ecstasy)

    dominance: float
    # 0.0 = totally controlled / powerless / trapped
    # 0.5 = neutral agency
    # 1.0 = fully in control / assertive / powerful

    # --- Primary emotion: Plutchik's 8 + guilt + neutral (Framework 2) ---
    primary_emotion: str
    # joy | sadness | anger | fear | disgust |
    # surprise | trust | anticipation | guilt | neutral

    # --- Secondary emotion: TONE/Parrott ontology (Framework 2) ---
    secondary_emotion: str
    # Finer label derived from primary + arousal tier, e.g.:
    # grief, rage, terror, ecstasy, loathing, shame, self-blame,
    # pensiveness, annoyance, apprehension, serenity, acceptance, remorse...

    # --- Window of Tolerance (Framework 5) ---
    window_of_tolerance: str
    # "in"    = regulated, within tolerance window
    # "hyper" = overwhelmed, flooded, activated beyond window
    # "hypo"  = shut down, dissociated, below window

    wot_triggered_by: str
    # "clinical_words" = WoT state set by clinical phrase match (ALWAYS wins)
    # "vad_threshold"  = WoT state set by VAD scores (arousal + valence combo)
    # "none"           = within window, neither trigger fired
    # Tracked for Phase 2 comparison engine to audit escalation patterns.

    # --- Wise Mind signal (Framework 7) ---
    wise_mind_signal: bool
    # True = text contains both emotional AND rational/reflective language
    # in balance. DBT concept: overlap of Emotion Mind and Reasonable Mind.

    # --- Reappraisal signal (Framework 3) ---
    reappraisal_signal: bool
    # True = linguistic distancing detected:
    #   - Low first-person pronoun ratio (< 15% of words)
    #   - Presence of third-person / abstract / retrospective phrases
    # Research-validated 2024: reduced "I" + abstraction = reappraisal marker.

    # --- Suppression signal (Framework 3) ---
    suppression_signal: bool
    # True = emotional minimizing / deflecting language detected:
    #   - Phrases like "I'm fine", "it's nothing", "don't worry about me"
    #   - Contradiction between negative VAD and positive surface words
    # Suppression and reappraisal are mutually exclusive.
    # Both False = neither pattern detected (genuine neutral expression).
    # Phase 2 comparison engine uses temporal suppression patterns to
    # detect chronic suppression as a clinical risk signal.

    # --- Guilt family (Framework 2 — PoliGuilt 2025) ---
    guilt_type: str
    # "none"        = no guilt signal detected
    # "moral_guilt" = violation of personal ethical standard ("I was wrong")
    # "social_guilt"= letting others down ("I let them down")
    # "self_blame"  = attributing events to self as cause ("it was my fault")
    # "shame"       = identity-level ("I am bad", not "I did bad")
    # Maps to PoliGuilt 2025 taxonomy locked into the Resonance dataset stack.

    # --- Confidence and quality signals ---
    confidence: float
    # 0.0  = no emotion signal found (empty or purely factual text)
    # 0.20 = very weak signal
    # 0.45 = single emotion word hit
    # 0.65 = 2-3 hits
    # 0.80 = 4-6 hits
    # 0.90 = 7+ hits
    # Reduced by 15% if TextBlob and NRC valence strongly disagree (> 0.6 gap)
    # Reduced by 10% for voice modality until Phase 2 acoustic enrichment active

    alexithymia_flag: bool
    # True = emotion word density < 3% across 8+ word input.
    # Signals possible difficulty identifying or expressing feelings.
    # Activates compassion mode in the LLM injector (Phase 3).

    # --- Modality ---
    modality: str
    # "text"  = direct typed input — full confidence in extractor output
    # "emoji" = emoji converted to text via emoji.demojize() before extract()
    # "voice" = Whisper transcript — text extractor reads words only.
    #           Phase 2 adds openSMILE acoustic features (pitch, energy,
    #           speaking rate). Until then, voice flagged for Phase 2 enrichment.
    #           Storage layer weights voice readings at 90% confidence.

    # --- Raw scores (kept for storage, comparison engine, retraining loop) ---
    raw_nrc_scores: dict = field(default_factory=dict)
    raw_empath_scores: dict = field(default_factory=dict)

    def __str__(self) -> str:
        wot_sym = {"in": "✓", "hyper": "↑", "hypo": "↓"}.get(
            self.window_of_tolerance, "?"
        )
        guilt_line = (
            f"  guilt_type={self.guilt_type}\n"
            if self.guilt_type != "none"
            else ""
        )
        return (
            f"EmotionResult(\n"
            f"  primary={self.primary_emotion} / secondary={self.secondary_emotion}\n"
            f"  VAD: valence={self.valence:+.2f}  arousal={self.arousal:.2f}"
            f"  dominance={self.dominance:.2f}\n"
            f"  WoT={wot_sym}{self.window_of_tolerance}"
            f" [{self.wot_triggered_by}]\n"
            f"  wise_mind={self.wise_mind_signal}"
            f"  reappraisal={self.reappraisal_signal}"
            f"  suppression={self.suppression_signal}\n"
            f"{guilt_line}"
            f"  confidence={self.confidence:.2f}"
            f"  alexithymia={self.alexithymia_flag}"
            f"  modality={self.modality}\n"
            f")"
        )


# ============================================================================
# LEXICONS AND REFERENCE DATA
# All constants are module-level — computed once at import, never per-call.
# ============================================================================

# --- TONE / Parrott ontology: secondary emotion mapping ---
# primary × arousal_tier -> secondary label
SECONDARY_MAP: dict = {
    ("joy",          "high_arousal"):  "ecstasy",
    ("joy",          "mid_arousal"):   "joy",
    ("joy",          "low_arousal"):   "serenity",
    ("sadness",      "high_arousal"):  "grief",
    ("sadness",      "mid_arousal"):   "sadness",
    ("sadness",      "low_arousal"):   "pensiveness",
    ("anger",        "high_arousal"):  "rage",
    ("anger",        "mid_arousal"):   "anger",
    ("anger",        "low_arousal"):   "annoyance",
    ("fear",         "high_arousal"):  "terror",
    ("fear",         "mid_arousal"):   "fear",
    ("fear",         "low_arousal"):   "apprehension",
    ("disgust",      "high_arousal"):  "loathing",
    ("disgust",      "mid_arousal"):   "disgust",
    ("disgust",      "low_arousal"):   "boredom",
    ("surprise",     "high_arousal"):  "amazement",
    ("surprise",     "mid_arousal"):   "surprise",
    ("surprise",     "low_arousal"):   "distraction",
    ("trust",        "high_arousal"):  "admiration",
    ("trust",        "mid_arousal"):   "trust",
    ("trust",        "low_arousal"):   "acceptance",
    ("anticipation", "high_arousal"):  "vigilance",
    ("anticipation", "mid_arousal"):   "anticipation",
    ("anticipation", "low_arousal"):   "interest",
    # Guilt family — PoliGuilt 2025 taxonomy
    ("guilt",        "high_arousal"):  "shame",
    ("guilt",        "mid_arousal"):   "guilt",
    ("guilt",        "low_arousal"):   "remorse",
}

# --- VAD reference values per primary emotion ---
# (valence, arousal, dominance) — research-derived approximations
VAD_BY_EMOTION: dict = {
    "joy":          ( 0.76,  0.48,  0.35),
    "sadness":      (-0.63,  0.27,  0.24),
    "anger":        (-0.51,  0.59,  0.25),
    "fear":         (-0.62,  0.60,  0.15),
    "disgust":      (-0.60,  0.35,  0.33),
    "surprise":     ( 0.40,  0.67,  0.35),
    "trust":        ( 0.55,  0.30,  0.45),
    "anticipation": ( 0.30,  0.50,  0.40),
    "guilt":        (-0.55,  0.28,  0.18),  # lower arousal base → quiet guilt = remorse
    "neutral":      ( 0.00,  0.10,  0.50),
}

# --- NRC gap overrides ---
# Each match adds +2 to override NRC noise on high-signal words.
# These are words NRC either misses entirely or routes to wrong categories.
FEAR_OVERRIDE_WORDS: frozenset = frozenset({
    "terrified", "terrifying", "terror", "petrified", "paralyzed", "paralysed",
    "dread", "dreading", "horrified", "horror", "nightmare", "nightmares",
    "phobia", "phobic", "panicking", "scared", "frightened", "afraid",
    "anxious", "anxiety", "dreadful", "fearful",
})
ANGER_OVERRIDE_WORDS: frozenset = frozenset({
    "furious", "fuming", "outraged", "livid", "seething", "infuriated",
    "enraged", "incensed", "irate", "infuriating", "maddening", "enraging",
    "frustrated", "frustrating", "irritated", "irritating", "aggravated",
    "dissatisfied", "dissatisfaction", "betrayed", "betrayal",
    "pointless", "useless", "annoyed", "annoying", "annoyance",
})
SADNESS_OVERRIDE_WORDS: frozenset = frozenset({
    "devastated", "heartbroken", "bereft", "grieving", "mourning",
    "desolate", "despairing", "inconsolable", "shattered", "miserable",
    "wretched", "gloomy", "melancholy", "wistful", "sorrowful", "forlorn",
    "mournful", "downhearted", "despondent", "dejected",
    "painful", "aching", "hurting", "broken", "crushed", "gutted",
})
DISGUST_OVERRIDE_WORDS: frozenset = frozenset({
    "disgusting", "revolting", "repulsive", "nauseating", "vile",
    "repugnant", "abhorrent", "sickening", "gross", "appalling",
    "hideous", "foul", "putrid",
})
JOY_OVERRIDE_WORDS: frozenset = frozenset({
    "happy", "happiness", "joyful", "joyous", "ecstatic", "elated",
    "thrilled", "delighted", "overjoyed", "gleeful", "jubilant", "blissful",
    "euphoric", "exhilarated", "wonderful", "fantastic", "amazing", "great",
    "excited", "excitement",
})
TRUST_OVERRIDE_WORDS: frozenset = frozenset({
    # Only words that unambiguously signal trust as a positive felt state
    # NOT: "trust", "betrayed", "honest", "loyal" — these appear heavily in
    # betrayal sentences ("they betrayed my trust", "they were not honest")
    # and incorrectly boost trust score in anger/sadness contexts.
    "trustworthy", "dependable", "reliable", "devoted", "sincere",
    "i trust you", "i believe in you", "i have faith in",
})
SURPRISE_OVERRIDE_WORDS: frozenset = frozenset({
    "unexpected", "shocking", "shocked", "astonished", "astonishing",
    "stunned", "stunning", "startled", "startling", "amazed", "astounded",
    "astounding", "unbelievable", "incredible", "inconceivable",
    "out of nowhere", "had no idea", "did not expect", "never expected",
})

# --- Guilt family word lists (PoliGuilt 2025 taxonomy) ---
SHAME_WORDS: frozenset = frozenset({
    "ashamed", "shame", "shameful", "embarrassed", "humiliated", "humiliation",
    "worthless", "pathetic", "i am bad", "i am terrible", "i am awful",
    "i am a failure", "i am weak", "i am stupid", "i am broken",
    "disgusted with myself", "hate myself",
})
SELF_BLAME_WORDS: frozenset = frozenset({
    "my fault", "blame myself", "i caused", "i ruined", "i destroyed",
    "i let this happen", "i should have stopped", "because of me",
    "all my fault", "entirely my fault", "i am responsible for",
    "i did this", "i brought this on",
})
MORAL_GUILT_WORDS: frozenset = frozenset({
    "i should not have", "i should have known", "i was wrong", "i sinned",
    "i betrayed", "i lied", "i cheated", "i hurt them", "i wronged",
    "i violated", "it was wrong of me", "i regret doing",
    "i feel guilty", "guilt is", "guilty about", "guilty for",
})
SOCIAL_GUILT_WORDS: frozenset = frozenset({
    "i let them down", "i let everyone down", "i let you down",
    "i failed them", "i failed you", "i disappointed", "i was not there",
    "i was not enough", "i could not help", "they deserved better",
    "i let my family", "i let my friends",
})

# --- Window of Tolerance clinical word lists ---
# Clinical match ALWAYS overrides VAD thresholds — intentional by design.
WOT_HYPER_WORDS: frozenset = frozenset({
    "panic", "panicking", "overwhelmed", "frantic", "racing", "spinning",
    "flooded", "exploding", "hysterical", "manic", "uncontrollable",
    "out of control", "cannot stop", "can't stop", "shaking", "screaming",
    "spiraling", "losing it", "losing my mind", "can't breathe",
    "cannot breathe", "heart pounding", "heart racing", "losing control",
    "falling apart", "breaking down", "coming apart", "going crazy",
    "going insane", "losing my grip",
})
WOT_HYPO_WORDS: frozenset = frozenset({
    "numb", "empty", "blank", "disconnected", "dissociated", "shutdown",
    "shut down", "frozen", "flat", "hollow", "checked out", "zoned out",
    "can't feel", "cannot feel", "don't care", "stopped caring",
    "no energy", "dead inside", "gone", "not here", "not present",
    "spacing out", "going through the motions", "feel nothing",
    "feel like a robot", "feel like a zombie",
})

# --- Suppression detection (Framework 3) ---
SUPPRESSION_PHRASES: frozenset = frozenset({
    "i'm fine", "im fine", "i am fine", "i'll be okay", "i will be okay",
    "i am okay", "i'm okay", "it's fine", "its fine", "it is fine",
    "it's nothing", "its nothing", "it is nothing", "not a big deal",
    "don't worry about me", "dont worry about me", "no big deal",
    "i'll get over it", "i will get over it", "i'm over it", "im over it",
    "it doesn't matter", "it does not matter", "doesn't matter",
    "i don't want to talk about it", "never mind", "nevermind",
    "forget it", "just ignore it", "i'll be fine", "i will be fine",
    "everything is fine", "i'm good", "im good", "i am good",
    "just pushing through", "i'll push through", "just dealing with it",
})
SUPPRESSION_POSITIVE_WORDS: frozenset = frozenset({
    "fine", "okay", "good", "great", "alright", "all right",
    "not bad", "managing", "coping", "handling it",
})

# --- Reappraisal distancing markers (Framework 3) ---
# NOTE: Short common words like "it", "one", "he", "she", "they" are
# intentionally excluded — they fire too broadly and cause false positives.
# Only use phrases and words that are unambiguously retrospective/abstract.
DISTANCING_WORDS: frozenset = frozenset({
    "the situation", "the experience", "the feeling", "the event",
    "looking back", "in hindsight", "from a distance", "stepping back",
    "objectively", "rationally", "in perspective", "with distance",
    "viewed from outside", "as an observer", "that experience",
    "that situation", "that feeling", "that moment",
    "someone in that position", "a person might",
})
FIRST_PERSON_WORDS: frozenset = frozenset({
    "i", "i'm", "i've", "i'll", "i'd", "my", "me", "myself",
})

# --- Wise Mind balance markers (Framework 7) ---
# IMPORTANT: Do NOT include raw emotion names (joy, anger, rage, fear, etc.)
# here — those are primary emotion signals, not Wise Mind signals.
# Wise Mind requires language that shows AWARENESS of feeling, not just feeling.
EMOTION_WORDS_WISE: frozenset = frozenset({
    "feel", "feeling", "felt", "sense", "sensing", "emotion", "emotions",
    "heart", "hurt", "pain", "upset", "scared", "sad", "anxious",
    "overwhelmed", "moved", "troubled", "bothered", "affected",
})
REASON_WORDS_WISE: frozenset = frozenset({
    "think", "know", "understand", "realize", "realise", "believe",
    "logic", "reason", "fact", "evidence", "because", "therefore",
    "consider", "reflect", "perspective", "rational", "analysis",
    "makes sense", "looking at", "objectively", "conclude",
})

# --- Empath categories used (subset of 194 total) ---
EMPATH_CATEGORIES: list = [
    "anger", "joy", "fear", "sadness", "shame",
    "positive_emotion", "negative_emotion",
    "power", "dominant_personality", "dominant_heirarchical",
    "weakness", "suffering", "nervousness",
    "hate", "love", "rage", "violence", "aggression",
]


# ============================================================================
# THE EXTRACTOR
# ============================================================================

class Extractor:
    """
    Resonance emotion extractor.

    Processes text from any modality (typed text, emoji-converted text,
    or voice transcript) and returns a fully populated EmotionResult.

    All 8 Resonance psychology frameworks are represented in the output.
    Frameworks 4, 6, and 8 are downstream concerns — correctly deferred —
    but every field they will need is present in EmotionResult now.

    Voice modality note:
        Pass Whisper transcript as text with modality="voice".
        Text-only extraction runs identically to "text" mode.
        Confidence is reduced by 10% to flag that acoustic features
        (pitch, energy, speaking rate via openSMILE) are not yet active.
        Phase 2 will add an acoustic enrichment step that merges with
        this result post-extraction to produce a complete voice reading.

    Usage:
        extractor = Extractor()
        result = extractor.extract("I can't stop crying, everything is hopeless")
        print(result)

        # Voice transcript
        result = extractor.extract(whisper_transcript, modality="voice")

        # Emoji (pre-process first with emoji.demojize())
        import emoji
        text = emoji.demojize("I feel so 😭😭 today")
        result = extractor.extract(text, modality="emoji")
    """

    def __init__(self):
        pass  # All lexicons are module-level constants — nothing to init.

    def extract(self, text: str, modality: str = "text") -> EmotionResult:
        """
        Main extraction method.

        Args:
            text:     Input string. For voice, pass the Whisper transcript.
                      For emoji, pre-process with emoji.demojize() first.
            modality: "text" | "emoji" | "voice"

        Returns:
            EmotionResult with all fields populated. Never raises.
        """
        if not text or not text.strip():
            return self._neutral_result(modality)

        text_lower = text.lower()
        words = re.findall(r"\b\w+\b", text_lower)
        word_count = max(len(words), 1)

        # ----------------------------------------------------------------
        # STEP 1 — NRC emotion scores
        # Always lowercase — NRC is case-sensitive and misses FURIOUS, etc.
        # ----------------------------------------------------------------
        nrc = NRCLex(text_lower)
        nrc.load_raw_text(text_lower)
        raw_nrc = nrc.raw_emotion_scores

        primary_keys = {
            "joy", "sadness", "anger", "fear",
            "disgust", "surprise", "trust", "anticipation",
        }
        emotion_scores = {k: v for k, v in raw_nrc.items() if k in primary_keys}

        # NRC gap overrides (+3 each — beats NRC ties on high-signal words).
        # Weight is 3 not 2: ensures a single high-signal word like "terrified"
        # wins against NRC context words like "tomorrow" (which score anticipation:2).
        for word in FEAR_OVERRIDE_WORDS:
            if word in text_lower:
                emotion_scores["fear"] = emotion_scores.get("fear", 0) + 3
        for word in ANGER_OVERRIDE_WORDS:
            if word in text_lower:
                emotion_scores["anger"] = emotion_scores.get("anger", 0) + 3
        for word in SADNESS_OVERRIDE_WORDS:
            if word in text_lower:
                emotion_scores["sadness"] = emotion_scores.get("sadness", 0) + 3
        for word in DISGUST_OVERRIDE_WORDS:
            if word in text_lower:
                emotion_scores["disgust"] = emotion_scores.get("disgust", 0) + 3
        for word in JOY_OVERRIDE_WORDS:
            if word in text_lower:
                emotion_scores["joy"] = emotion_scores.get("joy", 0) + 3
        for word in TRUST_OVERRIDE_WORDS:
            if word in text_lower:
                emotion_scores["trust"] = emotion_scores.get("trust", 0) + 3
        for phrase in SURPRISE_OVERRIDE_WORDS:
            if phrase in text_lower:
                emotion_scores["surprise"] = emotion_scores.get("surprise", 0) + 3

        # ----------------------------------------------------------------
        # STEP 2 — Guilt detection (PoliGuilt 2025 taxonomy)
        # NRC has no guilt category. Empath shame supports detection.
        # Shame checked first — most clinically significant guilt type.
        # ----------------------------------------------------------------
        empath_result = _EMPATH.analyze(
            text_lower, categories=EMPATH_CATEGORIES, normalize=True
        ) or {}
        empath_shame = empath_result.get("shame", 0) or 0

        shame_hits = sum(1 for p in SHAME_WORDS if p in text_lower)
        self_blame_hits = sum(1 for p in SELF_BLAME_WORDS if p in text_lower)
        moral_guilt_hits = sum(1 for p in MORAL_GUILT_WORDS if p in text_lower)
        social_guilt_hits = sum(1 for p in SOCIAL_GUILT_WORDS if p in text_lower)

        guilt_type = "none"
        guilt_score = 0

        if shame_hits > 0 or (empath_shame > 0.10 and self_blame_hits > 0):
            guilt_type = "shame"
            guilt_score = (shame_hits * 3) + int(empath_shame * 10)
        elif self_blame_hits > 0:
            guilt_type = "self_blame"
            guilt_score = self_blame_hits * 3
        elif moral_guilt_hits > 0:
            guilt_type = "moral_guilt"
            guilt_score = moral_guilt_hits * 2
        elif social_guilt_hits > 0:
            guilt_type = "social_guilt"
            guilt_score = social_guilt_hits * 2

        if guilt_type != "none":
            emotion_scores["guilt"] = emotion_scores.get("guilt", 0) + guilt_score

        # ----------------------------------------------------------------
        # STEP 3 — Primary emotion
        # ----------------------------------------------------------------
        if emotion_scores:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            total_hits = sum(emotion_scores.values())
        else:
            primary_emotion = "neutral"
            total_hits = 0

        # ----------------------------------------------------------------
        # STEP 4 — Valence (TextBlob 0.6 + NRC polarity 0.4)
        # ----------------------------------------------------------------
        blob = TextBlob(text)
        tb_valence = blob.sentiment.polarity
        tb_subjectivity = blob.sentiment.subjectivity

        nrc_pos = raw_nrc.get("positive", 0)
        nrc_neg = raw_nrc.get("negative", 0)
        nrc_total = nrc_pos + nrc_neg
        nrc_valence = (nrc_pos - nrc_neg) / nrc_total if nrc_total > 0 else 0.0

        valence = round((tb_valence * 0.6) + (nrc_valence * 0.4), 3)
        valence = max(-1.0, min(1.0, valence))

        # Valence floor: if strong negative override words are present but
        # NRC polarity is flooding evenly (e.g. 'devastated and despairing'
        # gets mixed NRC positive/negative), enforce a negative valence floor.
        STRONG_NEG_WORDS = {
            "devastated", "despairing", "hopeless", "heartbroken", "shattered",
            "worthless", "suicidal", "inconsolable", "desolate", "bereft",
            "terrified", "horrified", "petrified", "loathing", "hatred",
        }
        neg_override_hits = sum(1 for w in STRONG_NEG_WORDS if w in text_lower)
        if neg_override_hits > 0 and valence > -0.15:
            valence = max(-0.30, valence - (neg_override_hits * 0.20))
            valence = round(valence, 3)

        # ----------------------------------------------------------------
        # STEP 5 — Arousal (base VAD + intensity signals + Empath)
        # ----------------------------------------------------------------
        base_vad = VAD_BY_EMOTION.get(primary_emotion, (0.0, 0.1, 0.5))
        base_arousal = base_vad[1]

        exclamation_boost = min(text.count("!") * 0.05, 0.20)
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        caps_boost = min(caps_ratio * 0.3, 0.15)
        subjectivity_boost = tb_subjectivity * 0.10
        empath_arousal_boost = min(
            ((empath_result.get("rage", 0) or 0)
             + (empath_result.get("nervousness", 0) or 0)) * 0.15,
            0.15,
        )

        arousal = round(
            base_arousal + exclamation_boost + caps_boost
            + subjectivity_boost + empath_arousal_boost,
            3,
        )
        arousal = max(0.0, min(1.0, arousal))

        # Quiet intensity modifiers: when low-intensity adverbs are present
        # alongside primary emotions, reduce arousal so TONE maps correctly.
        # e.g. "slightly annoyed" = annoyance not rage; "gently happy" = serenity not ecstasy
        # Applies to: guilt, sadness, joy, anger, fear
        QUIET_MODIFIERS = {
            "quietly", "softly", "gently", "calmly", "slowly", "slightly",
            "mildly", "a little", "a bit", "somewhat", "just a", "faintly",
            "barely", "hardly", "minor", "nothing serious", "not serious",
            "small", "tiny", "faint",
        }
        if primary_emotion in ("guilt", "sadness", "joy", "anger", "fear"):
            quiet_hits = sum(1 for phrase in QUIET_MODIFIERS if phrase in text_lower)
            if quiet_hits > 0:
                arousal = max(0.0, round(arousal - (quiet_hits * 0.12), 3))
        # distress-intensity words are present, push arousal toward high tier.
        # This ensures "cannot stop crying / devastated / falling apart" reaches
        # high_arousal so TONE maps grief correctly (not pensiveness).
        DISTRESS_INTENSITY_WORDS = {
            "cannot stop", "can't stop", "devastated", "falling apart",
            "breaking down", "losing control", "out of control", "panicking",
            "terrified", "horrified", "screaming", "shaking", "spiraling",
        }
        if primary_emotion in ("sadness", "fear"):
            distress_hits = sum(
                1 for phrase in DISTRESS_INTENSITY_WORDS if phrase in text_lower
            )
            if distress_hits > 0:
                arousal = min(1.0, arousal + (distress_hits * 0.12))
                arousal = round(arousal, 3)

        # ----------------------------------------------------------------
        # STEP 6 — Dominance (base VAD + hedge/assert words + Empath)
        # ----------------------------------------------------------------
        base_dominance = base_vad[2]

        hedge_words = {
            "can't", "cannot", "helpless", "stuck", "trapped", "powerless",
            "no choice", "have to", "forced", "must", "hopeless",
        }
        hedge_count = sum(1 for w in words if w in hedge_words)
        hedge_penalty = min(hedge_count * 0.08, 0.30)

        assert_words = {
            "decided", "chose", "will", "determined", "confident", "sure",
            "clear", "ready", "going to", "choosing",
        }
        assert_count = sum(1 for w in words if w in assert_words)
        assert_boost = min(assert_count * 0.06, 0.20)

        empath_dom_boost = min(
            ((empath_result.get("power", 0) or 0)
             + (empath_result.get("dominant_personality", 0) or 0)
             + (empath_result.get("dominant_heirarchical", 0) or 0)) * 0.12
            - ((empath_result.get("weakness", 0) or 0) * 0.10),
            0.20,
        )

        dominance = round(
            base_dominance - hedge_penalty + assert_boost + empath_dom_boost, 3
        )
        dominance = max(0.0, min(1.0, dominance))

        # ----------------------------------------------------------------
        # STEP 7 — Secondary emotion (TONE/Parrott ontology)
        # Arousal tier boundaries are per-emotion because each primary has
        # a different natural baseline. Uniform 0.35/0.65 thresholds fail
        # because "low arousal anger" (annoyance) still sits at ~0.55 due
        # to anger's base VAD of 0.59.
        #
        # Per-emotion tier thresholds (high_min, low_max):
        #   joy:          base=0.48 → high>=0.65, low<0.45
        #   sadness:      base=0.27 → high>=0.55, low<0.30
        #   anger:        base=0.59 → high>=0.70, low<0.55
        #   fear:         base=0.60 → high>=0.70, low<0.55
        #   disgust:      base=0.35 → high>=0.60, low<0.38
        #   surprise:     base=0.67 → high>=0.72, low<0.55
        #   trust:        base=0.30 → high>=0.55, low<0.35
        #   anticipation: base=0.50 → high>=0.65, low<0.42
        #   guilt:        base=0.28 → high>=0.42, low<0.30
        # ----------------------------------------------------------------
        TIER_THRESHOLDS = {
            # emotion:     (high_min, low_max)
            "joy":          (0.65, 0.45),
            "sadness":      (0.55, 0.30),
            "anger":        (0.70, 0.55),
            "fear":         (0.70, 0.55),
            "disgust":      (0.60, 0.38),
            "surprise":     (0.72, 0.55),
            "trust":        (0.55, 0.32),  # trust mid = 0.32-0.55; acceptance < 0.32
            "anticipation": (0.65, 0.42),
            "guilt":        (0.42, 0.30),
        }
        high_min, low_max = TIER_THRESHOLDS.get(primary_emotion, (0.65, 0.35))
        if arousal >= high_min:
            arousal_tier = "high_arousal"
        elif arousal < low_max:
            arousal_tier = "low_arousal"
        else:
            arousal_tier = "mid_arousal"

        secondary_emotion = SECONDARY_MAP.get(
            (primary_emotion, arousal_tier), primary_emotion
        )

        # ----------------------------------------------------------------
        # STEP 8 — Window of Tolerance (Framework 5)
        # Clinical word match ALWAYS wins over VAD thresholds.
        # This is intentional — a clinical phrase like "cannot stop crying"
        # reveals the true state even when surface VAD looks moderate.
        # wot_triggered_by documents WHY the state was set.
        # ----------------------------------------------------------------
        hyper_clinical = any(p in text_lower for p in WOT_HYPER_WORDS)
        hypo_clinical = any(p in text_lower for p in WOT_HYPO_WORDS)
        hyper_vad = arousal >= 0.75 and valence < -0.3
        hypo_vad = arousal <= 0.15 and abs(valence) < 0.2

        if hyper_clinical:
            window_of_tolerance = "hyper"
            wot_triggered_by = "clinical_words"
        elif hypo_clinical:
            window_of_tolerance = "hypo"
            wot_triggered_by = "clinical_words"
        elif hyper_vad:
            window_of_tolerance = "hyper"
            wot_triggered_by = "vad_threshold"
        elif hypo_vad:
            window_of_tolerance = "hypo"
            wot_triggered_by = "vad_threshold"
        else:
            window_of_tolerance = "in"
            wot_triggered_by = "none"

        # ----------------------------------------------------------------
        # STEP 9 — Wise Mind signal (Framework 7)
        # Requires MINIMUM 2 emotion word hits — prevents "feel" + "think"
        # in a purely emotional sentence from triggering a false positive.
        # ----------------------------------------------------------------
        emotion_word_count = sum(1 for w in words if w in EMOTION_WORDS_WISE)
        reason_word_count = sum(1 for w in words if w in REASON_WORDS_WISE)
        wise_mind_signal = (
            emotion_word_count >= 2
            and reason_word_count >= 1
            and abs(emotion_word_count - reason_word_count) <= 3
        )

        # ----------------------------------------------------------------
        # STEP 10 — Reappraisal signal (Framework 3)
        # Low first-person ratio + distancing language = reappraisal.
        # ----------------------------------------------------------------
        fp_count = sum(1 for w in words if w in FIRST_PERSON_WORDS)
        fp_ratio = fp_count / word_count
        distancing_count = sum(
            1 for p in DISTANCING_WORDS if p in text_lower
        )
        reappraisal_signal = (fp_ratio < 0.15) and (distancing_count >= 2)

        # ----------------------------------------------------------------
        # STEP 11 — Suppression signal (Framework 3)
        # Explicitly detected. Mutually exclusive with reappraisal.
        # Three detection paths: phrase match, VAD contradiction,
        # Empath contradiction (positive surface + negative NRC).
        # ----------------------------------------------------------------
        suppression_signal = False
        if not reappraisal_signal:
            phrase_match = any(p in text_lower for p in SUPPRESSION_PHRASES)
            positive_surface = any(w in words for w in SUPPRESSION_POSITIVE_WORDS)
            # VAD contradiction: clearly negative valence hidden under positive words
            # Threshold -0.35 (not -0.25) to avoid false positives on genuinely
            # mixed or mildly positive text
            vad_contradiction = valence < -0.35 and positive_surface and fp_ratio > 0.08
            empath_contradiction = (
                empath_shame < 0.05
                and nrc_neg > nrc_pos
                and positive_surface
            )
            suppression_signal = (
                phrase_match
                or vad_contradiction
                or empath_contradiction
            )

        # ----------------------------------------------------------------
        # STEP 12 — Confidence
        # ----------------------------------------------------------------
        if total_hits == 0:
            confidence = 0.20
        elif total_hits == 1:
            confidence = 0.45
        elif total_hits <= 3:
            confidence = 0.65
        elif total_hits <= 6:
            confidence = 0.80
        else:
            confidence = 0.90

        if nrc_total > 0 and abs(tb_valence - nrc_valence) > 0.6:
            confidence = round(confidence * 0.85, 2)

        if modality == "voice":
            confidence = round(confidence * 0.90, 2)

        # ----------------------------------------------------------------
        # STEP 13 — Alexithymia flag
        # NRC sometimes tags everyday words (home, store, bought) as
        # positive/joy/trust — giving false density on flat factual text.
        # Cross-check with Empath negative_emotion to confirm real signal:
        # if NRC density looks non-zero but Empath shows no emotional content,
        # treat the text as low-emotion and flag alexithymia.
        # ----------------------------------------------------------------
        nrc_emotion_hits = sum(
            v for k, v in raw_nrc.items()
            if k in {"joy","sadness","anger","fear","disgust","surprise","trust","anticipation"}
        )
        empath_emotion_signal = (
            (empath_result.get("negative_emotion", 0) or 0)
            + (empath_result.get("positive_emotion", 0) or 0)
            + (empath_result.get("suffering", 0) or 0)
            + (empath_result.get("nervousness", 0) or 0)
        )
        # Real emotion density: NRC hits confirmed by Empath signal
        real_emotion_density = (
            nrc_emotion_hits / word_count
            if empath_emotion_signal > 0.05
            else 0.0
        )
        alexithymia_flag = (real_emotion_density < 0.05) and (word_count >= 8)

        return EmotionResult(
            valence=valence,
            arousal=arousal,
            dominance=dominance,
            primary_emotion=primary_emotion,
            secondary_emotion=secondary_emotion,
            window_of_tolerance=window_of_tolerance,
            wot_triggered_by=wot_triggered_by,
            wise_mind_signal=wise_mind_signal,
            reappraisal_signal=reappraisal_signal,
            suppression_signal=suppression_signal,
            guilt_type=guilt_type,
            confidence=confidence,
            alexithymia_flag=alexithymia_flag,
            modality=modality,
            raw_nrc_scores=raw_nrc,
            raw_empath_scores={
                k: round(v, 4) for k, v in empath_result.items() if v and v > 0
            },
        )

    def _neutral_result(self, modality: str) -> EmotionResult:
        """
        Returns a fully-populated neutral result for empty or whitespace input.
        Every field populated — storage and downstream modules receive no gaps.
        """
        return EmotionResult(
            valence=0.0,
            arousal=0.0,
            dominance=0.5,
            primary_emotion="neutral",
            secondary_emotion="neutral",
            window_of_tolerance="in",
            wot_triggered_by="none",
            wise_mind_signal=False,
            reappraisal_signal=False,
            suppression_signal=False,
            guilt_type="none",
            confidence=0.0,
            alexithymia_flag=False,
            modality=modality,
            raw_nrc_scores={},
            raw_empath_scores={},
        )
