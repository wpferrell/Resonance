# RESONANCE_STATE.md
# Single source of truth for every session.
# Claude reads this at session start. Update at session end.
# If this conflicts with memory, THIS FILE WINS.
# Last updated: April 6 2026

---

## WHAT RESONANCE IS
An Affective Memory Layer for AI. Named after Jody (Will's wife).
A layer — not just a model. Detects emotion, builds per-user context over time, hands that context to any LLM before it responds. Works in the background, zero effort from the user. Makes any AI conversation feel like genuine human connection.

---

## LIVE STATUS
| Item | Status |
|---|---|
| PyPI package | resonance-layer v1.0.34 |
| GitHub | wpferrell/Resonance (public) |
| HuggingFace model | wpferrell/resonance-model (ModernBERT-base) |
| Landing page | resonance-layer.com (live) |
| Install scripts | install.resonance-layer.com (live) |
| Feedback server | feedback.resonance-layer.com/stats (live, reset to zero) |
| Current model shame F1 | 0.455 — THIS IS THE PROBLEM TO SOLVE |

---

## INFRASTRUCTURE
- Shadow PC: Windows 11, RTX A4500 20GB VRAM
- Project path: C:\Users\Shadow\Documents\Resonance
- Venv: .venv\Scripts\Activate.ps1
- Pi server: feedback.resonance-layer.com (permanent URL)
- Pi runs via: nohup uvicorn server:app --host 0.0.0.0 --port 8000
- HuggingFace token (read-only): stored in resonance/model_loader.py — do not put in any tracked file
- GitHub Actions: triggers only on tag push matching v* — commits alone do NOT publish
- Publish sequence: bump version.py + pyproject.toml → commit → push → git tag vX.X.X && git push origin vX.X.X

---

## DATASET STACK
- Registry version: v8
- Confirmed datasets: 29
- Total rows: ~1,482,500
- Registry file: Resonance_Dataset_Registry.md (gitignored — local only, proprietary)
- Data script: scripts/prepare_data_v2.py (gitignored — local only, proprietary)
- ISEAR: REMOVED from active list (was still listed — fixed April 2026)

### Blocked / Pending
- ABBE Corpus: all 7 rules pass, CC0, 2,010 rows — BLOCKED: FIU server file broken (datafile ID 2731). Email sent to rdm@fiu.edu. When fixed → dataset #30.
- Reddit MH MDPI: in script, needs data/raw/reddit_mh_mdpi_800.csv downloaded manually from paper supplementary materials. When downloaded → loads automatically.
- enISEAR: monitor — email sent to Roman Klinger, Univ Stuttgart re CC/MIT licence.

### Dataset scout
- Script: scripts/dataset_scout.py
- Running: every 4 hours, 18 sources, Windows toast on FOUND/BORDERLINE
- Results: scripts/scout_results.md (review before starting P2)
- Seen cache: scripts/scout_seen.json (pre-loaded with all 29 datasets + known fails)

### Dataset rules (7)
R1: Commercial licence only | R2: Peer-reviewed/institution | R3: Real human text only | R4: Emotional/psychological states | R5: No narrow domain | R6: No gated access | R7: No structural imbalance
- PERMANENTLY EXCLUDED: LIWC (no exceptions), EmpatheticDialogues (R1), DailyDialog, RECCON (R1+R6)

---

## CURRENT MODEL & ARCHITECTURE

### Current (live)
ModernBERT-base. Shame F1 = 0.455. Replaced by student in build queue.

### Student (to be built)
- Backbone: DeBERTa-v3-base (86M, 768 dims, 12 layers)
- 10 active heads: primary emotion (7-class), VAD regression, CNN local patterns, confidence calibration, secondary emotion TONE (21-class), reappraisal/suppression, alexithymia, PoliGuilt guilt type (4-class), crisis detection, PERMA wellbeing (5 outputs)
- 3 deferred heads: Window of Tolerance (threshold recalibration), Wise Mind (session-level), sustained distress (session counter)
- 2 encoder objectives: domain adversarial training (20 source domains) + contrastive loss (shame separation)
- VAD targets: NRC VAD Lexicon token-level scoring on training data (Option D)
- 3 teachers (all train on Will's human-labeled data only):
  - DeBERTa-v3-large + CNN head (shame/guilt specialist)
  - XLNet-large (anger + contextual dependencies)
  - ELECTRA-large (fear + compute-efficient signal)

---

## EXTRACTOR STATUS
File: resonance/extractor.py
Libraries: NRCLex + TextBlob + Empath MIT
EmotionResult fields (19): valence, arousal, dominance, primary_emotion, secondary_emotion, window_of_tolerance, wot_triggered_by, wise_mind_signal, reappraisal_signal, suppression_signal, guilt_type, confidence, alexithymia_flag, modality, raw_nrc_scores, raw_empath_scores, crisis_detected, sustained_distress, outward_reflection

Phase 3 will convert wise_mind, reappraisal, suppression from booleans → scored floats and add 6 new framework fields.

---

## BUILD QUEUE STATUS
Full detail: docs/BUILD_QUEUE.md

| Phase | What | Status |
|---|---|---|
| P1 | Architecture spec + validation criteria (docs/ARCHITECTURE_SPEC.md) | NOT STARTED |
| P2 | Reddit MH MDPI CSV + build_training_data.py (dedup + soft labels + back-translation) | NOT STARTED |
| P3 | 6 framework signals in extractor + trajectory + ethics + MLE emoji + validate | NOT STARTED |
| P4 | DAPT + 3 teachers + validate + student 18 heads + confidence profile + validate | NOT STARTED |
| P5 | Extractor refactor + feedback + storage + Pi + attachment + validate | NOT STARTED |
| P6 | ONNX stack | PARKED — do not start until P1-P5 complete |

### Validation criteria (to be locked in ARCHITECTURE_SPEC.md)
- After P3: all 6 frameworks correct on 20+ real sentences, trajectory correct across 5-message sim
- After teacher train: soft label agreement >0.6 on shame, distributions within 10% on majority classes
- After student train: shame F1 >0.60, all 18 heads non-null, VAD in expected range, no collapsed heads
- After P5: message → extractor → all fields → feedback → Pi stats shows all new fields

---

## EXTRACTOR FRAMEWORK BUILD ORDER (P3) — LOCKED
1. PERMA (5 scored float fields: perma_p, perma_e, perma_r, perma_m, perma_a)
2. SDT (3 scored float fields: autonomy_signal, competence_signal, relatedness_signal)
3. WoT trajectory (session-level: escalating / stable / deescalating)
4. Secondary emotion independence (parallel detection, not SECONDARY_MAP lookup)
5. Reappraisal/suppression scored floats (convert from boolean + add distress trajectory)
6. Wise Mind scored float (convert from boolean)
Then: ethics revision → trajectory layer → MLE emoji lexicon → VALIDATE

---

## PANEL & UI — LOCKED
Teal dot header → large emoji + serif "You seem X" + 3-4 word italic reflection → 2 bars (mood/energy, 4px, word labels) → teal senses block (border-left 2px #4fd1c5, bg #E1F5EE) → divider → "does this feel right?" + chip grid → bottom search "how do you feel?"

Chip layout: max 6, 1fr 1fr grid. c1 full width. c2 2 equal. c3 detected full + 2 below. c4 2×2. c5 detected full + 2×2. c6 detected full + 2×2+2. Equal width, no orphan, text-overflow ellipsis. Saved chip: teal (#E1F5EE bg, #085041 text, #9FE1CB border).

Pill colors: Amber #f6ad55 (worry/anxiety/stress) | Red #fc8181 (angry/frustrated) | Pink #ed93b1 (hurt/loved) | Grey #a0aec0 (sad/empty/numb) | Dark grey #888780 (done) | Blue #85b7eb (lonely) | Teal #4fd1c5 (calm/okay) | Green #68d391 (happy/excited/grateful)

---

## FEEDBACK PHILOSOPHY — LOCKED
- Primary feedback = conversation text/messages = training data
- Secondary feedback = chip/panel selections = labels
- Text is data. Chips are labels. Together = complete training examples.
- Ethical solution = explicit user consent, not hidden telemetry.
- This is the dataset nobody else has.

Feedback box wording (locked):
"Before we begin - one question: / Help Resonance get better at understanding how people actually feel? / Anonymous emotion signals and conversation patterns are shared. Never your identity. / resonance config --feedback on/off / [1] Yes, help Resonance understand people better / [2] No, keep everything local"

---

## TRAINING DATA PRINCIPLES — LOCKED
- Every signal traces to real human training examples
- No LLM soft labels, no synthetic data, no data laundering
- VAD lookup table retired — model owns VAD output entirely, no fallback
- Fallbacks corrupt the learning loop — model must own its output and receive corrective signal on its own predictions
- Multi-teacher value = architectural diversity, not data manipulation — all teachers train on Will's human-labeled data only

---

## KEY FILES
| File | Purpose |
|---|---|
| RESONANCE_STATE.md | THIS FILE — read at session start, update at session end |
| docs/BUILD_QUEUE.md | Full build queue with step detail |
| docs/ARCHITECTURE_SPEC.md | 18-head spec (to be created in P1) |
| Resonance_Dataset_Registry.md | Master dataset list (gitignored) |
| scripts/prepare_data_v2.py | Dataset loader (gitignored) |
| scripts/dataset_scout.py | Background dataset scanner |
| scripts/build_training_data.py | Dedup + soft labels + augmentation (to be created in P2) |
| resonance/extractor.py | Extractor |
| resonance/model/confidence_profile.json | Per-class confidence thresholds |

---

## SESSION CLOSE ROUTINE
At the end of every session, Claude will write what changed to this file directly.
You run one command: git add -A && git commit -m "state update" && git push
That's it. Nothing else.

---

## WHAT CLAUDE CAN DO WITHOUT YOU
- Read any file on Shadow PC
- Write any file on Shadow PC
- Edit any file on Shadow PC
- Read GitHub via Chrome MCP
- Check GitHub Actions status

## WHAT ALWAYS NEEDS ONE COMMAND FROM YOU
- git push (authentication)
- Running Python scripts (training, testing)
- Starting/stopping servers
