"""
Resonance Emoji Emotion Lexicon
Built from: Godard & Holtzman (2022) MLE + Unicode CLDR emoji descriptions
CC-BY: Godard, R. & Holtzman, S. (2022) Front. Psychol. DOI: 10.3389/fpsyg.2022.921388
359 emojis rated on anger/anticipation/disgust/fear/joy/sadness/surprise/trust/positive/negative
We map to Resonance 7-class taxonomy: joy/sadness/anger/fear/surprise/shame/neutral
"""

# emoji -> (primary_emotion, confidence)
EMOJI_EMOTION_MAP = {
    # JOY / HAPPINESS
    "😀": ("joy", 0.95), "😁": ("joy", 0.95),
    "😂": ("joy", 0.90), "🤣": ("joy", 0.90),
    "😃": ("joy", 0.95), "😄": ("joy", 0.95),
    "😅": ("joy", 0.75), "😆": ("joy", 0.90),
    "😊": ("joy", 0.90), "😋": ("joy", 0.80),
    "😎": ("joy", 0.75), "🥰": ("joy", 0.95),
    "😍": ("joy", 0.90), "🤩": ("joy", 0.95),
    "😘": ("joy", 0.85), "😗": ("joy", 0.80),
    "😙": ("joy", 0.80), "😚": ("joy", 0.85),
    "🙂": ("joy", 0.70), "🤗": ("joy", 0.85),
    "😛": ("joy", 0.75), "😜": ("joy", 0.75),
    "🤪": ("joy", 0.70), "😝": ("joy", 0.75),
    "🤑": ("joy", 0.70), "🥳": ("joy", 0.95),
    "🎉": ("joy", 0.90), "🎊": ("joy", 0.90),
    "🥂": ("joy", 0.80), "🍾": ("joy", 0.80),
    "✨": ("joy", 0.70), "🌟": ("joy", 0.70),
    "⭐": ("joy", 0.65), "💫": ("joy", 0.65),
    "🌈": ("joy", 0.80), "☀️": ("joy", 0.65),
    "😻": ("joy", 0.90), "😺": ("joy", 0.75),
    "🐶": ("joy", 0.70), "🌺": ("joy", 0.65),
    "🌸": ("joy", 0.70), "🌼": ("joy", 0.65),
    "🌻": ("joy", 0.70), "👍": ("joy", 0.65),
    "👏": ("joy", 0.75), "🙏": ("joy", 0.70),
    "💪": ("joy", 0.70), "✌️": ("joy", 0.70),
    "🫶": ("joy", 0.80),
    # LOVE / AFFECTION
    "❤️": ("joy", 0.90), "🧡": ("joy", 0.85),
    "💛": ("joy", 0.85), "💚": ("joy", 0.80),
    "💙": ("joy", 0.80), "💜": ("joy", 0.80),
    "🖤": ("sadness", 0.60), "🤍": ("joy", 0.70),
    "🤎": ("joy", 0.65), "💗": ("joy", 0.90),
    "💓": ("joy", 0.90), "💞": ("joy", 0.90),
    "💕": ("joy", 0.90), "💖": ("joy", 0.90),
    "💝": ("joy", 0.90), "💘": ("joy", 0.85),
    "💟": ("joy", 0.80), "♥️": ("joy", 0.85),
    # SADNESS / GRIEF
    "😢": ("sadness", 0.95), "😭": ("sadness", 0.95),
    "😔": ("sadness", 0.85), "😞": ("sadness", 0.85),
    "😟": ("sadness", 0.80), "😕": ("sadness", 0.75),
    "🙁": ("sadness", 0.80), "☹️": ("sadness", 0.85),
    "😣": ("sadness", 0.80), "😖": ("sadness", 0.80),
    "😩": ("sadness", 0.75), "😪": ("sadness", 0.75),
    "😓": ("sadness", 0.70), "🥺": ("sadness", 0.85),
    "😿": ("sadness", 0.90), "💔": ("sadness", 0.90),
    "🥀": ("sadness", 0.80), "🌪️": ("sadness", 0.60),
    # ANGER / FRUSTRATION
    "😡": ("anger", 0.95), "🤬": ("anger", 0.95),
    "😠": ("anger", 0.90), "😤": ("anger", 0.85),
    "💢": ("anger", 0.90), "👿": ("anger", 0.85),
    "😾": ("anger", 0.80), "🖖": ("anger", 0.90),
    "💣": ("anger", 0.75), "🔥": ("anger", 0.65),
    "⚡": ("anger", 0.65), "🤢": ("anger", 0.80),
    "🤮": ("anger", 0.85), "😒": ("anger", 0.70),
    "🙄": ("anger", 0.65), "😏": ("anger", 0.60),
    # FEAR / ANXIETY
    "😨": ("fear", 0.90), "😰": ("fear", 0.85),
    "😱": ("fear", 0.90), "😧": ("fear", 0.80),
    "😦": ("fear", 0.80), "🫣": ("fear", 0.75),
    "😬": ("fear", 0.65), "😥": ("fear", 0.70),
    "🤐": ("fear", 0.60),
    # SURPRISE
    "😲": ("surprise", 0.90), "🤯": ("surprise", 0.90),
    "😮": ("surprise", 0.80), "🫢": ("surprise", 0.80),
    "🤔": ("surprise", 0.55), "🧐": ("surprise", 0.55),
    "😜": ("surprise", 0.55), "🤭": ("surprise", 0.65),
    # SHAME / EMBARRASSMENT
    "😳": ("shame", 0.85), "🫣": ("shame", 0.70),
    "🙈": ("shame", 0.75), "🤦": ("shame", 0.75),
    "🤦‍♂️": ("shame", 0.75),
    "🤦‍♀️": ("shame", 0.75),
    # NEUTRAL
    "😐": ("neutral", 0.80), "😑": ("neutral", 0.80),
    "🤷": ("neutral", 0.70),
    "🤷‍♂️": ("neutral", 0.70),
    "🤷‍♀️": ("neutral", 0.70),
    "👎": ("sadness", 0.65),
}


def get_emoji_emotion(text: str):
    """Find highest-confidence emoji emotion in text. Returns (emotion, confidence) or None."""
    best_emotion = None
    best_conf = 0.0
    for emoji, (emotion, conf) in EMOJI_EMOTION_MAP.items():
        if emoji in text and conf > best_conf:
            best_emotion = emotion
            best_conf = conf
    return (best_emotion, best_conf) if best_emotion else None


def get_all_emoji_emotions(text: str):
    """All emoji emotions found in text, sorted by confidence desc."""
    results = []
    for emoji, (emotion, conf) in EMOJI_EMOTION_MAP.items():
        if emoji in text:
            results.append((emoji, emotion, conf))
    return sorted(results, key=lambda x: x[2], reverse=True)


if __name__ == "__main__":
    tests = [
        ("😊🎉", "joy"),
        ("😭💔", "sadness"),
        ("😡💢", "anger"),
        ("😱", "fear"),
        ("😳", "shame"),
    ]
    print("Emoji Lexicon Test")
    for text, expected in tests:
        r = get_emoji_emotion(text)
        if r:
            emotion, conf = r
            status = "PASS" if emotion == expected else "FAIL"
            print(f"  {status}: {text} -> {emotion} ({conf:.0%}), expected {expected}")
        else:
            print(f"  FAIL: {text} -> no match")
