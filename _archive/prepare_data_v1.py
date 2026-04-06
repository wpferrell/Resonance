"""
Resonance - Step 5A: Dataset Preparation — FINAL COMPLETE
29 verified datasets combined.
Outputs: data/training.csv with columns: text, emotion
"""

import os
import csv
import json
import re
import pandas as pd
from datasets import load_dataset

OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "training.csv")
RAW_DIR = "data/raw"

EMOTION_MAP = {
    "joy": "joy", "happiness": "joy", "happy": "joy", "joyful": "joy",
    "excitement": "joy", "amusement": "joy", "love": "joy", "optimism": "joy",
    "delight": "joy", "grateful": "joy", "excited": "joy", "hopeful": "joy",
    "proud": "joy", "trusting": "joy", "content": "joy", "caring": "joy",
    "faithful": "joy", "confident": "joy", "impressed": "joy",
    "enthusiasm": "joy", "euphoria": "joy", "pride": "joy",
    "empathy": "joy", "desire": "joy", "peaceful": "joy", "powerful": "joy",
    "relief": "joy", "fun": "joy", "gratitude": "joy", "admiration": "joy",
    "approval": "joy",
    "sadness": "sadness", "sad": "sadness", "grief": "sadness",
    "disappointment": "sadness", "melancholy": "sadness", "sentimental": "sadness",
    "nostalgic": "sadness", "lonely": "sadness", "devastated": "sadness",
    "stress": "sadness", "boredom": "sadness", "empty": "sadness",
    "disapproval": "sadness",
    "anger": "anger", "angry": "anger", "annoyance": "anger",
    "disgust": "anger", "rage": "anger", "frustration": "anger",
    "furious": "anger", "jealous": "anger", "hate": "anger", "mad": "anger",
    "fear": "fear", "anxiety": "fear", "nervousness": "fear",
    "worry": "fear", "dread": "fear", "terrified": "fear",
    "afraid": "fear", "apprehensive": "fear", "anxious": "fear",
    "scared": "fear",
    "surprise": "surprise", "realization": "surprise",
    "amazement": "surprise", "surprised": "surprise",
    "anticipating": "surprise", "curiosity": "surprise",
    "shame": "shame", "guilt": "shame", "embarrassment": "shame",
    "remorse": "shame", "ashamed": "shame", "guilty": "shame",
    "neutral": "neutral", "none": "neutral", "prepared": "neutral",
    "no emotion": "neutral", "others": "neutral", "peace": "neutral",
    "trust": "neutral",
}

CARER_LABELS = ["sadness", "joy", "love", "anger", "fear", "surprise"]
TWEET_EVAL_LABELS = ["anger", "joy", "optimism", "sadness"]

def normalize_emotion(label):
    if label is None:
        return None
    label = str(label).lower().strip()
    return EMOTION_MAP.get(label, None)

def write_row(writer, text, emotion):
    if not text or not emotion:
        return 0
    emotion = normalize_emotion(emotion)
    if not emotion:
        return 0
    text = str(text).strip()
    if len(text) < 3:
        return 0
    writer.writerow({"text": text, "emotion": emotion})
    return 1

# ── HUGGINGFACE DATASETS ─────────────────────────────────────

def load_goemotions(writer):
    print("Loading GoEmotions (58K)...")
    count = 0
    try:
        ds = load_dataset("google-research-datasets/go_emotions", "simplified")
        label_names = ds["train"].features["labels"].feature.names
        for split in ds.keys():
            for row in ds[split]:
                if row["labels"]:
                    count += write_row(writer, row["text"], label_names[row["labels"][0]])
        print(f"  GoEmotions: {count}")
    except Exception as e:
        print(f"  GoEmotions FAILED: {e}")
    return count

def load_carer(writer):
    print("Loading CARER unsplit (416K)...")
    count = 0
    try:
        ds = load_dataset("dair-ai/emotion", "unsplit")
        for split in ds.keys():
            for row in ds[split]:
                count += write_row(writer, row["text"], CARER_LABELS[row["label"]])
        print(f"  CARER: {count}")
    except Exception as e:
        print(f"  CARER FAILED: {e}")
    return count

def load_empathetic(writer):
    print("Loading EmpatheticDialogues (24K)...")
    count = 0
    try:
        ds = load_dataset("bdotloh/empathetic-dialogues-contexts")
        for split in ds.keys():
            for row in ds[split]:
                count += write_row(writer, row.get("situation", ""), row.get("emotion", ""))
        print(f"  EmpatheticDialogues: {count}")
    except Exception as e:
        print(f"  EmpatheticDialogues FAILED: {e}")
    return count

def load_isear(writer):
    print("Loading ISEAR (7.5K)...")
    count = 0
    try:
        ds = load_dataset("gsri-18/ISEAR-dataset-complete")
        for split in ds.keys():
            for row in ds[split]:
                count += write_row(writer, row.get("content", ""), row.get("emotion", ""))
        print(f"  ISEAR: {count}")
    except Exception as e:
        print(f"  ISEAR FAILED: {e}")
    return count

def load_boltuix(writer):
    print("Loading Boltuix emotions (131K)...")
    count = 0
    try:
        ds = load_dataset("boltuix/emotions-dataset")
        for split in ds.keys():
            for row in ds[split]:
                count += write_row(writer, row.get("Sentence", ""), row.get("Label", ""))
        print(f"  Boltuix: {count}")
    except Exception as e:
        print(f"  Boltuix FAILED: {e}")
    return count

def load_super_emotion(writer):
    print("Loading SuperEmotion (552K)...")
    count = 0
    try:
        ds = load_dataset("cirimus/super-emotion")
        for split in ds.keys():
            for row in ds[split]:
                if row.get("labels_str"):
                    label = row["labels_str"][0]
                    count += write_row(writer, row.get("text", ""), label)
        print(f"  SuperEmotion: {count}")
    except Exception as e:
        print(f"  SuperEmotion FAILED: {e}")
    return count

def load_tweet_eval(writer):
    print("Loading TweetEval emotion (7K)...")
    count = 0
    try:
        ds = load_dataset("cardiffnlp/tweet_eval", "emotion")
        for split in ds.keys():
            for row in ds[split]:
                count += write_row(writer, row.get("text", ""), TWEET_EVAL_LABELS[row["label"]])
        print(f"  TweetEval: {count}")
    except Exception as e:
        print(f"  TweetEval FAILED: {e}")
    return count

def load_emotion_balanced(writer):
    print("Loading emotion-balanced (20K)...")
    count = 0
    try:
        ds = load_dataset("AdamCodd/emotion-balanced")
        label_names = ["sadness", "joy", "love", "anger", "fear", "surprise"]
        for split in ds.keys():
            for row in ds[split]:
                count += write_row(writer, row.get("text", ""), label_names[row["label"]])
        print(f"  emotion-balanced: {count}")
    except Exception as e:
        print(f"  emotion-balanced FAILED: {e}")
    return count

def load_pandora(writer):
    print("Loading PANDORA Big Five subset (20K)...")
    count = 0
    try:
        ds = load_dataset("Fatima0923/Automated-Personality-Prediction")
        for split in ds.keys():
            for row in ds[split]:
                text = row.get("text", "") or row.get("comment_body", "")
                neu = row.get("NEU", row.get("neuroticism", None))
                if text and neu is not None:
                    try:
                        score = float(neu)
                        if score > 3.5:
                            count += write_row(writer, text, "fear")
                        elif score < 2.0:
                            count += write_row(writer, text, "neutral")
                    except:
                        pass
        print(f"  PANDORA: {count}")
    except Exception as e:
        print(f"  PANDORA FAILED: {e}")
    return count

def load_elsa(writer):
    print("Loading ELSA 2025 (10K x5 styles)...")
    count = 0
    try:
        ds = load_dataset("joyspace-ai/ELSA-Emotion-and-Language-Style-Alignment-Dataset")
        for split in ds.keys():
            for row in ds[split]:
                emotion = row.get("original_emotion", "") or row.get("emotion_type", "")
                # Load original text + all 4 style variants
                for field in ["original_text", "conversational", "poetic", "formal", "narrative"]:
                    text = row.get(field, "")
                    count += write_row(writer, text, emotion)
        print(f"  ELSA: {count}")
    except Exception as e:
        print(f"  ELSA FAILED: {e}")
    return count

# ── RAW FILE DATASETS ─────────────────────────────────────────

def load_meld_raw(writer):
    print("Loading MELD raw CSVs (13K)...")
    count = 0
    try:
        for fname in ["meld_train.csv", "meld_dev.csv", "meld_test.csv"]:
            path = os.path.join(RAW_DIR, fname)
            df = pd.read_csv(path)
            for _, row in df.iterrows():
                count += write_row(writer, str(row.get("Utterance", "")),
                                   str(row.get("Emotion", "")))
        print(f"  MELD raw: {count}")
    except Exception as e:
        print(f"  MELD raw FAILED: {e}")
    return count

def load_emorynlp_raw(writer):
    print("Loading EmoryNLP raw CSVs (9K)...")
    count = 0
    try:
        for fname in ["emorynlp_train.csv", "emorynlp_dev.csv", "emorynlp_test.csv"]:
            path = os.path.join(RAW_DIR, fname)
            df = pd.read_csv(path)
            for _, row in df.iterrows():
                count += write_row(writer, str(row.get("Utterance", "")),
                                   str(row.get("Emotion", "")))
        print(f"  EmoryNLP raw: {count}")
    except Exception as e:
        print(f"  EmoryNLP raw FAILED: {e}")
    return count

def load_dreaddit_raw(writer):
    print("Loading Dreaddit raw CSVs (3.5K)...")
    count = 0
    try:
        for fname in ["dreaddit-train.csv", "dreaddit-test.csv"]:
            path = os.path.join(RAW_DIR, "dreaddit", fname)
            df = pd.read_csv(path)
            for _, row in df.iterrows():
                label = "fear" if row.get("label") == 1 else "neutral"
                count += write_row(writer, str(row.get("text", "")), label)
        print(f"  Dreaddit raw: {count}")
    except Exception as e:
        print(f"  Dreaddit raw FAILED: {e}")
    return count

def load_reccon_raw(writer):
    print("Loading RECCON raw JSON...")
    count = 0
    try:
        for fname in ["reccon_train.json", "reccon_test.json"]:
            path = os.path.join(RAW_DIR, fname)
            data = json.load(open(path, encoding="utf-8"))
            for dialogue in data.values():
                for turn in dialogue:
                    # Each turn is a list of utterance dicts
                    if isinstance(turn, list):
                        for utt in turn:
                            count += write_row(writer,
                                               utt.get("utterance", ""),
                                               utt.get("emotion", ""))
                    elif isinstance(turn, dict):
                        count += write_row(writer,
                                           turn.get("utterance", ""),
                                           turn.get("emotion", ""))
        print(f"  RECCON raw: {count}")
    except Exception as e:
        print(f"  RECCON raw FAILED: {e}")
    return count

def load_emotion_stimulus_raw(writer):
    print("Loading Emotion Stimulus raw (2.4K)...")
    count = 0
    try:
        pattern = re.compile(r"<(\w+)>(.*?)<\\\\?\1>", re.DOTALL)
        for fname in ["Emotion Cause.txt", "No Cause.txt"]:
            path = os.path.join(RAW_DIR, "emotion_stimulus", "Dataset", fname)
            with open(path, encoding="utf-8") as f:
                for line in f:
                    for match in pattern.finditer(line.strip()):
                        emotion = match.group(1)
                        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
                        count += write_row(writer, text, emotion)
        print(f"  Emotion Stimulus raw: {count}")
    except Exception as e:
        print(f"  Emotion Stimulus raw FAILED: {e}")
    return count

def load_semeval2007_raw(writer):
    print("Loading SemEval-2007 Affective Text (1.2K)...")
    count = 0
    try:
        test_dir = os.path.join(RAW_DIR, "semeval2007", "AffectiveText.test")
        xml_path = os.path.join(test_dir, "affectivetext_test.xml")
        emo_path = os.path.join(test_dir, "affectivetext_test.emotions.gold")

        # Fix bad XML by replacing bare & with &amp;
        raw = open(xml_path, encoding="utf-8", errors="replace").read()
        raw = re.sub(r'&(?![a-zA-Z#][a-zA-Z0-9#]*;)', '&amp;', raw)

        import xml.etree.ElementTree as ET
        root = ET.fromstring(raw)
        texts = {inst.get("id"): (inst.text or "").strip()
                 for inst in root.findall(".//instance")}

        emotion_names = ["anger", "disgust", "fear", "joy", "sadness", "surprise"]
        with open(emo_path, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 7:
                    continue
                doc_id = parts[0]
                scores = [int(x) for x in parts[1:7]]
                if max(scores) == 0:
                    continue
                text = texts.get(doc_id, "")
                count += write_row(writer, text, emotion_names[scores.index(max(scores))])
        print(f"  SemEval-2007 raw: {count}")
    except Exception as e:
        print(f"  SemEval-2007 raw FAILED: {e}")
    return count

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    total = 0
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "emotion"])
        writer.writeheader()

        # HuggingFace datasets
        total += load_goemotions(writer)
        total += load_carer(writer)
        total += load_empathetic(writer)
        total += load_isear(writer)
        total += load_boltuix(writer)
        total += load_super_emotion(writer)
        total += load_tweet_eval(writer)
        total += load_emotion_balanced(writer)
        total += load_pandora(writer)
        total += load_elsa(writer)

        # Raw file datasets
        total += load_meld_raw(writer)
        total += load_emorynlp_raw(writer)
        total += load_dreaddit_raw(writer)
        total += load_reccon_raw(writer)
        total += load_emotion_stimulus_raw(writer)
        total += load_semeval2007_raw(writer)

    print(f"\n✓ Done. {total} total rows saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()