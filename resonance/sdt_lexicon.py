"""
Resonance SDT Lexicon
Self-Determination Theory signal detection.
Proprietary -- built from published psychology research.
Commercially clean -- no LIWC, no proprietary dependencies.

Sources:
- Deci & Ryan (1985, 2000) Self-Determination Theory
- Ryan & Deci (2017) Self-Determination and Intrinsic Motivation
- Sheldon et al. (2004) The independent effects of goal contents and motives
- Vansteenkiste et al. (2006) Examining the motivational impact of intrinsic vs extrinsic goal framing

Three core needs:
  Autonomy    -- sense of agency, choice, volition, self-direction
  Competence  -- sense of mastery, skill, effectiveness, capability
  Relatedness -- sense of connection, belonging, being cared for

Scoring:
  Each signal scored [0, 1] -- presence/strength of that need expression
  0.0 = no signal detected
  1.0 = strong signal detected
  Negation-aware: need words preceded by negation flip to low signal
"""

import re

# ---------------------------------------------------------------------------
# AUTONOMY -- agency, choice, volition, self-direction
# Source: Deci & Ryan (2000) -- autonomy = volitional causation of behaviour
# ---------------------------------------------------------------------------
AUTONOMY_POSITIVE = [
    # Choice language
    "i chose", "i choose", "my choice", "i decided", "my decision",
    "i want to", "i wanted to", "i get to", "i am free to",
    "i can", "i will", "up to me", "my own", "on my terms",
    # Agency language
    "i am doing", "i am building", "i am creating", "i am making",
    "i took control", "i took charge", "i am in charge", "i lead",
    "i initiated", "i started", "i launched", "i built", "i created",
    "i designed", "i planned", "i set", "i determined",
    # Self-direction
    "my path", "my way", "my direction", "my journey", "my goals",
    "i am pursuing", "i am following", "i set my own",
    "independent", "independence", "autonomy", "self-directed",
    "on my own", "by myself", "my own terms",
    # Values-aligned action
    "because i believe", "because i value", "because i care",
    "authentic", "authentically", "genuine", "genuinely",
    "true to myself", "being myself",
]

AUTONOMY_NEGATIVE = [
    # Coercion / external pressure
    "i have to", "i had to", "i must", "i am forced", "forced to",
    "no choice", "no option", "no say", "out of my hands",
    "i was told to", "i was made to", "they made me",
    "i am expected to", "i am supposed to", "i should",
    "obligation", "obligated", "required", "mandatory",
    "controlled", "micromanaged", "manipulated",
    "trapped", "stuck", "can not leave", "cannot leave",
    "no freedom", "no autonomy", "powerless",
    "helpless", "at their mercy", "no control",
]

AUTONOMY_PHRASES = [
    "on my own terms", "my own path", "my own way",
    "i get to decide", "i am in control", "i have control",
    "true to myself", "being myself", "my own goals",
]

# ---------------------------------------------------------------------------
# COMPETENCE -- mastery, skill, effectiveness, capability
# Source: Deci & Ryan (2000) -- competence = feeling effective and capable
# ---------------------------------------------------------------------------
COMPETENCE_POSITIVE = [
    # Mastery / skill
    "skilled", "skill", "expert", "expertise", "mastery", "mastered",
    "proficient", "proficiency", "capable", "capability", "competent",
    "good at", "great at", "talented", "talent",
    # Achievement / effectiveness
    "effective", "effectively", "successful", "succeeded", "success",
    "accomplished", "accomplishment", "achieved", "achievement",
    "completed", "finished", "done", "figured out", "solved",
    "nailed it", "crushed it", "pulled it off", "made it work",
    # Growth / learning
    "learning", "learned", "improving", "improved", "getting better",
    "growing", "growth", "developing", "developed", "progress",
    "stronger", "sharper", "smarter", "more capable",
    # Confidence in ability
    "i can do this", "i know how", "i am able", "i am capable",
    "confident", "confidence", "i trust myself",
    "i am good at", "i am great at",
]

COMPETENCE_NEGATIVE = [
    # Incompetence / failure
    "incompetent", "incapable", "unable", "can not do",
    "i failed", "failure", "failing", "i give up", "gave up",
    "i am bad at", "i am terrible at", "i am useless",
    "not good enough", "not capable", "not skilled",
    "i do not know how", "i have no idea how",
    "overwhelmed", "out of my depth", "over my head",
    "i will never", "i cannot", "impossible for me",
    "stupid", "dumb", "idiot", "useless",
    "i keep failing", "i always fail", "i never succeed",
]

COMPETENCE_PHRASES = [
    "i know how to", "i am good at", "i am great at",
    "i can handle", "i can do this", "i figured it out",
    "made it work", "pulled it off", "got it done",
    "i am getting better", "i am improving",
    "getting better at",
    "figured it out",
    "worked it out",
]

# ---------------------------------------------------------------------------
# RELATEDNESS -- connection, belonging, being cared for, caring for others
# Source: Deci & Ryan (2000) -- relatedness = feeling connected and cared for
# ---------------------------------------------------------------------------
RELATEDNESS_POSITIVE = [
    # Connection
    "connected", "connection", "close", "closeness",
    "belong", "belonging", "part of", "included", "inclusion",
    "together", "united", "bond", "bonded", "bonding",
    # Being cared for
    "cared for", "cared about", "loved", "love",
    "supported", "support", "there for me", "showed up",
    "understood", "listened", "heard", "seen", "valued",
    "accepted", "appreciated", "cherished",
    # Caring for others
    "i care about", "i love", "i support", "i am there for",
    "i look after", "i take care of",
    # Social warmth
    "friend", "friends", "friendship", "family",
    "partner", "together with", "with someone",
    "not alone", "someone who", "people who",
    "community", "team", "we", "us", "our",
]

RELATEDNESS_NEGATIVE = [
    # Isolation / loneliness
    "lonely", "loneliness", "alone", "all alone", "by myself",
    "isolated", "isolation", "no one", "nobody",
    "no friends", "no family", "no support",
    # Rejection / exclusion
    "rejected", "rejection", "excluded", "left out", "unwanted",
    "abandoned", "forgotten", "invisible", "ignored",
    "no one cares", "nobody cares", "no one understands",
    "misunderstood", "unheard", "unseen", "unvalued",
    # Disconnection
    "disconnected", "distant", "apart", "separated",
    "cut off", "pushed away", "pushed out",
    "betrayed", "betrayal", "let down", "used",
]

RELATEDNESS_PHRASES = [
    "not alone", "there for me", "showed up for me",
    "feel connected", "feel close", "feel supported",
    "people who care", "someone who understands",
    "part of something", "i belong",
]

# ---------------------------------------------------------------------------
# NEGATION HANDLING (shared with PERMA lexicon approach)
# ---------------------------------------------------------------------------
NEGATION_WINDOW = 3
NEGATION_WORDS = {
    "no", "not", "never", "nothing", "none", "nobody",
    "nowhere", "nor", "neither", "without", "hardly",
    "barely", "scarcely", "cannot", "can't", "don't",
    "doesn't", "didn't", "won't", "wouldn't", "couldn't",
}


def _count_hits(word_list, words):
    """
    Count positive and negated hits for a list of target words/phrases.
    Returns (positive_hits, negated_hits).
    Negated = preceded by a negation word within NEGATION_WINDOW tokens.
    """
    pos_hits = 0
    neg_hits = 0
    for i in range(len(words)):
        for target in word_list:
            target_words = target.split()
            if words[i:i + len(target_words)] == target_words:
                window_start = max(0, i - NEGATION_WINDOW)
                preceding = words[window_start:i]
                if any(n in preceding for n in NEGATION_WORDS):
                    neg_hits += 1
                else:
                    pos_hits += 1
                break
    return pos_hits, neg_hits


def score_sdt(text: str) -> dict:
    """
    Score a text on all 3 SDT need dimensions.
    Returns: {"autonomy": float, "competence": float, "relatedness": float}
    Each score is 0.0 (no signal) to 1.0 (strong signal).
    A score near 0.0 on relatedness with negative words = loneliness signal.

    Design note: SDT scores measure PRESENCE of need expression, not
    satisfaction vs frustration. Use the raw score + context to interpret:
      - autonomy > 0.3  = person is expressing agency and choice
      - autonomy < 0.1 with negative autonomy words = coercion signal
      - relatedness < 0.1 with lonely/isolated words = loneliness signal
    """
    lower = text.lower()
    words = lower.split()
    n = max(len(words), 1)

    def _score_need(positives, negatives, phrases):
        pos_hits, negated_pos = _count_hits(positives, words)
        neg_hits, negated_neg = _count_hits(negatives, words)
        phrase_hits, _ = _count_hits(phrases, words)

        # Positive signal: presence of need-satisfying language
        pos_score = (pos_hits / n) * 8
        # Phrase bonus
        pos_score += phrase_hits * 0.15
        # Negation reduces positive signal
        pos_score -= (negated_pos / n) * 8
        # Negative language (need frustration) pushes score down
        neg_score = (neg_hits / n) * 8

        raw = pos_score - neg_score
        return round(max(0.0, min(1.0, raw)), 4)

    return {
        "autonomy":    _score_need(AUTONOMY_POSITIVE,    AUTONOMY_NEGATIVE,    AUTONOMY_PHRASES),
        "competence":  _score_need(COMPETENCE_POSITIVE,  COMPETENCE_NEGATIVE,  COMPETENCE_PHRASES),
        "relatedness": _score_need(RELATEDNESS_POSITIVE, RELATEDNESS_NEGATIVE, RELATEDNESS_PHRASES),
    }


if __name__ == "__main__":
    tests = [
        ("I chose this path myself and I am building something I truly believe in.",
         {"autonomy": True, "competence": False, "relatedness": False}),
        ("I have no choice in this. I am forced to do what they say.",
         {"autonomy": False, "competence": False, "relatedness": False}),
        ("I finally figured it out. I am getting so much better at this.",
         {"autonomy": False, "competence": True, "relatedness": False}),
        ("I feel completely alone. Nobody cares and I have no one.",
         {"autonomy": False, "competence": False, "relatedness": False}),
        ("My friends really showed up for me. I feel so supported and loved.",
         {"autonomy": False, "competence": False, "relatedness": True}),
    ]

    print("SDT Lexicon Self-Test")
    print("=" * 50)
    for text, expectations in tests:
        scores = score_sdt(text)
        print(f"\nText: {text[:65]}...")
        print(f"Scores: autonomy={scores['autonomy']:.2f}  competence={scores['competence']:.2f}  relatedness={scores['relatedness']:.2f}")
        for need, should_be_high in expectations.items():
            actual_high = scores[need] > 0.1
            status = "PASS" if actual_high == should_be_high else "FAIL"
            print(f"  {status}: {need} expected {'high' if should_be_high else 'low'}, got {scores[need]:.2f}")
