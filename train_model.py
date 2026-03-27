# Resonance — Step 5B: Train the emotion model
# Fine-tunes NeoBERT on 1.3M emotion examples
# Output: resonance/model/ — your trained model, ready to use

import os
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.model_selection import train_test_split
import json

# ── Configuration ──────────────────────────────────────────────
DATA_PATH   = "data/training.csv"
MODEL_OUT   = "resonance/model"
BASE_MODEL  = "answerdotai/ModernBERT-base"
MAX_LEN     = 128
BATCH_SIZE  = 32
EPOCHS      = 3
LR          = 2e-5
SEED        = 42

# ── Load data ──────────────────────────────────────────────────
print("Loading training data...")
df = pd.read_csv(DATA_PATH)
print(f"  Rows loaded: {len(df):,}")

# Keep only rows with text and label
df = df.dropna(subset=["text", "emotion"])
df["text"] = df["text"].astype(str).str.strip()
df = df[df["text"].str.len() > 2]
print(f"  Rows after cleanup: {len(df):,}")

# ── Encode labels ──────────────────────────────────────────────
le = LabelEncoder()
df["label_id"] = le.fit_transform(df["emotion"])
num_labels = len(le.classes_)
print(f"  Emotion classes ({num_labels}): {list(le.classes_)}")

# Save label mapping so extractor.py can use it
os.makedirs(MODEL_OUT, exist_ok=True)
label_map = {int(i): str(label) for i, label in enumerate(le.classes_)}
with open(f"{MODEL_OUT}/label_map.json", "w") as f:
    json.dump(label_map, f, indent=2)
print(f"  Label map saved to {MODEL_OUT}/label_map.json")

# ── Train / validation split ───────────────────────────────────
train_df, val_df = train_test_split(
    df, test_size=0.05, random_state=SEED, stratify=df["label_id"]
)
print(f"  Training rows:   {len(train_df):,}")
print(f"  Validation rows: {len(val_df):,}")

# ── Tokenizer ──────────────────────────────────────────────────
print(f"\nLoading tokenizer: {BASE_MODEL}")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

# ── Dataset class ──────────────────────────────────────────────
class EmotionDataset(Dataset):
    def __init__(self, texts, labels):
        self.encodings = tokenizer(
            list(texts),
            truncation=True,
            padding=True,
            max_length=MAX_LEN,
            return_tensors="pt"
        )
        self.labels = torch.tensor(list(labels), dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return {
            "input_ids":      self.encodings["input_ids"][idx],
            "attention_mask": self.encodings["attention_mask"][idx],
            "labels":         self.labels[idx]
        }

print("Tokenizing training data (this takes a few minutes)...")
train_dataset = EmotionDataset(train_df["text"].values, train_df["label_id"].values)
print("Tokenizing validation data...")
val_dataset   = EmotionDataset(val_df["text"].values,   val_df["label_id"].values)
print("Tokenization complete.")

# ── Model ──────────────────────────────────────────────────────
print(f"\nLoading model: {BASE_MODEL}")
model = AutoModelForSequenceClassification.from_pretrained(
    BASE_MODEL,
    num_labels=num_labels,
    ignore_mismatched_sizes=True
)

# ── Metrics ────────────────────────────────────────────────────
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro", zero_division=0)
    }

# ── Training arguments ─────────────────────────────────────────
args = TrainingArguments(
    output_dir=MODEL_OUT,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=64,
    learning_rate=LR,
    warmup_ratio=0.1,
    weight_decay=0.01,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1_macro",
    logging_steps=500,
    fp16=True,
    seed=SEED,
    report_to="none"
)

# ── Train ──────────────────────────────────────────────────────
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
)

print("\n" + "="*50)
print("STARTING TRAINING")
print(f"  Device: {torch.cuda.get_device_name(0)}")
print(f"  Training rows: {len(train_dataset):,}")
print(f"  Epochs: {EPOCHS}")
print(f"  Batch size: {BATCH_SIZE}")
print("="*50 + "\n")

trainer.train()

# ── Save final model ───────────────────────────────────────────
print("\nSaving model...")
trainer.save_model(MODEL_OUT)
tokenizer.save_pretrained(MODEL_OUT)
print(f"Model saved to {MODEL_OUT}/")

# ── Final evaluation ───────────────────────────────────────────
print("\nRunning final evaluation...")
preds_output = trainer.predict(val_dataset)
preds = np.argmax(preds_output.predictions, axis=1)
labels = val_df["label_id"].values

print("\n" + "="*50)
print("TRAINING COMPLETE — RESULTS")
print("="*50)
print(classification_report(labels, preds, target_names=le.classes_))
print(f"Overall accuracy: {accuracy_score(labels, preds):.4f}")
print(f"Macro F1 score:   {f1_score(labels, preds, average='macro', zero_division=0):.4f}")
print(f"\nModel saved to: {MODEL_OUT}/")
print("Ready for Step 5C.")
