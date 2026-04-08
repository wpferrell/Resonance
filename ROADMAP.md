# Resonance â€” Roadmap

*Last updated: April 2026*

---

## What Resonance Is Building Toward

Resonance sits invisibly in any conversation and knows how a person actually feels â€” not what they say, but what is underneath. It gets more accurate per person over time. It makes any LLM conversation feel like something that genuinely knows you are there.

Every decision in this roadmap traces back to that vision.

---

## What Is Live Now

- **resonance-layer v1.x** â€” installable via `pip install resonance-layer`
- Emotion detection across 7 classes with VAD scoring
- Six psychology framework signals: PERMA, SDT, Window of Tolerance, reappraisal/suppression, Wise Mind, secondary emotion
- Per-user emotional profile that builds over time
- LLM context injection via `to_prompt()`
- Anonymous feedback collection to Pi server
- Fully local â€” no data leaves the device without explicit opt-in

---

## What Is Being Built â€” v2.0.0

A ground-up rebuild of the emotion model at the core of Resonance.

The current model gets the broad strokes right but struggles with nuanced emotions â€” particularly shame, which sits close to guilt and embarrassment in emotional space. v2.0.0 fixes this with a new teacher-student architecture trained on a carefully curated dataset of real human emotional expression.

**What changes in v2.0.0:**
- New student model replacing the current one â€” more accurate, especially on subtle and hard-to-detect emotions
- All six psychology framework signals upgraded from rule-based to model-driven scored outputs
- Richer LLM context â€” more signal, more nuance, more useful to the LLM
- Same install, same API â€” developers get the upgrade automatically

**What stays the same:**
- `pip install resonance-layer` â€” no change
- `r.process()` and `to_prompt()` â€” no change
- Fully local, no external server required â€” no change
- BUSL 1.1 license â€” no change

---

## Timeline

v2.0.0 is in active development. No release date is promised. It ships when it is right.

---

## Further Out

After v2.0.0 is live and validated:

- **Personal adaptation** â€” the model adapts to individual users over time, getting more accurate to each specific person
- **Voice layer** â€” emotion detection from speech, not just text
- **Consumer app** â€” desktop app with panel UI, supporting Ollama, Claude, and ChatGPT in one place
- **Clinical validation** â€” longitudinal dataset and academic collaboration

---

## What Will Never Change

- Resonance is a layer, not a product. It works invisibly in the background.
- No message text is ever stored or transmitted without explicit user consent.
- No user is ever identified, profiled, or tracked without consent.
- Resonance reflects emotion â€” it never diagnoses, treats, or replaces professional support.
- The science inside is serious because the people using it are real.

---

*For integration documentation, see [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).*
*For ethics and principles, see [ETHICS.md](ETHICS.md).*
