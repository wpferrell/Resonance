"""
Resonance - Dataset Downloader
Downloads all manually-available datasets to data/raw/
"""

import os
import urllib.request
import zipfile
import tarfile

RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

def download_file(url, dest_path, label):
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"  Already exists, skipping: {label}")
        return True
    try:
        print(f"  Downloading {label}...")
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            with open(dest_path, "wb") as f:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        print(f"\r    {downloaded*100//total}%", end="")
        print(f"\n  ✓ {label}")
        return True
    except Exception as e:
        print(f"\n  ✗ {label} FAILED: {e}")
        return False

def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_to)
        print(f"  ✓ Extracted")
    except Exception as e:
        print(f"  ✗ Extract failed: {e}")

def extract_tar(tar_path, extract_to):
    try:
        with tarfile.open(tar_path, "r:gz") as t:
            t.extractall(extract_to, filter="data")
        print(f"  ✓ Extracted")
    except Exception:
        try:
            with tarfile.open(tar_path, "r:gz") as t:
                t.extractall(extract_to)
            print(f"  ✓ Extracted")
        except Exception as e:
            print(f"  ✗ Extract failed: {e}")

def download_meld():
    print("\n[1] MELD — Friends TV emotion (13K)")
    base = "https://raw.githubusercontent.com/declare-lab/MELD/master/data/MELD"
    for fname, url in {
        "meld_train.csv": f"{base}/train_sent_emo.csv",
        "meld_dev.csv":   f"{base}/dev_sent_emo.csv",
        "meld_test.csv":  f"{base}/test_sent_emo.csv",
    }.items():
        download_file(url, os.path.join(RAW_DIR, fname), fname)

def download_emorynlp():
    print("\n[2] EmoryNLP — Friends TV emotion (9K)")
    base = "https://raw.githubusercontent.com/declare-lab/MELD/master/data/emorynlp"
    for fname, url in {
        "emorynlp_train.csv": f"{base}/emorynlp_train_final.csv",
        "emorynlp_dev.csv":   f"{base}/emorynlp_dev_final.csv",
        "emorynlp_test.csv":  f"{base}/emorynlp_test_final.csv",
    }.items():
        download_file(url, os.path.join(RAW_DIR, fname), fname)

def download_semeval2007():
    print("\n[3] SemEval-2007 Affective Text (1.2K)")
    url = "http://web.eecs.umich.edu/~mihalcea/downloads/AffectiveText.Semeval.2007.tar.gz"
    dest = os.path.join(RAW_DIR, "affective_text_semeval2007.tar.gz")
    if download_file(url, dest, "SemEval-2007"):
        extract_tar(dest, os.path.join(RAW_DIR, "semeval2007"))

def download_emotion_stimulus():
    print("\n[4] Emotion Stimulus (2.4K)")
    url = "https://www.site.uottawa.ca/~diana/resources/emotion_stimulus_data/Dataset.zip"
    dest = os.path.join(RAW_DIR, "emotion_stimulus.zip")
    if download_file(url, dest, "Emotion Stimulus"):
        extract_zip(dest, os.path.join(RAW_DIR, "emotion_stimulus"))

def download_reccon():
    print("\n[5] RECCON — emotion cause in conversation")
    base = "https://raw.githubusercontent.com/declare-lab/RECCON/main/data/original_annotation"
    for fname, url in {
        "reccon_train.json": f"{base}/dailydialog_train.json",
        "reccon_test.json":  f"{base}/dailydialog_valid.json",
    }.items():
        download_file(url, os.path.join(RAW_DIR, fname), fname)

def download_dreaddit():
    print("\n[6] Dreaddit — Reddit stress (3.5K)")
    url = "http://www.cs.columbia.edu/~eturcan/data/dreaddit.zip"
    dest = os.path.join(RAW_DIR, "dreaddit.zip")
    if download_file(url, dest, "Dreaddit"):
        extract_zip(dest, os.path.join(RAW_DIR, "dreaddit"))

def download_wassa2017():
    print("\n[7] WASSA-2017 EmoInt (7K)")
    os.makedirs(os.path.join(RAW_DIR, "wassa2017"), exist_ok=True)
    base = "http://saifmohammad.com/WebDocs/EmoInt%20Train%20Data"
    for fname, url in {
        "anger-ratings-0to1.train.txt":   f"{base}/anger-ratings-0to1.train.txt",
        "fear-ratings-0to1.train.txt":    f"{base}/fear-ratings-0to1.train.txt",
        "joy-ratings-0to1.train.txt":     f"{base}/joy-ratings-0to1.train.txt",
        "sadness-ratings-0to1.train.txt": f"{base}/sadness-ratings-0to1.train.txt",
    }.items():
        download_file(url, os.path.join(RAW_DIR, "wassa2017", fname), fname)

def main():
    print("=" * 60)
    print("Resonance Dataset Downloader — Final Complete Version")
    print("=" * 60)

    download_meld()
    download_emorynlp()
    download_semeval2007()
    download_emotion_stimulus()
    download_reccon()
    download_dreaddit()
    download_wassa2017()

    print("\n" + "=" * 60)
    print("Done. The following load via HuggingFace — no download needed:")
    print("  GoEmotions, CARER, EmpatheticDialogues, ISEAR, Boltuix,")
    print("  SuperEmotion, SemEval EMO 2019, TweetEval, XED, MELD-ST,")
    print("  emotion-balanced, EmoEvent, SAD, FEEL-IT, CrowdFlower,")
    print("  PANDORA subset, EmoBank, ELSA 2025")
    print("\nRequire manual registration (cannot auto-download):")
    print("  - IEMOCAP: https://sail.usc.edu/iemocap/")
    print("  - TEC/SemEval-2018: http://saifmohammad.com/WebPages/SentimentEmotionLabeledData.html")
    print("=" * 60)

if __name__ == "__main__":
    main()