# Resonance

[![PyPI version](https://badge.fury.io/py/resonance-layer.svg)](https://pypi.org/project/resonance-layer/)


*The emotional memory layer for AI.*

---

## What It Is

Resonance is an emotional memory layer for AI — it reads the feeling behind your words, learns who you are over time, and gives any AI the emotional awareness to respond to how you actually feel, not just what you said.

Text doesn't carry emotion. You know what you meant when you wrote it — but the AI only sees the words.

Resonance changes that. It reads what is underneath. The exhaustion behind a short reply. The anxiety inside a polite question. The things you feel but would never think to say out loud — and sometimes don't even have words for yet.

It remembers. It learns you over time. And it gives that understanding to any AI before it ever responds to you — so the conversation feels less like typing at a machine and more like talking to something that actually knows you're there.

Not a messenger. A connection.

Resonance is named after Jody. She walks into a room and just knows. That is the standard.

---

## What It Does

Everything happens invisibly. You write. Resonance reads — not just the words, but the weight behind them. It detects emotion, measures intensity, tracks how you are doing right now versus how you have been doing over time. It updates your profile with every message. And before the AI responds to you, Resonance tells it everything it needs to know about where you actually are.

You do nothing differently. The conversation just feels different — because for the first time, the AI knows who it is talking to.

Resonance v2 runs a custom-trained model built on real human expressions. Detection is no longer rule-based — it is learned. Every signal is produced by a model trained specifically to understand emotion the way people actually express it.

---

## How It Learns

Resonance learns you in layers.

**From the start** — it reads the emotion in every message automatically. No setup required.

**From your corrections** — if it gets something wrong, you can tell it. One tap. It remembers and adjusts. The more you correct it, the more accurate it becomes for you specifically.

**From your patterns** — over time, Resonance builds a profile. Not a data file. A living picture. It notices that you tend to feel frustrated on certain topics, or that your energy is lower in the evenings, or that you process difficult things through humour. It holds all of that and uses it.

**From context** — you can optionally tag what you are doing when you send a message. Working, resting, talking to family. That context helps Resonance understand why you feel the way you do, not just what you feel.

The longer you use it, the better it knows you. Zero extra effort required.

---

## The Panel

The Resonance panel sits beside your conversation. It is not in the way. It reflects you back to yourself.

At a glance you can see:

- **What Resonance senses right now** — a short plain-English description of your current emotional state
- **Your mood and energy** — two simple bars showing where you are right now
- **Emotion chips** — the specific emotions detected in this conversation, starting with the strongest
- **Search** — type how you feel if you want to explore it

The panel is a mirror. It does not tell you what to do with what you are feeling. It just shows you what it sees.

---

## The Science Inside It

Resonance is not guessing. Every detection is grounded in established psychological research.

Seven detection frameworks are baked into every layer:

- **Self-Determination Theory** — reads your need for autonomy, connection, and competence beneath what you say
- **DBT secondary emotion** — detects what you feel underneath the surface emotion, independently
- **Reappraisal vs suppression** — detects how you are relating to your emotion, not just what it is
- **Window of Tolerance** — knows whether you are calm, overwhelmed, or shut down
- **PERMA flourishing** — scores all five dimensions of wellbeing continuously: Positive emotion, Engagement, Relationships, Meaning, and Achievement — updated with every message
- **Wise Mind detection** — recognises when you are in emotional mind, reasonable mind, or the balance between them
- **PoliGuilt guilt typing** — distinguishes guilt from shame and identifies the specific guilt type beneath surface emotion

There is no good or bad emotion inside Resonance. Every signal is treated with equal weight.

The science is serious because the people using it are real.

---

## Improving Over Time

Resonance gets more accurate the more it is used — both for you personally, and for everyone.

**For you** — every correction you make teaches Resonance your specific patterns. The more you use it, the more it knows you.

**For everyone** — when you first run Resonance, it will ask you one question: whether you want to share anonymous correction data to help improve the model for all users. Corrections only — no message text, no identity, nothing personal. You must make a conscious choice. There is no default. You can change your answer at any time:

```python
r.set_feedback(True)   # turn on
r.set_feedback(False)  # turn off
```

**Version updates** — when a new version of Resonance is available, it will tell you once at startup:

```
┌─ Resonance Update Available ─────────────────────────┐
│  New version: 2.0.1  (you have 2.0.0)                │
│  pip install --upgrade resonance-layer               │
└───────────────────────────────────────────────────────┘
```

It never updates silently. You always choose when to update.

---

## What It Is Not

Resonance is not a therapy tool and makes no clinical claims.

It reflects emotion — it does not diagnose, treat, or replace professional support.

It is a mirror, not a therapist. It detects emotion. It never tells you what that emotion means for your life.

If you are in crisis, Resonance will flag it — and any application built on Resonance is required to surface appropriate support immediately.

---

## For Developers

Add emotional awareness to any LLM in three lines:

```python
from resonance import Resonance

r = Resonance()
context = r.process("I've been so anxious about this")

# Pass context to your LLM before the conversation
llm.chat(system=context.to_prompt(), message=message)
```

Resonance v2 runs a custom-trained model built on real human expressions — primary emotion, shame/guilt separation, crisis detection, and all framework signals are produced by the model directly. Detection is learned, not rule-based.

Resonance handles everything else — detection, profiling, injection, flagging. You handle the conversation.

**Requirements:** Python 3.10+, runs fully embedded, no external server required.

**First run:** model weights (~700MB) download automatically from HuggingFace on first use and are cached locally. After that, everything runs fully offline.

**Install:**

Linux:
```bash
curl -fsSL https://install.resonance-layer.com/install-linux.sh | sh
```

Mac:
```bash
curl -fsSL https://install.resonance-layer.com/install-mac.sh | sh
```

Windows:
```powershell
irm https://install.resonance-layer.com/install-win.ps1 | iex
```

The install script handles everything automatically — virtual environment, dependencies, first-run setup, and model download in one command.

**Manual install (any OS):**
```bash
pip install resonance-layer
```

For full integration documentation including edge cases, flags reference, and developer responsibilities — read the [Developer Guide](DEVELOPER_GUIDE.md).

For ethical principles, prohibited use cases, and safeguards — read the [Ethics Document](ETHICS.md).

---

## License

Resonance is released under the [Business Source License (BUSL)](LICENSE).

Free for individual and non-commercial use. Commercial use requires a license.

---

## Links
- [Website](https://resonance-layer.com)
- [PyPI](https://pypi.org/project/resonance-layer/)

- [Developer Guide](DEVELOPER_GUIDE.md) — integration, edge cases, flags reference
- [Ethics & Principles](ETHICS.md) — what Resonance will and will not do
- [GitHub](https://github.com/wpferrell/Resonance) — source code, issues, contributions


