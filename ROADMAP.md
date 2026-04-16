# Resonance  -  Roadmap

*Last updated: April 2026*

---

## What Resonance Is Building Toward

Resonance sits invisibly in any conversation and knows how a person actually feels  -  not what they say, but what is underneath. It gets more accurate per person over time. It makes any LLM conversation feel like something that genuinely knows you are there.

Every decision in this roadmap traces back to that vision.

---

## What Is Live Now

- **resonance-layer v2.0.0**  -  installable via `pip install resonance-layer`
- Custom-trained student model replacing the v1 rule-based system  -  detection is learned, not rule-based
- Emotion detection across 7 classes with VAD scoring
- Seven psychology framework signals: PERMA, SDT, Window of Tolerance, reappraisal/suppression, Wise Mind, secondary emotion, PoliGuilt guilt typing
- Per-user emotional profile that builds over time
- LLM context injection via `to_prompt()`
- Anonymous feedback collection to Pi server
- Fully local  -  no data leaves the device without explicit opt-in

---

## What Changed in v2.0.0

A ground-up rebuild of the emotion model at the core of Resonance.

v1 got the broad strokes right but struggled with nuanced emotions  -  particularly shame, which sits close to guilt and embarrassment in emotional space. v2.0.0 addresses this with a new teacher-student architecture trained on a carefully curated dataset of real human emotional expression.

**What changed:**
- New custom-trained student model  -  more accurate, especially on subtle and hard-to-detect emotions
- Primary emotion, shame/guilt separation, and crisis detection now model-driven
- Framework signals produce richer scored outputs
- Richer LLM context  -  more signal, more nuance, more useful to the LLM
- Same install, same API  -  developers get the upgrade automatically

**What stayed the same:**
- `pip install resonance-layer`  -  no change
- `r.process()` and `to_prompt()`  -  no change
- Fully local, no external server required  -  no change
- BUSL 1.1 license  -  no change

---

## Timeline

v2.0.0 is live. Further out work is listed below.

---

## Further Out

After v2.0.0 is live and validated:

- **Personal adaptation**  -  the model adapts to individual users over time, getting more accurate to each specific person
- **Voice layer**  -  emotion detection from speech, not just text
- **Consumer app**  -  desktop app with panel UI, supporting Ollama, Claude, and ChatGPT in one place
- **Clinical validation**  -  longitudinal dataset and academic collaboration

---

## What Will Never Change

- Resonance is a layer, not a product. It works invisibly in the background.
- No message text is ever stored or transmitted without explicit user consent.
- No user is ever identified, profiled, or tracked without consent.
- Resonance reflects emotion  -  it never diagnoses, treats, or replaces professional support.
- The science inside is serious because the people using it are real.

---

*For integration documentation, see [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).*
*For ethics and principles, see [ETHICS.md](ETHICS.md).*
