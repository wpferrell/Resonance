# Resonance — Complete Build Queue
# LOCKED — April 2026
# This is the authoritative build queue.
# Nothing moves forward until the current step is working and verified.
# Update this file when a step is completed — mark it done with ~~strikethrough~~.

---

## PHASE 1 — Design (no code — lock everything on paper first)

**Goal:** Every architectural decision is written and locked before a single line of training code is written.

### Step 1 — Lock 18-head student architecture
Write ARCHITECTURE_SPEC.md covering:
- All 18 active output heads — what each outputs, what loss function, what training target
- Which teacher generates soft labels for which head
- 2 encoder objectives — contrastive shame separation + domain adversarial training
- 3 teachers — DeBERTa-v3-large+CNN, XLNet-large, ELECTRA-large
- Student — DeBERTa-v3-base, 86M, 768 dims, 12 layers
- VAD target generation method (NRC token-level scoring on training data)
- Auxiliary label generation method (apply extractor rules offline to training data)

**Done when:** ARCHITECTURE_SPEC.md exists on disk, is complete, and has been reviewed.

### Step 2 — Lock validation criteria
Write into ARCHITECTURE_SPEC.md exactly what "working" means before moving to the next phase:
- After Phase 3: all 6 frameworks correct on 20+ real sentences, trajectory reads correctly across 5-message simulation
- After teacher training: soft label agreement >0.6 on shame, distributions within 10% across teachers on majority classes
- After student training: shame F1 >0.60 (baseline 0.455), all 18 heads produce non-null output, VAD in expected range per emotion
- After Phase 5: end-to-end message → extractor → EmotionResult → all new fields populated → feedback drains to Pi → Pi stats page shows new fields

**Done when:** Validation criteria written into ARCHITECTURE_SPEC.md and reviewed.

---

## PHASE 2 — Data Pipeline

**Goal:** One clean unified training file with deduplication, soft labels, and augmentation. Ready for teachers to train on.

### Step 3 — Reddit MH MDPI local file
~~Add Reddit MH MDPI + SWMH to Registry and script~~ *(done — Registry v8, script v6)*
Pending: download `reddit_mh_mdpi_800.csv` from paper supplementary materials to `data/raw/reddit_mh_mdpi_800.csv`.

**Done when:** File exists at that path and `prepare_data_v2.py` loads it without skipping.

### Step 4 — Scout results reviewed
~~Review scout_results.md~~ *(done — April 2026, zero entries pass all 7 rules, documented)*

**Done when:** Already done. Re-check when scout finds new FOUND/BORDERLINE entries.

### Step 5 — Build unified build_training_data.py
File: `scripts/build_training_data.py`
Three steps in one script, run in sequence:

**Step A — Deduplication**
- Run prepare_data_v2.py to produce data/training.csv
- Hash every (text, emotion) pair
- Remove exact duplicates across all 29 datasets
- Log how many rows removed per dataset
- Output: data/training_dedup.csv

**Step B — Soft labels**
- For every row in training_dedup.csv:
  - Score text with NRC VAD Lexicon token by token → derive V, A, D targets
  - Score text with NRC affect frequencies → derive soft emotion distribution
  - Apply extractor rules offline → derive auxiliary binary labels (reappraisal, suppression, crisis, alexithymia, guilt_type)
  - Score text with PERMA lexicon → derive 5 PERMA targets
- Output: data/soft_labels.csv (one row per training example, all targets)

**Step C — Back-translation augmentation (shame and guilt only)**
- Filter training_dedup.csv for emotion == "shame"
- Translate each row: English → French → English (using Helsinki-NLP opus-mt models, no API needed)
- Verify round-trip preserved meaning (BLEU score > 0.6)
- Append augmented rows to training_dedup.csv
- Log augmentation count
- Output: data/training_final.csv (original + augmented shame/guilt rows)

**Done when:** Script runs end to end, produces training_final.csv and soft_labels.csv, logs show row counts per step, no errors.

---

## PHASE 3 — Extractor Framework Signals

**Goal:** All 6 detection frameworks producing real scored output from the extractor. Validated on real text before any training starts.

Build order is locked. Do not reorder.

### Step 6 — PERMA
- Connect proprietary PERMA lexicon to extractor
- Add 5 new scored float fields to EmotionResult: perma_p, perma_e, perma_r, perma_m, perma_a
- Each field scores the message on that PERMA dimension [0, 1]
- **Done when:** 5 PERMA fields appear in EmotionResult output with non-zero values on clearly positive/meaningful text

### Step 7 — SDT
- Add 3 new scored float fields to EmotionResult: autonomy_signal, competence_signal, relatedness_signal
- Detect autonomy language (agency words, choice language, control language)
- Detect competence language (mastery words, skill language, achievement language)
- Detect relatedness language (connection words, belonging language, isolation language)
- **Done when:** 3 SDT fields appear in EmotionResult, relatedness_signal is high on clearly lonely text, autonomy_signal is high on clearly agency-expressing text

### Step 8 — WoT trajectory
- Existing WoT detects per-message state (hyper/in/hypo) — this step adds session-level trajectory
- Track WoT state across messages in a session
- Add wot_trajectory field to EmotionResult: "escalating", "stable", "deescalating"
- **Done when:** wot_trajectory changes correctly across a simulated 5-message sequence going from calm → overwhelmed

### Step 9 — Secondary emotion independence
- Currently secondary emotion is inferred from primary via SECONDARY_MAP lookup
- Replace with parallel detection: secondary emotion detected from text independently of primary
- Primary and secondary can now differ (e.g., primary=anger, secondary=grief — both present simultaneously)
- **Done when:** A sentence expressing two simultaneous emotions returns different primary and secondary

### Step 10 — Reappraisal/suppression scored floats
- Currently reappraisal_signal and suppression_signal are booleans
- Convert to scored floats: reappraisal_score [0,1], suppression_score [0,1]
- Add suppression score to distress trajectory: high suppression + negative valence → escalate sustained distress signal
- **Done when:** reappraisal_score and suppression_score return graded values, not just 0/1

### Step 11 — Wise Mind scored float
- Currently wise_mind_signal is a boolean
- Convert to wise_mind_score [0,1]
- Score reflects degree of balanced/integrated thinking, not just presence/absence
- **Done when:** wise_mind_score returns graded values on sentences expressing varying degrees of emotional integration

### Step 12 — Ethics safeguards revision
- Update sustained_distress trigger to factor in suppression_score and wot_trajectory
- High suppression + escalating WoT trajectory should trigger sustained_distress sooner
- Update ETHICS.md to document revised trigger conditions
- **Done when:** Simulated suppression + escalating WoT session triggers sustained_distress at correct point

### Step 13 — Trajectory layer
- Add trajectory field to EmotionResult: overall direction of travel across all 6 frameworks per session
- Combines: valence trend + WoT trajectory + suppression trend + PERMA trend
- Values: "improving", "stable", "declining"
- **Done when:** Trajectory reads correctly across simulated sessions going in each direction

### Step 14 — MLE emoji lexicon
- Replace crude EMOJI_MAP dict in extractor with Multidimensional Lexicon of Emojis (Godard & Holtzman 2022)
- 359 emojis rated on 8 NRC emotion dimensions
- CC-BY license — commercially clean
- **Done when:** Emoji detection uses MLE scores, not hardcoded map. More emojis covered. Output more nuanced.

### PHASE 3 VALIDATION CHECKPOINT
Before moving to Phase 4:
- Test all 6 frameworks on minimum 20 real sentences
- Verify every new EmotionResult field returns non-null output
- Simulate a 5-message session and verify trajectory reads correctly
- No exceptions, no silent failures

**Done when:** All tests pass and are documented.

---

## PHASE 4 — Train

**Goal:** 3 trained teachers producing quality soft labels, then 1 trained student with all 18 heads working.

### Step 15 — DAPT
- Domain-adaptive pretraining on full 29-dataset stack (~1.48M examples)
- Continue pretraining DeBERTa-v3-base on masked language modelling before any classification heads are added
- Adapts encoder to emotional expression domain before distillation
- Script: `scripts/run_dapt.py`
- **Done when:** DAPT completes, loss curve shows convergence, adapted weights saved

### Step 16 — Train 3 teachers
- Script: `scripts/train_teachers.py`
- Teacher 1: DeBERTa-v3-large + CNN head — trains on full stack, specialises in shame/guilt/local patterns
- Teacher 2: XLNet-large — trains on full stack, specialises in anger/contextual dependencies
- Teacher 3: ELECTRA-large — trains on full stack, specialises in fear/efficient signal
- All teachers generate soft label probability distributions across all 18 output types
- Ensemble script combines with confidence weighting + temperature scaling → one soft label file per training example
- **Done when:** All 3 teachers trained, soft_labels_ensemble.csv produced

### PHASE 4 VALIDATION CHECKPOINT (teacher quality)
Before training student:
- Soft label agreement >0.6 on shame class across all 3 teachers
- Label distributions within 10% of each other on majority classes (joy, sadness, anger, fear)
- Sample 100 rows manually and verify soft labels look correct

**Done when:** All checks pass and are documented.

### Step 17 — Multi-task loss weighting
- Balance loss weights across all 18 heads so no single head dominates gradient signal
- Focal loss on shame and guilt specifically
- Shame class weight ~17x (from existing confidence_profile.json analysis)
- **Done when:** Loss weights documented in ARCHITECTURE_SPEC.md and confirmed before training starts

### Step 18 — Train student
- Script: `scripts/train_student.py`
- Student: DeBERTa-v3-base, 18 heads, all training objectives
- Trains on: hard labels + teacher ensemble soft labels + auxiliary labels + VAD targets + PERMA targets
- 2 encoder objectives active: contrastive shame separation + domain adversarial training
- **Done when:** Student training completes, all 18 heads produce output, model saved

### Step 19 — Confidence profile update
- Run extractor on held-out validation set using new student
- Update confidence_profile.json to capture per-class confidence thresholds for all 18 heads
- **Done when:** Updated confidence_profile.json saved, shame confidence floor updated

### PHASE 4 VALIDATION CHECKPOINT (student quality)
Before Phase 5:
- Shame F1 > 0.60 (baseline ModernBERT: 0.455)
- All 18 heads produce non-null output on real text
- VAD outputs within expected range per emotion class
- No head returning constant output (collapsed training)

**Done when:** All checks pass and are documented.

---

## PHASE 5 — Integrate

**Goal:** New model drives all output. Extractor becomes a translator. Feedback and storage capture everything. End-to-end test passes.

### Step 20 — Extractor refactor
- Model now owns all output — VAD lookup table retired entirely, no fallback
- Extractor reads model output for: primary emotion, VAD, secondary emotion, reappraisal/suppression scores, wise mind score, WoT state, PERMA scores, crisis, alexithymia, guilt type, SDT signals
- Extractor continues to handle: session-level trajectory, sustained distress counter, outward reflection (session-level, not per-message model outputs)
- **Done when:** Extractor produces correct EmotionResult from model output only, no rule-based fallback for model-owned fields

### Step 21 — Feedback system verify
- Verify all new EmotionResult fields drain correctly to Pi server
- Update feedback payload schema to include all new fields
- Verify Pi stats page displays new fields
- **Done when:** End-to-end test: message → process() → all 18 head outputs in EmotionResult → feedback payload → Pi stats shows new fields

### Step 22 — Storage update
- Update Qdrant schema to capture all new EmotionResult vector fields
- Update SurrealDB schema to capture all new EmotionResult fields per message
- Verify existing stored records are not broken
- **Done when:** New fields stored correctly, retrievable, no schema errors

### Step 23 — Pi server update
- Add trajectory endpoint to Pi server
- Add export pipeline for model retraining (feedback data → training examples)
- **Done when:** Trajectory endpoint live at feedback.resonance-layer.com/trajectory, export pipeline tested

### Step 24 — Attachment inference layer
- Builds silently from SDT relatedness, suppression score, and WoT trajectory across 10+ sessions
- Never claimed directly — inferred and used to weight LLM context injection
- **Done when:** After 10+ simulated sessions, attachment pattern detectable and influencing context injection correctly

### PHASE 5 VALIDATION CHECKPOINT (full end-to-end)
- Send a real message through the full stack
- Verify: message → extractor → all 18 head outputs populated → feedback payload correct → Pi receives it → Pi stats page updated → storage records complete
- No silent failures anywhere in the chain

**Done when:** All checks pass and are documented. Version bumped, new model uploaded to HuggingFace, new PyPI version published.

---

## PHASE 6 — ONNX (PARKED)

Do not start until Phases 1–5 are complete and validated.

Order when ready:
1. GatedBias (300 params per user)
2. ORT on-device head training (frozen encoder)
3. LoRA adapters (280KB per user)
4. Trajectory embedding model (tiny LSTM on stored CLS vectors)
5. ATLAS gradient-free orchestration memory
6. Federated delta aggregation via Pi server

Full stack adds ~38MB files, ~190MB RAM, ~7–8ms latency over base ONNX.

---

## Key files

| File | Purpose |
|---|---|
| `docs/BUILD_QUEUE.md` | This file — authoritative build queue |
| `docs/ARCHITECTURE_SPEC.md` | 18-head spec, loss functions, validation criteria |
| `Resonance_Dataset_Registry.md` | Master dataset list (gitignored, local only) |
| `scripts/prepare_data_v2.py` | Dataset loader (gitignored, local only) |
| `scripts/build_training_data.py` | Dedup + soft labels + augmentation |
| `scripts/run_dapt.py` | Domain-adaptive pretraining |
| `scripts/train_teachers.py` | Train 3 teacher models |
| `scripts/train_student.py` | Train student with 18 heads |
| `resonance/extractor.py` | Extractor — updated each Phase 3 step |
| `resonance/model/confidence_profile.json` | Per-class confidence thresholds |

---

*Last updated: April 2026*
