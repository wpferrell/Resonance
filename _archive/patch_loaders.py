"""
Patch prepare_data_v2.py with all 6 correct new dataset loaders.
"""
import re

with open("scripts/prepare_data_v2.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: EmoBank - official JULIELab GitHub source
old_emobank = """def load_emobank(writer):
    print("Loading EmoBank (10K)...")
    count = 0
    try:
        ds = load_dataset("reallycarlaost/emobank")
        for split in ds.keys():
            for row in ds[split]:
                try:
                    v = float(row.get("V", 3))
                    a = float(row.get("A", 3))
                    if v > 3.5:
                        em = "joy"
                    elif v < 2.5 and a > 3.5:
                        em = "anger"
                    elif v < 2.5 and a < 2.5:
                        em = "sadness"
                    elif v < 2.0 and a > 4.0:
                        em = "fear"
                    else:
                        em = "neutral"
                    count += write_row(writer, row.get("text", ""), em)
                except:
                    continue
        print(f"  EmoBank: {count}")
    except Exception as e:
        print(f"  EmoBank FAILED: {e}")
    return count"""

new_emobank = """def load_emobank(writer):
    # Official source: JULIELab, Jena University CC-BY
    print("Loading EmoBank (10K)...")
    count = 0
    try:
        url = "https://raw.githubusercontent.com/JULIELab/EmoBank/master/corpus/emobank.csv"
        df = pd.read_csv(url, index_col=0)
        for _, row in df.iterrows():
            try:
                v = float(row["V"]); a = float(row["A"])
                if v > 3.5: em = "joy"
                elif v < 2.5 and a > 3.5: em = "anger"
                elif v < 2.5 and a < 2.5: em = "sadness"
                elif v < 2.0 and a > 4.0: em = "fear"
                else: em = "neutral"
                count += write_row(writer, str(row["text"]), em)
            except:
                continue
        print(f"  EmoBank: {count}")
    except Exception as e:
        print(f"  EmoBank FAILED: {e}")
    return count"""

content = content.replace(old_emobank, new_emobank)

# Fix 2: BRIGHTER - use emotions list field (binary columns, take first 1)
old_brighter = """def load_brighter(writer):
    print("Loading BRIGHTER English...")
    count = 0
    try:
        ds = load_dataset("brighter-dataset/BRIGHTER-emotion-categories", "eng")
        emotions = ["joy", "sadness", "fear", "anger", "surprise", "disgust"]
        for split in ds.keys():
            for row in ds[split]:
                try:
                    dominant = max(emotions, key=lambda e: int(row.get(e, 0)))
                    count += write_row(writer, row.get("text", ""), dominant)
                except:
                    continue
        print(f"  BRIGHTER: {count}")
    except Exception as e:
        print(f"  BRIGHTER FAILED: {e}")
    return count"""

new_brighter = """def load_brighter(writer):
    # BRIGHTER: emotions field is a list e.g. ["fear", "surprise"]
    print("Loading BRIGHTER English...")
    count = 0
    try:
        ds = load_dataset("brighter-dataset/BRIGHTER-emotion-categories", "eng")
        for split in ds.keys():
            for row in ds[split]:
                try:
                    emotions_list = row.get("emotions") or []
                    if emotions_list:
                        count += write_row(writer, row.get("text", ""), emotions_list[0])
                except:
                    continue
        print(f"  BRIGHTER: {count}")
    except Exception as e:
        print(f"  BRIGHTER FAILED: {e}")
    return count"""

content = content.replace(old_brighter, new_brighter)

# Fix 3: EmoEvent - TSV not CSV, columns: id, tweet, emotion, offensive
old_emoevent = """def load_emoevent(writer):
    print("Loading EmoEvent (83K)...")
    count = 0
    try:
        url = "https://raw.githubusercontent.com/fmplaza/EmoEvent/master/data/corpus_en.tsv"
        df = pd.read_csv(url, sep="\\t", on_bad_lines="skip")
        cols = df.columns.tolist()
        tkey = next((c for c in cols if "tweet" in c.lower() or "text" in c.lower()), cols[0])
        ekey = next((c for c in cols if "emotion" in c.lower() or "label" in c.lower()), cols[1])
        for _, row in df.iterrows():
            count += write_row(writer, str(row[tkey]), str(row[ekey]))
        print(f"  EmoEvent: {count}")
    except Exception as e:
        print(f"  EmoEvent FAILED: {e}")
    return count"""

new_emoevent = """def load_emoevent(writer):
    # EmoEvent: TSV file, columns: id, tweet, emotion, offensive
    print("Loading EmoEvent (83K)...")
    count = 0
    try:
        url = "https://raw.githubusercontent.com/fmplaza/EmoEvent/master/emoevent_en.csv"
        df = pd.read_csv(url, sep="\\t", on_bad_lines="skip")
        for _, row in df.iterrows():
            count += write_row(writer, str(row.get("tweet", "")), str(row.get("emotion", "")))
        print(f"  EmoEvent: {count}")
    except Exception as e:
        print(f"  EmoEvent FAILED: {e}")
    return count"""

content = content.replace(old_emoevent, new_emoevent)

# Fix 4: XED - load directly from Helsinki-NLP GitHub TSV
old_xed = """def load_xed(writer):
    print("Loading XED English (25K)...")
    count = 0
    try:
        ds = load_dataset("Helsinki-NLP/xed_en_fi", "en_annotated", trust_remote_code=True)
        xmap = {1:"anger", 2:"neutral", 3:"anger", 4:"fear",
                5:"joy", 6:"sadness", 7:"surprise", 8:"joy"}
        for split in ds.keys():
            for row in ds[split]:
                for lbl in row.get("labels", []):
                    em = xmap.get(lbl)
                    if em:
                        count += write_row(writer, row.get("sentence", ""), em)
                        break
        print(f"  XED: {count}")
    except Exception as e:
        print(f"  XED FAILED: {e}")
    return count"""

new_xed = """def load_xed(writer):
    # Official source: Helsinki-NLP GitHub CC-BY
    print("Loading XED English (25K)...")
    count = 0
    try:
        url = "https://raw.githubusercontent.com/Helsinki-NLP/XED/master/AnnotatedData/en-annotated.tsv"
        df = pd.read_csv(url, sep="\\t", header=None, names=["sentence","labels"], on_bad_lines="skip")
        xmap = {"1":"anger","2":"neutral","3":"anger","4":"fear",
                "5":"joy","6":"sadness","7":"surprise","8":"joy"}
        for _, row in df.iterrows():
            labels = str(row["labels"]).split()
            for lbl in labels:
                em = xmap.get(lbl.strip())
                if em:
                    count += write_row(writer, str(row["sentence"]), em)
                    break
        print(f"  XED: {count}")
    except Exception as e:
        print(f"  XED FAILED: {e}")
    return count"""

content = content.replace(old_xed, new_xed)

# Fix 5: GoodNewsEveryone - load from JSONL already downloaded
old_gne = """def load_goodnewseveryone(writer):
    print("Loading GoodNewsEveryone (5K)...")
    count = 0
    try:
        url = "https://raw.githubusercontent.com/glnmario/goodnewseveryone/main/data/goodnewseveryone.csv"
        df = pd.read_csv(url)
        cols = df.columns.tolist()
        tkey = next((c for c in cols if "head" in c.lower() or "text" in c.lower()), cols[0])
        ekey = next((c for c in cols if "dominant" in c.lower() or "emotion" in c.lower()), cols[1])
        for _, row in df.iterrows():
            count += write_row(writer, str(row[tkey]), str(row[ekey]))
        print(f"  GoodNewsEveryone: {count}")
    except Exception as e:
        print(f"  GoodNewsEveryone FAILED: {e}")
    return count"""

new_gne = """def load_goodnewseveryone(writer):
    # Official source: IMS Stuttgart, downloaded to data/raw/goodnewseveryone/
    print("Loading GoodNewsEveryone (5K)...")
    count = 0
    try:
        import json
        path = os.path.join(RAW_DIR, "goodnewseveryone", "goodnewseveryone-v1.0", "gne-release-v1.0.jsonl")
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                headline = obj.get("headline", "")
                # dominant_emotion is the most common reader-perceived emotion
                dominant = obj.get("dominant_emotion", "")
                count += write_row(writer, headline, dominant)
        print(f"  GoodNewsEveryone: {count}")
    except Exception as e:
        print(f"  GoodNewsEveryone FAILED: {e}")
    return count"""

content = content.replace(old_gne, new_gne)

# Fix 6: EmoBench-UA - correct HF ID ukr-detect/ukr-emotions-binary
old_ua = """def load_emobench_ua(writer):
    print("Loading EmoBench-UA Ukrainian (5K)...")
    count = 0
    try:
        url = "https://raw.githubusercontent.com/dardem/emobench-ua/main/data/train.csv"
        df = pd.read_csv(url)
        cols = df.columns.tolist()
        tkey = next((c for c in cols if "text" in c.lower()), cols[0])
        ekey = next((c for c in cols if "label" in c.lower() or "emotion" in c.lower()), cols[1])
        for _, row in df.iterrows():
            count += write_row(writer, str(row[tkey]), str(row[ekey]))
        print(f"  EmoBench-UA: {count}")
    except Exception as e:
        print(f"  EmoBench-UA FAILED: {e}")
    return count"""

new_ua = """def load_emobench_ua(writer):
    # Official source: ukr-detect/ukr-emotions-binary on HuggingFace
    # Binary columns: Joy, Fear, Anger, Sadness, Disgust, Surprise
    print("Loading EmoBench-UA Ukrainian (5K)...")
    count = 0
    try:
        ds = load_dataset("ukr-detect/ukr-emotions-binary")
        emotions = ["Joy", "Fear", "Anger", "Sadness", "Disgust", "Surprise"]
        em_map = {"Joy":"joy","Fear":"fear","Anger":"anger",
                  "Sadness":"sadness","Disgust":"anger","Surprise":"surprise"}
        for split in ds.keys():
            for row in ds[split]:
                try:
                    dominant = next((e for e in emotions if row.get(e,0)==1), None)
                    if dominant:
                        count += write_row(writer, row.get("text",""), em_map[dominant])
                except:
                    continue
        print(f"  EmoBench-UA: {count}")
    except Exception as e:
        print(f"  EmoBench-UA FAILED: {e}")
    return count"""

content = content.replace(old_ua, new_ua)

# Restore GoodNewsEveryone and EmoBench-UA in main() if they were commented out
content = content.replace(
    """        # GoodNewsEveryone: no accessible public URL found (SSL issue on Stuttgart server)
        # EmoBench-UA: GitHub data files not publicly accessible
        # Both will be added in next retrain when sources are confirmed""",
    """        total += load_goodnewseveryone(writer)
        total += load_emobench_ua(writer)"""
)

with open("scripts/prepare_data_v2.py", "w", encoding="utf-8") as f:
    f.write(content)

print("All 6 loaders patched. Run: python scripts/prepare_data_v2.py")

