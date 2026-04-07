"""
Resonance PERMA Lexicon
Proprietary â€” built from published psychology research.
Commercially clean â€” no LIWC, no proprietary dependencies.

Sources:
- Fredrickson (2001) Broaden-and-Build Theory / ten positive emotions
- Csikszentmihalyi (1990) Flow: six characteristics
- Steger et al. (2006) Meaning in Life Questionnaire (MLQ)
- Bandura (1997) Self-Efficacy / mastery experiences
- Butler & Kern (2016) PERMA-Profiler
- Schwartz et al. (2016) Predicting Wellbeing from Social Media Language
- Seligman (2011) Flourish

Scoring:
  Each message scored per dimension: -1.0 (strong negative) to +1.0 (strong positive)
  Level 1: word presence (normalize by message length)
  Level 2: phrase patterns
  Level 3: structural signals (pronouns, tense, syntax)
"""

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# P â€” POSITIVE EMOTION
# Joy, Gratitude, Contentment, Hope, Pride, Love, Awe, Serenity
# Source: Fredrickson (2001) ten positive emotions + PERMA-Profiler (Butler & Kern 2016)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
P_POSITIVE = [
    # Joy / Happiness
    "happy", "happiness", "joyful", "joy", "delight", "delighted", "elated", "elation",
    "thrilled", "ecstatic", "blissful", "cheerful", "gleeful", "jubilant", "merry",
    "overjoyed", "radiant", "lighthearted", "buoyant",
    # Gratitude
    "grateful", "gratitude", "thankful", "thankfulness", "appreciative", "appreciate",
    "appreciation", "blessed", "fortunate", "lucky", "count my blessings",
    # Contentment / Serenity
    "content", "contentment", "satisfied", "satisfaction", "peaceful", "peace",
    "calm", "tranquil", "serene", "serenity", "at ease", "relaxed", "settled",
    "comfortable", "cozy", "safe",
    # Hope / Optimism
    "hopeful", "hope", "optimistic", "optimism", "excited", "excitement", "looking forward",
    "anticipate", "anticipation", "eager", "eagerness", "can't wait", "positive",
    "bright side", "things will get better", "it'll be okay", "things are looking up",
    # Pride
    "proud", "pride", "accomplished", "achievement", "achieved", "did it", "made it",
    "pulled it off", "succeeded", "success",
    # Love / Affection
    "love", "loving", "loved", "adore", "adoration", "affection", "affectionate",
    "cherish", "treasure", "warmth", "warm", "tender", "care", "caring",
    # Awe / Inspiration
    "awe", "awed", "awesome", "amazed", "amazement", "wonder", "wonderful",
    "inspired", "inspiration", "moved", "breathtaking", "incredible", "magnificent",
    # Amusement
    "amused", "amusement", "funny", "laugh", "laughing", "laughed", "laughter",
    "hilarious", "humor", "playful", "fun", "enjoyed",
    # Interest / Curiosity
    "curious", "curiosity", "interested", "interesting", "fascinated", "fascination",
    "intrigued", "captivated", "engaged",
]

P_NEGATIVE = [
    "miserable", "hopeless", "hopelessness", "despair", "despairing", "bleak",
    "dreary", "gloomy", "joyless", "cheerless", "dismal", "dread", "dreading",
    "pointless", "meaningless", "empty", "hollow", "numb", "flat",
]

P_PHRASES = [
    "feel great", "feeling great", "so happy", "really happy", "genuinely happy",
    "couldn't be happier", "on top of the world", "loving life", "best day",
    "made my day", "so grateful", "truly grateful", "deeply grateful",
    "count my blessings", "bright side", "silver lining", "looking forward to",
    "can't wait", "so excited", "really excited",
]


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# E â€” ENGAGEMENT / FLOW
# Absorbed, focused, lost in time, immersed
# Source: Csikszentmihalyi (1990) six flow characteristics
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
E_POSITIVE = [
    # Flow / absorption
    "absorbed", "immersed", "engrossed", "captivated", "riveted", "hooked",
    "lost in", "lost track", "flew by", "time flew", "hours passed",
    "didn't notice", "forgot about everything", "completely focused",
    # Focus / concentration
    "focused", "concentrating", "concentrated", "deep work", "in the zone",
    "in flow", "locked in", "dialed in", "present", "fully present",
    "mindful", "mindfulness", "here and now",
    # Engagement / involvement
    "engaged", "engaging", "involvement", "involved", "committed", "dedication",
    "dedicated", "passionate", "passion", "enthusiastic", "enthusiasm",
    "motivated", "motivation", "driven", "drive",
    # Mastery / challenge-skill balance
    "challenging", "challenge", "stretched", "pushed myself", "grew",
    "skill", "skilled", "proficient", "capable", "competent",
    "improving", "progress", "getting better", "learning",
]

E_NEGATIVE = [
    "bored", "boredom", "disengaged", "distracted", "unfocused", "scattered",
    "can't concentrate", "mind wandering", "zoning out", "checked out",
    "going through the motions", "autopilot", "mindless", "apathetic", "apathy",
]

E_PHRASES = [
    "lost track of time", "time flew by", "hours just passed", "completely absorbed",
    "couldn't put it down", "in the zone", "deep in it", "fully engaged",
    "totally focused", "so into it", "couldn't stop", "didn't want to stop",
]

E_TIME_DISTORTION = [
    "time flew", "lost track of time", "hours passed", "didn't realize",
    "before i knew it", "suddenly it was", "where did the time go",
]


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# R â€” RELATIONSHIPS
# Connection, belonging, love, social support
# Source: Seligman (2011) + Schwartz et al. (2016)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
R_POSITIVE = [
    # Connection words
    "friend", "friends", "friendship", "buddy", "mate", "pal", "companion",
    "family", "mom", "dad", "parent", "parents", "brother", "sister", "sibling",
    "partner", "spouse", "husband", "wife", "girlfriend", "boyfriend",
    "colleague", "coworker", "teammate", "together", "us", "we", "our",
    # Support / care
    "support", "supported", "supportive", "cared for", "cared about",
    "there for me", "showed up", "listened", "understood", "understanding",
    "helped", "help", "helped me", "kind", "kindness", "generous", "generosity",
    "compassion", "compassionate", "empathy", "empathetic",
    # Belonging / connection
    "belong", "belonging", "connected", "connection", "close", "closeness",
    "bond", "bonded", "bonding", "relationship", "meaningful relationship",
    "community", "group", "team", "together", "inclusion", "included",
    # Social positive experiences
    "caught up", "reunited", "reunion", "reached out", "checked in",
    "spent time with", "hung out", "talked with", "conversation with",
]

R_NEGATIVE = [
    "lonely", "loneliness", "alone", "isolated", "isolation", "disconnected",
    "no one", "nobody", "rejected", "rejection", "left out", "excluded",
    "abandoned", "betrayed", "betrayal", "let down", "misunderstood",
    "invisible", "unheard", "unseen", "unwanted",
]

R_STRUCTURAL = [
    # First-person plural signals connection (Schwartz et al. 2016)
    "we ", "us ", "our ", "together ", "each other",
]

R_PHRASES = [
    "there for me", "showed up for me", "really listened", "made me feel",
    "feel connected", "feel close", "feel supported", "not alone",
    "someone who understands", "people who care", "good people around me",
]


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# M â€” MEANING / PURPOSE
# Significance, contribution, part of something larger
# Source: Steger et al. (2006) MLQ + Seligman (2011)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
M_POSITIVE = [
    # Purpose words
    "purpose", "purposeful", "meaningful", "meaning", "matters", "matter",
    "significant", "significance", "important", "importance", "value", "valued",
    "worth", "worthwhile", "worthwhile", "makes a difference", "difference",
    # Contribution / service
    "contribute", "contribution", "helping", "serve", "service", "impact",
    "legacy", "leave a mark", "make a difference", "give back", "give something back",
    # Calling / mission
    "calling", "mission", "vocation", "passion", "driven by", "stand for",
    "believe in", "committed to", "dedicated to",
    # Understanding / coherence
    "understand", "understanding", "makes sense", "clarity", "clear",
    "know why", "reason", "direction", "path", "right path",
    # Belonging to something larger
    "part of something", "bigger picture", "bigger than myself",
    "greater good", "greater purpose", "cause", "movement",
]

M_NEGATIVE = [
    "pointless", "meaningless", "purposeless", "futile", "futility",
    "what's the point", "doesn't matter", "nothing matters", "who cares",
    "waste", "wasted", "going nowhere", "no direction", "lost", "adrift",
    "no reason", "why bother",
]

M_PHRASES = [
    "makes a difference", "means something", "part of something bigger",
    "reason to get up", "what i stand for", "what matters to me",
    "gives me purpose", "gives me meaning", "why i do this",
    "bigger than me", "greater good",
]

M_CAUSAL_MARKERS = [
    # Causal language signals meaning-making (Schwartz et al. 2016)
    "because", "therefore", "which means", "so that", "in order to",
    "the reason", "that's why",
]


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# A â€” ACCOMPLISHMENT / ACHIEVEMENT
# Mastery, goal pursuit, success, competence
# Source: Bandura (1997) mastery experiences + Seligman (2011)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
A_POSITIVE = [
    # Achievement words
    "achieved", "accomplish", "accomplished", "accomplishment", "succeeded",
    "success", "successful", "completed", "finished", "done", "did it",
    "made it", "pulled it off", "nailed it", "crushed it",
    # Progress / improvement
    "progress", "progressing", "improving", "improved", "growth", "growing",
    "developed", "development", "better than before", "getting better",
    "advancing", "advancing", "moving forward", "milestone", "reached",
    # Competence / mastery
    "mastery", "mastered", "expert", "expertise", "skilled", "skill",
    "capability", "capable", "competent", "competence", "proficient",
    "good at", "great at",
    # Goal pursuit
    "goal", "goals", "objective", "target", "aim", "aiming",
    "working toward", "working towards", "pursuing", "pursuit",
    "striving", "strive", "effort", "hard work", "working hard",
    # Recognition / validation
    "recognized", "recognition", "praised", "promotion", "promoted",
    "award", "award", "won", "winning", "first place",
]

A_NEGATIVE = [
    "failed", "failure", "failing", "can't do it", "not good enough",
    "incompetent", "incapable", "gave up", "giving up", "quit", "quitting",
    "stuck", "stagnant", "no progress", "going backwards", "falling behind",
    "underachiever", "disappointing", "disappointed in myself",
]

A_PHRASES = [
    "finally done", "got it done", "made it happen", "figured it out",
    "worked hard", "put in the work", "paid off", "all paid off",
    "proud of myself", "did my best", "gave it my all",
    "achieved my goal", "hit my target", "reached my goal",
]

A_PAST_TENSE_ACHIEVEMENT = [
    # Past-tense achievement verbs signal accomplishment (structural signal)
    "finished", "completed", "achieved", "succeeded", "accomplished",
    "mastered", "solved", "built", "created", "launched", "shipped",
    "delivered", "published", "graduated", "certified",
]


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CROSS-DIMENSION STRUCTURAL SIGNALS
# From Schwartz et al. (2016) language-wellbeing mapping
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
STRUCTURAL_SIGNALS = {
    "R_plus":   ["we ", "us ", "our ", "together", "each other", "with each other"],
    "M_plus":   ["because", "therefore", "which means", "so that", "in order to", "the reason"],
    "E_plus":   ["lost track of time", "time flew", "before i knew it", "suddenly it was"],
    "A_plus":   ["finished", "completed", "achieved", "solved", "built", "launched", "shipped"],
    "P_minus":  ["i can't", "nothing works", "always", "never", "everyone hates", "no one cares"],
}


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SCORING FUNCTION
# Returns dict with scores per dimension: -1.0 to +1.0
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def score_perma(text: str) -> dict:
    """
    Score a text on all 5 PERMA dimensions.
    Returns: {"P": float, "E": float, "R": float, "M": float, "A": float}
    Each score is -1.0 (strongly negative) to +1.0 (strongly positive).
    """
    lower = text.lower()
    words = lower.split()
    n = max(len(words), 1)

    def _word_score(positives, negatives, phrases=None, structural=None):
        pos = sum(1 for w in positives if w in lower) / n * 10
        neg = sum(1 for w in negatives if w in lower) / n * 10
        phrase_bonus = 0.0
        if phrases:
            phrase_bonus = sum(0.15 for p in phrases if p in lower)
        struct_bonus = 0.0
        if structural:
            struct_bonus = sum(0.10 for s in structural if s in lower)
        raw = pos - neg + phrase_bonus + struct_bonus
        return max(-1.0, min(1.0, raw))

    return {
        "P": _word_score(P_POSITIVE, P_NEGATIVE, P_PHRASES),
        "E": _word_score(E_POSITIVE, E_NEGATIVE, E_PHRASES, E_TIME_DISTORTION),
        "R": _word_score(R_POSITIVE, R_NEGATIVE, R_PHRASES, R_STRUCTURAL),
        "M": _word_score(M_POSITIVE, M_NEGATIVE, M_PHRASES, M_CAUSAL_MARKERS),
        "A": _word_score(A_POSITIVE, A_NEGATIVE, A_PHRASES, A_PAST_TENSE_ACHIEVEMENT),
    }


if __name__ == "__main__":
    # Quick self-test
    tests = [
        ("I'm so grateful for my friends, they really showed up for me today.", {"R": True, "P": True}),
        ("I finally finished the project after months of hard work. Couldn't be prouder.", {"A": True, "P": True}),
        ("I've been completely absorbed in this book, lost track of time entirely.", {"E": True}),
        ("I feel like what I do really matters and makes a difference.", {"M": True}),
        ("I feel lonely and like nothing I do matters at all.", {"R": False, "M": False}),
    ]

    print("PERMA Lexicon Self-Test")
    print("=" * 50)
    for text, expectations in tests:
        scores = score_perma(text)
        print(f"\nText: {text[:60]}...")
        print(f"Scores: P={scores['P']:+.2f} E={scores['E']:+.2f} R={scores['R']:+.2f} M={scores['M']:+.2f} A={scores['A']:+.2f}")
        for dim, should_be_positive in expectations.items():
            actual_positive = scores[dim] > 0
            status = "PASS" if actual_positive == should_be_positive else "FAIL"
            print(f"  {status}: {dim} expected {'positive' if should_be_positive else 'negative'}, got {scores[dim]:+.2f}")
