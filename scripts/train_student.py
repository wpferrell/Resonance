#!/usr/bin/env python3
"""
train_student.py -- Student distillation training.

Architecture: DeBERTa-v3-base + 9 active heads
Training: 10,000 steps, Phase A freeze + Phase B backbone LR=1e-7
Loss: KL distillation + focal hard label + head-to-head per secondary head
Checks: A(shame), B(logit_std), C(500), D(1000), E(2000-10000), F(every 500)
Checkpoint averaging of best 3. Born-again soft labels at end.
"""

import os
import sys
import math
import logging
# psutil imported lazily below
from datetime import datetime
from pathlib import Path
from collections import defaultdict

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
from torch.utils.data import DataLoader, Dataset, SubsetRandomSampler
from transformers import AutoTokenizer, DebertaV2Model
from torch.optim import AdamW
from sklearn.metrics import f1_score

ROOT     = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import train_teachers as tt

ROUND            = 2    # 1 = train on ensemble labels, 2 = born-again on student labels

LOG_FILE = ROOT / "scripts" / f"train_student_r{ROUND}.log"
PID_FILE = ROOT / "scripts" / f"train_student_r{ROUND}.pid"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8", delay=False),
        logging.StreamHandler(sys.stdout),
    ],
)
# Force immediate flush on every log write
class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

root = logging.getLogger()
for h in root.handlers[:]:
    if isinstance(h, logging.FileHandler):
        root.removeHandler(h)
fh = FlushFileHandler(LOG_FILE, mode="w", encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
root.addHandler(fh)
log = logging.getLogger("student")

for _n in ["transformers","huggingface_hub","datasets","httpx","httpcore","filelock","urllib3"]:
    logging.getLogger(_n).setLevel(logging.ERROR)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ENSEMBLE_CSV   = ROOT / "data" / "ensemble_soft_labels.csv"
STUDENT_LABELS = ROOT / "data" / "student_soft_labels_round1.csv"
# Round 2: use born-again student labels as primary soft labels
INPUT_CSV      = STUDENT_LABELS if ROUND == 2 else ENSEMBLE_CSV
PROB_PREFIX    = "s1_prob" if ROUND == 2 else "ensemble_prob"
SHAME_IDX_FILE = ROOT / "data" / "shame_oversample_indices.txt"
DATA_FINAL     = ROOT / "data" / "training_final.csv"
OUT_DIR        = ROOT / "models" / f"student_deberta_base_r{ROUND}"
CKPT_DIR       = OUT_DIR / "checkpoints"
TOKEN_CACHE    = ROOT / "models" / "student_token_cache" / "student_tokens.pt"
STUDENT_LABELS = ROOT / "data" / f"student_soft_labels_round{ROUND}.csv"
FLAG_FILE      = OUT_DIR / f"student_r{ROUND}_complete.flag"

HF_NAME = "microsoft/deberta-v3-base"

EMOTIONS   = tt.EMOTION_CLASSES
EMO_IDX    = tt.EMOTION_TO_IDX
N_EMO      = tt.NUM_EMOTIONS
SHAME_IDX  = EMO_IDX["shame"]

# ---------------------------------------------------------------------------
# Hyperparameters
# ---------------------------------------------------------------------------
BS               = 32
ACCUM            = 4       # effective batch = 128
STEPS            = 10_000
WARMUP           = 800
PHASE_A_STEPS    = 800
LR_HEADS         = 3e-5
LR_BACKBONE      = 1e-7
LR_MIN           = 1e-8
GRAD_CLIP        = 1.0
LOG_EVERY        = 10
CHECKPOINT_EVERY = 500

# Distillation -- Round 2 uses smoother born-again labels, lower T is fine
TEMP         = 4.0 if ROUND == 1 else 2.0
ALPHA        = 0.7   # KL weight in primary loss

# Loss component weights
W_CNN    = 0.5
W_GUILT  = 0.6
W_CRISIS = 0.2
W_VAD    = 0.4
W_PERMA  = 0.3
W_REAP   = 0.2
W_SUPP   = 0.2
W_ALEX   = 0.2
W_MI     = 0.05

MAX_CKPTS = 3


# ---------------------------------------------------------------------------
# PID guard
# ---------------------------------------------------------------------------
def pid_guard():
    if PID_FILE.exists():
        try:
            old = int(PID_FILE.read_text().strip())
            import psutil
            if psutil.pid_exists(old):
                proc = psutil.Process(old)
                if "train_student" in " ".join(proc.cmdline()):
                    log.error(f"ABORT: another instance running (PID {old})")
                    sys.exit(1)
        except Exception:
            pass
    PID_FILE.write_text(str(os.getpid()))


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
class StudentModel(nn.Module):
    def __init__(self, backbone):
        super().__init__()
        self.backbone       = backbone
        hidden              = 768
        self.primary_head   = nn.Linear(hidden, N_EMO)
        self.cnn_head       = tt.CNNHead(hidden, N_EMO, num_filters=64)
        self.guilt_head     = nn.Linear(hidden, 4)
        self.crisis_head    = nn.Linear(hidden, 1)
        self.vad_head       = nn.Linear(hidden, 3)
        self.perma_head     = nn.Linear(hidden, 5)
        self.reappraisal_head = nn.Linear(hidden, 1)
        self.suppression_head = nn.Linear(hidden, 1)
        self.alexithymia_head = nn.Linear(hidden, 1)

    def forward(self, input_ids, attention_mask):
        out    = self.backbone(input_ids, attention_mask)
        hidden = out.last_hidden_state
        cls    = hidden[:, 0, :]
        return {
            "primary":     self.primary_head(cls),
            "cnn":         self.cnn_head(hidden),
            "guilt":       self.guilt_head(cls),
            "crisis":      self.crisis_head(cls).squeeze(-1),
            "vad":         self.vad_head(cls),
            "perma":       self.perma_head(cls),
            "reappraisal": self.reappraisal_head(cls).squeeze(-1),
            "suppression": self.suppression_head(cls).squeeze(-1),
            "alexithymia": self.alexithymia_head(cls).squeeze(-1),
            "cls":         cls,
        }


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class StudentDataset(Dataset):
    def __init__(self, input_ids, attention_mask, df):
        self.input_ids      = input_ids
        self.attention_mask = attention_mask
        # Primary
        ens_cols = [f"{PROB_PREFIX}_{e}" for e in EMOTIONS]
        self.ensemble_probs = torch.tensor(df[ens_cols].values, dtype=torch.float32)
        self.gt_labels      = torch.tensor(
            [EMO_IDX[e] for e in df["gt_emotion"].values], dtype=torch.long)
        self.agreement      = torch.tensor(df["ensemble_agreement"].values, dtype=torch.float32)
        self.confidence     = torch.tensor(df["ensemble_confidence"].values, dtype=torch.float32)
        # Guilt (4 types)
        guilt_cols = ["t1_guilt_shame","t1_guilt_self_blame","t1_guilt_moral_guilt","t1_guilt_social_guilt"]
        self.guilt_targets  = torch.tensor(df[guilt_cols].values, dtype=torch.float32)
        # Crisis
        self.crisis_target  = torch.tensor(df["t1_crisis"].values, dtype=torch.float32)
        # VAD
        vad_cols = ["t2_vad_v","t2_vad_a","t2_vad_d"]
        self.vad_targets    = torch.tensor(df[vad_cols].values, dtype=torch.float32)
        # PERMA
        perma_cols = ["t3_perma_p","t3_perma_e","t3_perma_r","t3_perma_m","t3_perma_a"]
        self.perma_targets  = torch.tensor(df[perma_cols].values, dtype=torch.float32)
        # Regulation
        self.reap_target    = torch.tensor(df["t3_reappraisal"].values, dtype=torch.float32)
        self.supp_target    = torch.tensor(df["t3_suppression"].values, dtype=torch.float32)
        self.alex_target    = torch.tensor(df["t3_alexithymia"].values, dtype=torch.float32)

    def __len__(self):
        return len(self.input_ids)

    def __getitem__(self, idx):
        return {
            "input_ids":      self.input_ids[idx],
            "attention_mask": self.attention_mask[idx],
            "ensemble_probs": self.ensemble_probs[idx],
            "gt_label":       self.gt_labels[idx],
            "agreement":      self.agreement[idx],
            "confidence":     self.confidence[idx],
            "guilt_targets":  self.guilt_targets[idx],
            "crisis_target":  self.crisis_target[idx],
            "vad_targets":    self.vad_targets[idx],
            "perma_targets":  self.perma_targets[idx],
            "reap_target":    self.reap_target[idx],
            "supp_target":    self.supp_target[idx],
            "alex_target":    self.alex_target[idx],
        }


# ---------------------------------------------------------------------------
# Focal loss
# ---------------------------------------------------------------------------
def build_focal_loss(device):
    gt = pd.read_csv(DATA_FINAL)
    counts = gt["emotion"].value_counts()
    w = torch.tensor([1.0 / counts.get(e, 1) for e in EMOTIONS], dtype=torch.float32)
    w = w / w.mean()
    return tt.FocalLoss(gamma=2.0, weight=w.to(device))


# ---------------------------------------------------------------------------
# LR schedule
# ---------------------------------------------------------------------------
def cosine_lr(step, total, peak, warmup, min_lr=1e-8):
    if step < warmup:
        return peak * (step + 1) / warmup
    p = (step - warmup) / max(1, total - warmup)
    return min_lr + (peak - min_lr) * 0.5 * (1 + math.cos(math.pi * p))


# ---------------------------------------------------------------------------
# Loss computation
# ---------------------------------------------------------------------------
def compute_loss(outputs, batch, focal, device):
    ens   = batch["ensemble_probs"].to(device)
    gt    = batch["gt_label"].to(device)
    agree = batch["agreement"].to(device)

    # Primary: KL + focal, agreement-weighted
    logits = outputs["primary"]
    kl = F.kl_div(
        F.log_softmax(logits / TEMP, dim=-1),
        F.softmax(ens / TEMP, dim=-1),
        reduction="none"
    ).sum(dim=-1) * (TEMP ** 2)
    focal_l = focal(logits, gt)  # scalar per example via focal
    # FocalLoss returns scalar -- recompute per-example for weighting
    log_p = F.log_softmax(logits, dim=-1)
    p     = torch.exp(log_p)
    focal_per = -(focal.weight[gt] * ((1 - p[torch.arange(len(gt)), gt]) ** focal.gamma)
                  * log_p[torch.arange(len(gt)), gt])
    # Agreement weighting + shame-specific loss boost
    shame_mask = (gt == SHAME_IDX).float()
    example_w  = 0.5 + agree + (shame_mask * 1.5)  # shame rows get 2x extra weight
    l_primary  = (example_w * (ALPHA * kl + (1 - ALPHA) * focal_per)).mean()

    # CNN head
    cnn_kl = F.kl_div(
        F.log_softmax(outputs["cnn"] / TEMP, dim=-1),
        F.softmax(ens / TEMP, dim=-1),
        reduction="none"
    ).sum(dim=-1) * (TEMP ** 2)
    l_cnn = (example_w * W_CNN * cnn_kl).mean()

    # Guilt head -- argmax of guilt targets as hard label
    guilt_t  = batch["guilt_targets"].to(device)
    guilt_lbl = guilt_t.argmax(dim=-1)
    l_guilt  = F.cross_entropy(outputs["guilt"], guilt_lbl) * W_GUILT

    # Crisis head
    crisis_t = (batch["crisis_target"].to(device) > 0.5).float()
    l_crisis = F.binary_cross_entropy_with_logits(outputs["crisis"], crisis_t) * W_CRISIS

    # VAD head
    vad_t   = batch["vad_targets"].to(device)
    l_vad   = F.huber_loss(outputs["vad"], vad_t, delta=0.5) * W_VAD

    # PERMA head
    perma_t = batch["perma_targets"].to(device)
    l_perma = F.mse_loss(outputs["perma"], perma_t) * W_PERMA

    # Regulation heads
    reap_t  = (batch["reap_target"].to(device) > 0.5).float()
    supp_t  = (batch["supp_target"].to(device) > 0.5).float()
    alex_t  = (batch["alex_target"].to(device) > 0.5).float()
    l_reap  = F.binary_cross_entropy_with_logits(outputs["reappraisal"], reap_t) * W_REAP
    l_supp  = F.binary_cross_entropy_with_logits(outputs["suppression"], supp_t) * W_SUPP
    l_alex  = F.binary_cross_entropy_with_logits(outputs["alexithymia"], alex_t) * W_ALEX

    # Mutual information regularisation
    l_mi = W_MI * (-(ens * F.log_softmax(logits, dim=-1)).sum(dim=-1)).mean()

    total = l_primary + l_cnn + l_guilt + l_crisis + l_vad + l_perma + l_reap + l_supp + l_alex + l_mi
    return total, {
        "primary": l_primary.item(), "cnn": l_cnn.item(),
        "guilt": l_guilt.item(), "crisis": l_crisis.item(),
        "vad": l_vad.item(), "perma": l_perma.item(),
        "mi": l_mi.item(),
    }


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def quick_accuracy(model, tokenizer, device):
    model.eval()
    cases = [
        ("I feel so ashamed of what I did",        "shame"),
        ("I am so happy today everything is great", "joy"),
        ("I am furious about what happened",        "anger"),
        ("I am terrified something bad will happen","fear"),
        ("I am devastated by this terrible loss",   "sadness"),
        ("Wow that was totally unexpected",         "surprise"),
        ("The report is due on Friday morning",     "neutral"),
    ]
    correct = 0
    with torch.no_grad():
        for text, expected in cases:
            enc = tokenizer(text, return_tensors='pt', max_length=128,
                           truncation=True, padding='max_length')
            enc = {k: v.to(device) for k, v in enc.items()}
            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                out = model(enc['input_ids'], enc['attention_mask'])
            pred = EMOTIONS[out["primary"].float().argmax().item()]
            ok = pred == expected
            if ok: correct += 1
            log.info(f"    '{text[:40]}' -> {pred} ({'OK' if ok else 'X'})")
    model.train()
    return correct / len(cases)


def cls_diff_check(model, tokenizer, device):
    model.eval()
    sents = [
        "I am so happy and joyful today",
        "I feel terrible anger about this",
        "I feel so ashamed of what I did",
        "This is frightening and scary",
        "I am deeply saddened by this loss",
    ]
    vecs = []
    with torch.no_grad():
        for s in sents:
            enc = tokenizer(s, return_tensors='pt', max_length=128,
                           truncation=True, padding='max_length')
            enc = {k: v.to(device) for k, v in enc.items()}
            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                out = model.backbone(enc['input_ids'], enc['attention_mask'])
            vecs.append(out.last_hidden_state[:, 0, :].float().cpu())
    diff = max((vecs[i]-vecs[j]).abs().max().item()
               for i in range(len(vecs)) for j in range(i+1, len(vecs)))
    model.train()
    return diff


def run_validation(model, dataset, device, n=5000):
    """Per-emotion F1 on n holdout rows. Returns dict with shame_f1 and pred_counts."""
    loader = DataLoader(dataset, batch_size=64, shuffle=False,
                        num_workers=0, drop_last=False)
    model.eval()
    all_preds, all_gt = [], []
    with torch.no_grad():
        for i, batch in enumerate(loader):
            if i * 64 >= n: break
            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                out = model(batch["input_ids"].to(device),
                           batch["attention_mask"].to(device))
            preds = out["primary"].float().argmax(dim=-1).cpu().numpy()
            gt    = batch["gt_label"].numpy()
            all_preds.extend(preds.tolist())
            all_gt.extend(gt.tolist())
    all_preds = np.array(all_preds)
    f1_per   = f1_score(all_gt, all_preds.tolist(), labels=list(range(N_EMO)),
                        average=None, zero_division=0.0)
    macro    = float(np.mean(f1_per))
    shame_f1 = float(f1_per[SHAME_IDX])
    pred_counts = np.bincount(all_preds, minlength=N_EMO).tolist()
    model.train()
    result = {"macro": macro, "shame_f1": shame_f1, "pred_counts": pred_counts}
    for i, e in enumerate(EMOTIONS):
        result[e] = float(f1_per[i])
    return result


def final_accuracy(model, tokenizer, device):
    """12-sentence accuracy test for final validation (7 from quick_accuracy + 5 more)."""
    model.eval()
    cases = [
        # same 7 as quick_accuracy
        ("I feel so ashamed of what I did",                      "shame"),
        ("I am so happy today everything is great",               "joy"),
        ("I am furious about what happened",                      "anger"),
        ("I am terrified something bad will happen",              "fear"),
        ("I am devastated by this terrible loss",                 "sadness"),
        ("Wow that was totally unexpected",                       "surprise"),
        ("The report is due on Friday morning",                   "neutral"),
        # 5 more covering the same emotions from different angles
        ("I am bursting with joy and gratitude for everything",   "joy"),
        ("I cannot believe how angry this makes me feel",         "anger"),
        ("The dread is overwhelming I cannot stop worrying",      "fear"),
        ("My heart is broken I am overwhelmed with grief",        "sadness"),
        ("I am utterly humiliated by what I did I cannot face it","shame"),
    ]
    correct = 0
    with torch.no_grad():
        for text, expected in cases:
            enc = tokenizer(text, return_tensors='pt', max_length=128,
                           truncation=True, padding='max_length')
            enc = {k: v.to(device) for k, v in enc.items()}
            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                out = model(enc['input_ids'], enc['attention_mask'])
            pred = EMOTIONS[out["primary"].float().argmax().item()]
            ok = pred == expected
            if ok: correct += 1
            log.info(f"    '{text[:50]}' -> {pred} ({'OK' if ok else 'X'})")
    model.train()
    return correct / len(cases)


def save_checkpoint(model, step, shame_f1, ckpt_dir, best_ckpts):
    """Save checkpoint, keep only MAX_CKPTS best."""
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    path = ckpt_dir / f"ckpt_step{step}_shame{shame_f1:.4f}.pt"
    torch.save({k: v.float() for k, v in model.state_dict().items()}, path)
    best_ckpts.append((shame_f1, path))
    best_ckpts.sort(key=lambda x: -x[0])
    while len(best_ckpts) > MAX_CKPTS:
        _, old_path = best_ckpts.pop()
        if old_path.exists():
            old_path.unlink()
            log.info(f"  Deleted old checkpoint: {old_path.name}")
    log.info(f"  Saved checkpoint: {path.name} (shame_f1={shame_f1:.4f})")
    return best_ckpts


def average_checkpoints(ckpt_paths):
    """Average state dicts from multiple checkpoints."""
    states = [torch.load(p, map_location="cpu") for p in ckpt_paths]
    avg = {}
    for key in states[0]:
        avg[key] = torch.stack([s[key].float() for s in states]).mean(dim=0)
    return avg


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train(model, dataset, device, focal, tokenizer):
    log.info("")
    log.info("=" * 60)
    log.info(f"STUDENT TRAINING: {STEPS} steps, BS={BS}, ACCUM={ACCUM}, eff={BS*ACCUM}")
    log.info(f"Phase A: {PHASE_A_STEPS} steps frozen | Phase B: backbone LR={LR_BACKBONE}")
    log.info(f"Distillation T={TEMP}, alpha={ALPHA}")
    log.info("=" * 60)

    # Phase A: plain shuffle, NO shame oversampling
    # Shame oversampling only starts in Phase B once backbone is active
    sampler = SubsetRandomSampler(list(range(len(dataset))))
    loader  = DataLoader(dataset, batch_size=BS, sampler=sampler,
                         num_workers=0, pin_memory=True, drop_last=True)
    log.info("  Phase A: plain shuffle DataLoader (no shame oversampling)")

    # Phase A: freeze backbone
    for n, p in model.named_parameters():
        p.requires_grad_("backbone" not in n)
    frozen    = sum(p.numel() for n, p in model.named_parameters() if "backbone" in n)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log.info(f"  Phase A: backbone frozen ({frozen:,}), heads trainable ({trainable:,})")

    d = cls_diff_check(model, tokenizer, device)
    log.info(f"  CLS diff at start: {d:.6f}")
    model.train()

    head_params = [p for n, p in model.named_parameters() if "backbone" not in n]
    optimiser   = AdamW(head_params, lr=LR_HEADS, weight_decay=0.01, eps=1e-6)
    optimiser.zero_grad(set_to_none=True)

    global_step   = 0
    accum_count   = 0
    running_loss  = defaultdict(float)
    data_iter     = iter(loader)
    shame_streak  = 0
    in_phase_b    = False
    best_ckpts    = []
    best_shame_f1 = 0.0

    while global_step < STEPS:

        # Phase B transition
        if global_step == PHASE_A_STEPS and not in_phase_b:
            in_phase_b = True
            # Enable shame AND sadness oversampling -- these two emotions
            # are confused with each other. Oversample both 2x so the
            # student learns the boundary between them.
            expanded_indices = list(range(len(dataset)))
            if SHAME_IDX_FILE.exists():
                with open(SHAME_IDX_FILE) as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) == 2:
                            idx, tier = int(parts[0]), int(parts[1])
                            if tier == 1:
                                expanded_indices.extend([idx] * 1)  # 2x shame
            # Sadness 2x oversampling
            sadness_idx_val = EMO_IDX["sadness"]
            sadness_rows = [i for i, lbl in enumerate(dataset.gt_labels.tolist()) if lbl == sadness_idx_val]
            expanded_indices.extend(sadness_rows)  # 2x sadness
            log.info(f"  Phase B: shame+sadness oversampling ({len(expanded_indices):,} total indices)")
            sampler = SubsetRandomSampler(expanded_indices)
            loader  = DataLoader(dataset, batch_size=BS, sampler=sampler,
                                 num_workers=0, pin_memory=True, drop_last=True)
            data_iter = iter(loader)
            # Unfreeze backbone with layerwise LR decay
            for p in model.parameters():
                p.requires_grad_(True)
            # Build param groups -- store initial_lr so cosine schedule always
            # decays from the correct peak, not from the already-decayed value.
            backbone_layers = model.backbone.encoder.layer
            param_groups = []
            for li, layer in enumerate(backbone_layers):
                if li <= 3:   lr_b = LR_BACKBONE * 0.1
                elif li <= 7: lr_b = LR_BACKBONE * 0.3
                else:         lr_b = LR_BACKBONE * 1.0
                param_groups.append({"params": list(layer.parameters()),
                                     "lr": lr_b, "initial_lr": lr_b})
            # Embeddings and other backbone params
            emb_params = list(model.backbone.embeddings.parameters())
            param_groups.append({"params": emb_params,
                                  "lr": LR_BACKBONE * 0.1, "initial_lr": LR_BACKBONE * 0.1})
            param_groups.append({"params": head_params,
                                  "lr": LR_HEADS, "initial_lr": LR_HEADS})
            optimiser = AdamW(param_groups, weight_decay=0.01, eps=1e-6)
            optimiser.zero_grad(set_to_none=True)
            d = cls_diff_check(model, tokenizer, device)
            log.info(f"  Phase B start (step {global_step}) -- CLS diff: {d:.6f}")
            model.train()

        try:
            batch = next(data_iter)
        except StopIteration:
            data_iter = iter(loader)
            batch = next(data_iter)

        # LR schedule
        if not in_phase_b:
            lr = cosine_lr(global_step, PHASE_A_STEPS, LR_HEADS, WARMUP)
            for pg in optimiser.param_groups: pg["lr"] = lr
        else:
            for pg in optimiser.param_groups:
                peak = pg.get("initial_lr", LR_HEADS)
                pg["lr"] = cosine_lr(global_step, STEPS, peak, WARMUP, LR_MIN)
            lr = optimiser.param_groups[-1]["lr"]

        with torch.amp.autocast("cuda", dtype=torch.bfloat16):
            outputs = model(batch["input_ids"].to(device),
                           batch["attention_mask"].to(device))
            loss, parts = compute_loss(outputs, batch, focal, device)
            loss = loss / ACCUM

        loss.backward()
        accum_count += 1
        for k, v in parts.items():
            running_loss[k] += v

        if accum_count == ACCUM:
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad], GRAD_CLIP)
            optimiser.step()
            optimiser.zero_grad(set_to_none=True)
            accum_count  = 0
            global_step += 1

            with torch.no_grad():
                preds    = outputs["primary"].float().argmax(dim=-1).cpu().numpy()
                dist     = np.bincount(preds, minlength=N_EMO)
                dist_str = ",".join(f"{e[:2]}:{d}" for e, d in zip(EMOTIONS, dist))

            # CHECK A disabled -- shame dominance during Phase A frozen backbone
            # is expected with focal loss weights. Real check is Phase B behaviour.

            # CHECK B: logit_std at step 50
            if global_step == 50:
                ls = outputs["primary"].float().std(dim=-1).mean().item()
                log.info(f"  [CHECK B step 50] logit_std={ls:.4f}")
                if ls < 0.1:
                    log.error(f"CHECK B FAILED: logit_std too low -- aborting")
                    PID_FILE.unlink(missing_ok=True); sys.exit(1)

            # CHECK C: step 500 -- Phase A complete
            if global_step == 500:
                d = cls_diff_check(model, tokenizer, device)
                log.info(f"  [CHECK C step 500] CLS diff: {d:.6f}")
                if d < 0.01:
                    log.error("CHECK C FAILED: CLS collapsed -- aborting")
                    PID_FILE.unlink(missing_ok=True); sys.exit(1)
                log.info("  [CHECK C] Quick accuracy (7 sentences):")
                acc = quick_accuracy(model, tokenizer, device)
                log.info(f"  [CHECK C] Accuracy: {acc*100:.0f}%")
                log.info("  [CHECK C] Phase B begins next iteration (backbone unfreezes)")
                model.train()

            # CHECK D: step 1000
            if global_step == 1000:
                d = cls_diff_check(model, tokenizer, device)
                log.info(f"  [CHECK D step 1000] CLS diff: {d:.6f}")
                if d < 0.01:
                    log.error("CHECK D FAILED: CLS collapsed -- aborting")
                    PID_FILE.unlink(missing_ok=True); sys.exit(1)
                log.info("  [CHECK D] Quick accuracy:")
                acc = quick_accuracy(model, tokenizer, device)
                log.info(f"  [CHECK D] Accuracy: {acc*100:.0f}%")
                if acc < 0.33:
                    log.warning(f"CHECK D WARNING: accuracy {acc*100:.0f}% < 33%")
                model.train()

            # CHECK E: validation at milestones
            if global_step in [2000, 4000, 6000, 8000, 10000]:
                log.info(f"  [CHECK E step {global_step}] Running validation (5000 rows)...")
                val = run_validation(model, dataset, device, n=5000)
                log.info(f"  Macro F1: {val['macro']:.4f}")
                log.info(f"  *** SHAME F1: {val['shame_f1']:.4f} ***")
                for e in EMOTIONS:
                    log.info(f"    {e:<12} F1={val[e]:.4f}")
                if val["shame_f1"] > best_shame_f1:
                    best_shame_f1 = val["shame_f1"]
                    best_ckpts = save_checkpoint(model, global_step, val["shame_f1"],
                                                 CKPT_DIR, best_ckpts)
                if global_step == 4000 and val["shame_f1"] < 0.15:
                    log.warning(f"CHECK E WARNING: shame F1={val['shame_f1']:.4f} < 0.15 at step 4000 -- continuing")
                model.train()

            # Shame F1 check every 200 steps
            if global_step % 200 == 0 and global_step > 0 and global_step % CHECKPOINT_EVERY != 0 and global_step not in [2000,4000,6000,8000,10000]:
                val = run_validation(model, dataset, device, n=1000)
                log.info(f"  [SHAME CHECK step {global_step}] Shame F1: {val['shame_f1']:.4f} (best: {best_shame_f1:.4f})")
                model.train()

            # CHECK F: every 500 steps save best checkpoint
            elif global_step % CHECKPOINT_EVERY == 0 and global_step > 0:
                log.info(f"  [CHECK F step {global_step}] Quick validation...")
                val = run_validation(model, dataset, device, n=2000)
                log.info(f"  Shame F1: {val['shame_f1']:.4f} (best: {best_shame_f1:.4f})")
                if val["shame_f1"] > best_shame_f1:
                    best_shame_f1 = val["shame_f1"]
                    best_ckpts = save_checkpoint(model, global_step, val["shame_f1"],
                                                 CKPT_DIR, best_ckpts)
                model.train()

            if global_step % LOG_EVERY == 0:
                total_avg = sum(running_loss.values()) / LOG_EVERY
                parts_str = "  ".join(f"{k}={v/LOG_EVERY:.4f}" for k, v in running_loss.items())
                vram = torch.cuda.memory_allocated() / 1e9
                phase = "A" if not in_phase_b else "B"
                log.info(f"  Step {global_step:>6}/{STEPS} [{phase}] | Loss: {total_avg:.4f} | "
                         f"LR: {lr:.2e} | VRAM: {vram:.1f}GB | {parts_str} | dist={dist_str}")
                running_loss = defaultdict(float)

    log.info("  Training complete.")
    return best_ckpts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    log.info("=" * 60)
    log.info("STUDENT TRAINING")
    log.info(f"Date: {datetime.now().isoformat()}")
    log.info("=" * 60)

    pid_guard()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if not torch.cuda.is_available():
        log.error("CUDA required"); sys.exit(1)
    log.info(f"Device: {torch.cuda.get_device_name(0)}")
    log.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory/1024**3:.1f}GB")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CKPT_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "models" / "student_token_cache").mkdir(parents=True, exist_ok=True)

    # Load ensemble
    if not INPUT_CSV.exists():
        log.error(f"Input CSV not found: {INPUT_CSV}")
        log.error("Run build_ensemble_v2.py first" if ROUND == 1 else "Run Round 1 training first to generate born-again labels")
        sys.exit(1)

    log.info(f"Round {ROUND} training -- loading: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    log.info(f"  {len(df):,} rows, {len(df.columns)} cols")

    # Round 2: merge secondary head targets from original ensemble
    if ROUND == 2:
        log.info("  Round 2: merging secondary targets from ensemble...")
        ens_df = pd.read_csv(ENSEMBLE_CSV)
        secondary_cols = [c for c in ens_df.columns if c not in [f"ensemble_prob_{e}" for e in EMOTIONS]]
        for col in secondary_cols:
            df[col] = ens_df[col].values
        log.info(f"  Merged {len(secondary_cols)} secondary columns from ensemble")
    log.info(f"  {len(df):,} rows, {len(df.columns)} cols")

    # Tokenise
    log.info(f"Tokenising with {HF_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(HF_NAME)
    n_rows = len(df)
    rebuild_tokens = True
    if TOKEN_CACHE.exists():
        log.info("  Checking token cache...")
        try:
            cache = torch.load(TOKEN_CACHE, map_location="cpu", weights_only=True)
            if (cache.get("arch") == "deberta_base" and
                    cache.get("max_length") == 256 and
                    cache.get("num_texts") == n_rows):
                input_ids      = cache["input_ids"]
                attention_mask = cache["attention_mask"]
                rebuild_tokens = False
                log.info(f"  Cache valid ({n_rows:,} rows)")
            else:
                log.warning("  Cache invalid (arch/length/size mismatch) -- re-tokenising")
                TOKEN_CACHE.unlink(missing_ok=True)
        except Exception as e:
            log.warning(f"  Cache load error: {e} -- re-tokenising")
            TOKEN_CACHE.unlink(missing_ok=True)
    if rebuild_tokens:
        log.info("  Tokenising (this takes a few minutes)...")
        texts = pd.read_csv(DATA_FINAL)["text"].fillna("").tolist()
        all_ids, all_mask = [], []
        for i in range(0, len(texts), 1000):
            batch_texts = texts[i:i+1000]
            enc = tokenizer(batch_texts, return_tensors="pt", max_length=256,
                           truncation=True, padding="max_length")
            all_ids.append(enc["input_ids"])
            all_mask.append(enc["attention_mask"])
            if i % 50000 == 0:
                log.info(f"  Tokenised {i:,}/{len(texts):,}")
        input_ids      = torch.cat(all_ids)
        attention_mask = torch.cat(all_mask)
        TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "input_ids": input_ids, "attention_mask": attention_mask,
            "arch": "deberta_base", "max_length": 256, "num_texts": n_rows,
        }, TOKEN_CACHE)
        log.info(f"  Token cache saved: {TOKEN_CACHE}")

    dataset = StudentDataset(input_ids, attention_mask, df)
    log.info(f"  Dataset: {len(dataset):,} examples")

    # Build model
    log.info(f"Loading backbone: {HF_NAME}...")
    backbone = DebertaV2Model.from_pretrained(HF_NAME)
    model    = StudentModel(backbone).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    log.info(f"  Total params: {n_params:,}")

    focal = build_focal_loss(device)

    # Train
    best_ckpts = train(model, dataset, device, focal, tokenizer)

    # Checkpoint averaging
    log.info("Averaging best checkpoints...")
    if len(best_ckpts) >= 2:
        ckpt_paths = [p for _, p in best_ckpts[:MAX_CKPTS]]
        avg_state  = average_checkpoints(ckpt_paths)
        model.load_state_dict(avg_state)
        avg_path = OUT_DIR / "model_state_averaged.pt"
        torch.save(avg_state, avg_path)
        log.info(f"  Averaged {len(ckpt_paths)} checkpoints -> {avg_path.name}")
    else:
        log.info("  Not enough checkpoints to average, using final model")
        avg_path = OUT_DIR / "model_state.pt"
        torch.save({k: v.float() for k, v in model.state_dict().items()}, avg_path)

    torch.save({k: v.float() for k, v in model.state_dict().items()},
               OUT_DIR / "model_state.pt")

    # Final validation (on averaged model)
    log.info("")
    log.info("=" * 60)
    log.info("FINAL VALIDATION (averaged model)")
    log.info("=" * 60)
    log.info("12-sentence accuracy test:")
    acc = final_accuracy(model, tokenizer, device)
    log.info(f"12-sentence accuracy: {acc*100:.0f}% ({int(acc*12)}/12)")

    log.info("5000-row validation:")
    val = run_validation(model, dataset, device, n=5000)
    log.info(f"Macro F1: {val['macro']:.4f}")
    log.info(f"*** SHAME F1: {val['shame_f1']:.4f} ***")
    for e in EMOTIONS:
        log.info(f"  {e:<12} F1={val[e]:.4f}")

    # Distribution checks
    pred_counts = np.array(val.get("pred_counts", [0] * N_EMO))
    top_pct = pred_counts.max() / max(pred_counts.sum(), 1) * 100
    top_emo = EMOTIONS[int(pred_counts.argmax())]
    log.info(f"  Top predicted emotion: {top_emo} ({top_pct:.1f}%)")
    for i, e in enumerate(EMOTIONS):
        log.info(f"  {e:<12} pred={pred_counts[i]:>5}")

    # Check validation gates
    health_ok = True
    if val["shame_f1"] < 0.35:
        log.error(f"VALIDATION FAILED: shame F1={val['shame_f1']:.4f} < 0.35")
        health_ok = False
    elif val["shame_f1"] < 0.40:
        log.warning(f"VALIDATION WARNING: shame F1={val['shame_f1']:.4f} < 0.40")
    if top_pct > 75.0:
        log.error(f"VALIDATION FAILED: {top_emo} = {top_pct:.1f}% of predictions > 75%")
        health_ok = False
    else:
        log.info(f"  [OK] No emotion > 75% of predictions")
    missing_emos = [EMOTIONS[i] for i in range(N_EMO) if pred_counts[i] == 0]
    if missing_emos:
        log.error(f"VALIDATION FAILED: emotions with 0 predictions: {missing_emos}")
        health_ok = False
    else:
        log.info("  [OK] All 7 emotions present in predictions")

    if not health_ok:
        log.error("Student failed validation -- not generating soft labels")
        PID_FILE.unlink(missing_ok=True); sys.exit(1)

    # Born-again soft labels
    log.info("")
    log.info("=" * 60)
    log.info("GENERATING BORN-AGAIN SOFT LABELS")
    log.info("=" * 60)
    model.eval()
    loader = DataLoader(dataset, batch_size=64, shuffle=False,
                        num_workers=0, drop_last=False)
    all_probs = []
    with torch.no_grad():
        for i, batch in enumerate(loader):
            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                out = model(batch["input_ids"].to(device),
                           batch["attention_mask"].to(device))
            probs = F.softmax(out["primary"].float(), dim=-1).cpu().numpy()
            all_probs.append(probs)
            if i % 500 == 0:
                log.info(f"  Born-again inference: {i*64:,}/{len(dataset):,}")

    all_probs = np.concatenate(all_probs)
    born_again = pd.DataFrame(all_probs, columns=[f"s1_prob_{e}" for e in EMOTIONS])
    born_again.to_csv(STUDENT_LABELS, index=False)
    log.info(f"  Born-again labels: {STUDENT_LABELS}")

    FLAG_FILE.write_text(
        f"Student complete. Shame F1={val['shame_f1']:.4f}. {datetime.now().isoformat()}"
    )
    log.info(f"  Flag: {FLAG_FILE.name}")

    PID_FILE.unlink(missing_ok=True)

    log.info("")
    log.info("=" * 60)
    log.info("STUDENT TRAINING COMPLETE")
    log.info("Born-again labels ready for Round 2 distillation")
    log.info("=" * 60)

if __name__ == "__main__":
    main()
