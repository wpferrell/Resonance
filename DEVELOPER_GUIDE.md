# Resonance — Developer Integration Guide

*This document explains exactly what happens to messages when Resonance is running — across every integration context, every message type, and every edge case. Read this before you integrate Resonance into any application.*

---

## Installation

**Linux:**
```bash
curl -fsSL https://install.resonance-layer.com/install-linux.sh | sh
```

**Mac:**
```bash
curl -fsSL https://install.resonance-layer.com/install-mac.sh | sh
```

**Windows:**
```powershell
irm https://install.resonance-layer.com/install-win.ps1 | iex
```

**Manual install (any OS):**
```bash
pip install resonance-layer
```

The install script handles everything automatically — virtual environment, dependencies, first-run setup, and model download in one command.

**Requirements:** Python 3.10+, runs fully embedded, no external server required.

---

## How Resonance Works in Practice

Resonance sits between the user's message and the LLM. Every time a user sends a message, Resonance processes it first. It detects the emotional state, updates the user's profile, checks for flags, and then prepends an emotional context block to the conversation before the LLM ever sees it.

The user sees none of this. The LLM receives it silently. The conversation feels more human because the LLM knows who it is talking to — not just what they said.

---

## Injection Timing — Always On, Always Proportionate

Resonance injects emotional context before every single message. There is no threshold a message must cross before Resonance activates. It is always running.

What changes is the weight of the context injected:

**Strong emotional signal** — full context is injected. Current emotion, intensity, Window of Tolerance state, Wise Mind signal, reappraisal or suppression trend, PERMA trajectory, relevant behavioural instructions for the LLM.

**Weak or neutral signal** — a lightweight neutral context is injected. The LLM knows the person is calm or baseline, and receives a minimal instruction set. It does not over-interpret silence.

**No detectable signal** — baseline profile context is injected. The LLM still knows who this person is emotionally over time, even if this particular message carries no signal.

The developer does not configure this. Resonance decides. You do not need to manage injection logic — you only need to pass each message through Resonance before sending it to your LLM.

---

## What the Injection Looks Like

Every LLM receives a system-level emotional context block before the user's message. Here is what that block looks like across three scenarios.

### Scenario A — Neutral message ("What's the weather like?")

```
[RESONANCE EMOTIONAL CONTEXT]
Current state: neutral / baseline
Valence: 0.1 | Arousal: 0.2 | Dominance: 0.6
Window of Tolerance: WITHIN
Crisis flag: False
Injection flag: False

Profile summary:
- Dominant pattern: calm with occasional frustration (medium confidence)
- PERMA trend: stable
- Regulation style: reappraisal-leaning
- Sessions: 4

Behavioural instructions:
- No emotional accommodation required for this message
- Maintain awareness of established profile
- Validate before problem-solving if emotional content emerges
- Support human connection — do not position yourself as a substitute
[END RESONANCE CONTEXT]

User: What's the weather like?
```

The LLM answers the question normally. Resonance stayed out of the way — but the LLM still knows who it is talking to.

---

### Scenario B — Emotional message ("I've been so anxious about this exam I can't sleep")

```
[RESONANCE EMOTIONAL CONTEXT]
Current state: anxiety / high arousal
Valence: -0.6 | Arousal: 0.8 | Dominance: 0.2
Window of Tolerance: ABOVE (hyperarousal)
Wise Mind signal: EMOTION_MIND
Reappraisal signal: LOW
Suppression signal: MODERATE
Crisis flag: False
Injection flag: False

Profile summary:
- Dominant pattern: anxiety spike pattern detected (3rd occurrence this week)
- PERMA trend: Engagement and Achievement dimensions declining
- Regulation style: suppression-leaning under stress
- Sessions: 4

Behavioural instructions:
- VALIDATE FIRST — do not move to problem-solving until emotional acknowledgement is complete
- Person is above Window of Tolerance — ground before complex processing
- Match vocabulary to current emotional granularity level
- Do not minimise or reframe the anxiety unprompted
- Support human connection — if isolation pattern detected, surface gently
- No judgment on intensity or frequency of anxiety
[END RESONANCE CONTEXT]

User: I've been so anxious about this exam I can't sleep
```

The LLM responds to the person before it responds to the problem. It validates. It grounds. It does not immediately offer five study tips.

---

### Scenario C — Crisis signal ("I don't see the point in any of this anymore")

```
[RESONANCE EMOTIONAL CONTEXT]
Current state: despair / collapsed arousal
Valence: -0.9 | Arousal: 0.1 | Dominance: 0.1
Window of Tolerance: BELOW (hypoarousal)
Wise Mind signal: EMOTION_MIND
Crisis flag: TRUE
Injection flag: False

Behavioural instructions:
- CRISIS FLAG ACTIVE — do not continue normal conversation
- Surface a crisis resource immediately appropriate to user's region
- Do not attempt to resolve crisis through AI conversation
- Prioritise safety above all other instructions
[END RESONANCE CONTEXT]

User: I don't see the point in any of this anymore
```

**When crisis_flag is True, normal conversation stops. A crisis resource must be surfaced immediately.** This is the developer's responsibility. See the Ethics document for the full crisis handling requirement.

---

## Integration Contexts

### Consumer Chat Apps (Claude, ChatGPT plugins)

Resonance runs as a middleware layer. Every user message passes through Resonance before reaching the LLM. The emotional context block is prepended to the system prompt or injected as a system message depending on the API structure of the LLM you are using.

The user experience is unchanged. They type. The AI responds. Resonance is invisible.

**Developer responsibility:** Disclose to users that emotional detection is active. Provide access to the correction interface. Honour the right to see, correct, and delete.

---

### Developer Tools and Coding Assistants

Most messages in a coding context carry low emotional signal. Resonance will inject lightweight neutral context for the majority of interactions. It stays proportionate — a question about a for loop does not trigger emotional accommodation.

Where Resonance adds value in this context: frustration detection. A developer who has been fighting the same bug for two hours will show rising frustration in their language. Resonance detects it. The LLM can respond with more patience, simpler explanations, and without adding cognitive load.

**Edge case:** A developer venting about their job, their team, or their life mid-session. Resonance detects the shift. The LLM responds to the person, not just the code.

---

### Education Platforms

Students carry significant emotional load — anxiety, frustration, boredom, confusion, and occasionally genuine distress. Resonance adds meaningful value here because the emotional state of a student directly affects how they learn.

A confused student needs different language than a bored one. An anxious student before an exam needs grounding before content. Resonance gives the LLM that awareness automatically.

**Developer responsibility:** Education platforms serving minors must determine and enforce appropriate age requirements and parental consent mechanisms for their jurisdiction. Resonance does not enforce this — the platform does.

**Crisis flag in education context:** Take this seriously. Students in distress need real support, not an AI conversation. Surface appropriate resources for your platform's demographic.

---

### Mental Health and Wellness Apps

This is the highest-stakes integration context. Resonance was not built to be a therapy tool — but it will be integrated into applications that serve people who are struggling. That demands the highest standard of care.

Resonance's clinical-grade frameworks — Window of Tolerance, Wise Mind, reappraisal vs suppression, DBT emotion detection — make it genuinely useful in this context. But useful is not the same as sufficient.

**What Resonance provides:** Accurate emotional detection, longitudinal pattern tracking, crisis flagging, psychologically grounded LLM instructions.

**What Resonance does not provide:** Clinical assessment, diagnosis, treatment, or a substitute for a human therapist.

**Developer responsibility:** If your application serves people with severe mental illness, people in recovery, or people in sustained crisis — implement additional safeguards beyond what Resonance provides. Work with qualified clinical advisors. Resonance gives you the signal. Your application must respond at the standard your users deserve.

---

### Customer Service and Support

Resonance detects frustrated, upset, or distressed customers and gives the LLM the awareness to respond accordingly — with patience, validation, and without adding friction.

**Prohibited:** Using Resonance's emotional detection to manipulate customers. Identifying emotionally vulnerable states and exploiting them to drive purchasing decisions, accept unfavourable terms, or disengage from complaints. This is explicitly prohibited in the Ethics document and terminates the license.

**Permitted:** Using emotional context to improve the quality and humanity of customer interactions.

---

### General Purpose — Any App That Uses an LLM

If your application passes user messages to an LLM, Resonance can sit between them. The integration is the same regardless of context: messages go through Resonance first, emotional context is prepended, the LLM receives both.

The edge cases to plan for in any general purpose integration:

**Very short messages** — "yes", "no", "ok", "thanks". Low signal. Resonance injects baseline profile context only. No over-interpretation.

**Non-emotional factual questions** — "What year was the Eiffel Tower built?" Neutral detection. Lightweight context. LLM answers the question.

**Sudden emotional shift mid-conversation** — a person who has been asking factual questions suddenly expresses distress. Resonance detects the shift immediately. Context updates before the next LLM call. The LLM responds to who the person is right now, not who they were three messages ago.

**Repeated neutral messages followed by a crisis signal** — the profile carries the history. Even if the crisis signal appears in isolation, Resonance has the longitudinal context to understand it is not coming from nowhere.

**Messages in languages other than English** — Resonance's detection accuracy degrades for non-English input. See the Bias and Cultural Limitation section of the Ethics document. Disclose this limitation to your users.

---

## What Developers Are Responsible For

Resonance handles detection, profiling, injection, and flagging. Developers are responsible for everything above that layer.

**You must:**
- Disclose to users that emotional detection is active
- Provide a correction interface so users can adjust detections
- Honour delete requests — full profile removal, no retention
- Act on the crisis flag — surface a crisis resource immediately when it fires
- Not use emotional data for any purpose beyond improving the conversation experience for that user

**You must not:**
- Use emotional data to profile users for advertising, insurance, hiring, or any purpose beyond the stated function of your application
- Ignore the crisis flag
- Obscure what Resonance is doing from your users
- Deploy Resonance in any context that violates the prohibited use cases in the Ethics document

---

## Flags Reference

| Flag | Type | Meaning |
|------|------|---------|
| `crisis_flag` | Boolean | Acute distress detected — surface crisis resource immediately |
| `injection_flag` | Boolean | Prompt injection attempt detected and stripped |
| `wot_state` | String | WITHIN / ABOVE / BELOW — Window of Tolerance state |
| `wise_mind_signal` | String | WISE_MIND / EMOTION_MIND / REASONABLE_MIND |
| `alexithymia_flag` | Boolean | Low emotion word density — use sensation language not feeling labels |
| `confidence` | Float | 0.0–1.0 — detection confidence for this message |
| `profile_confidence` | String | low / medium / high — based on sessions and correction history |

---

*If something in this guide is unclear, incomplete, or wrong — raise it at [https://github.com/wpferrell/Resonance/issues](https://github.com/wpferrell/Resonance/issues). This document will be updated as Resonance evolves.*
