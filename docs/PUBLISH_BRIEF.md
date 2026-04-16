# Resonance v2.0.0 â€” Forum Post

---

Show HN: Resonance v2 â€“ Emotional intelligence layer for AI, now with a trained model

I've been building Resonance â€” it sits between your users and your LLM, reads the emotion behind what they write, and injects that context before the LLM responds. v2.0.0 is out today.

The problem it solves hasn't changed: text doesn't carry emotion. When someone types "I'm fine" or "whatever, doesn't matter" â€” the LLM sees words. It has no idea if that person is exhausted, shutting down, or genuinely okay. Resonance gives it that context.

What changed in v2 is how the detection works.

v1 used lexicons and hand-coded rules. v2 replaces that with a custom student model distilled from three specialist teachers trained on real human emotional expression. The main thing that motivated the rebuild was shame and guilt â€” every general-purpose emotion model I looked at collapsed them into one class or missed one entirely. v2 trains a dedicated specialist on the distinction, including PoliGuilt guilt typing which identifies the specific guilt type underneath.

The other thing that's different from most emotion detection out there: the psychology framework signals are continuous scored outputs, not binary flags. PERMA across five dimensions, Self-Determination Theory, Window of Tolerance, reappraisal vs suppression, Wise Mind, secondary emotion â€” all scored continuously with every message, grounded in the clinical research each framework comes from. Crisis detection runs as a dedicated model head independently of everything else.

It runs fully local. The weights download once (~700MB) and run offline after that. No API call, no data leaving your infrastructure.

Three lines to integrate with any LLM:

```python
from resonance import Resonance

r = Resonance(user_id="your-user-id")
context = r.process("I've been so anxious about this")
llm.chat(system=context.to_prompt(), message=message)
```

Resonance learns in two ways. First, from every message â€” each call to r.process() reads the emotion, updates the user's local profile, and builds a richer picture of who they are over time. Patterns, tendencies, suppression signals, regulation style â€” all accumulating silently in the background. The LLM gets more accurate context with every conversation, no extra effort from the user or developer. Second, from explicit corrections â€” if a user taps a different emotion chip to say the detection was wrong, that correction feeds directly into their per-user reinforcement loop and adjusts future detections for them specifically. Both paths are local, both require no opt-in.

Upgrading from v1 is just `pip install --upgrade resonance-layer`. No API changes.

Honest about limitations: shame still has the lowest F1 of any class. Sadness is weaker than anger, fear, and joy. Some high-arousal distress comes back as surprise. The model is better than v1 but not perfect, and those gaps are documented.

One hard requirement: if `crisis_detected` is True in the EmotionResult, you need to surface a crisis resource immediately. That's in the ethics doc and it's non-negotiable.

- pip install resonance-layer
- resonance-layer.com
- github.com/wpferrell/Resonance

Named after Jody. She walks into a room and just knows. That's the standard.
