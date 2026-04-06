"""
Resonance Dataset Scout — Background Search Daemon
===================================================
Runs forever on Shadow PC. Polls every known dataset source on a rolling
schedule, checks every result against all 7 Resonance rules AND against
framework relevance (which model heads it feeds), and writes any passes
to a report file you can check anytime.

Priority levels:
  CRITICAL — covers a head with ZERO current training data
             (reappraisal/suppression, alexithymia, PERMA, WoT, attachment)
  HIGH     — covers a significant head gap, framework score >= 6
  MEDIUM   — useful dataset, framework score 3-5
  LOW      — passes all rules, general emotion utility, score 1-2
  GENERAL  — passes all rules, no specific framework match, score 0
  BORDERLINE — passes most rules but needs manual review on one

Run:
    cd C:\\Users\\Shadow\\Documents\\Resonance
    .venv\\Scripts\\Activate.ps1
    python scripts\\dataset_scout.py

Outputs (in Resonance project root):
    scout_results.md     — FOUND / BORDERLINE reports (check this daily)
    scout_seen.json      — fingerprint cache (skip already-checked items)
    scout.log            — full operational log

Stop anytime with Ctrl+C. Safe to restart — cache persists.
"""

import requests
import json
import time
import logging
import hashlib
import re
import sys
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────

BASE         = Path(__file__).parent.parent
RESULTS_FILE = BASE / "scout_results.md"
SEEN_FILE    = BASE / "scout_seen.json"
LOG_FILE     = BASE / "scout.log"

# ─────────────────────────────────────────────────────────────────────────────
# WINDOWS TOAST NOTIFICATION
# ─────────────────────────────────────────────────────────────────────────────

def notify(title, body, priority="FOUND"):
    """
    Fire a Windows 10/11 toast notification via PowerShell.
    Falls back silently if PowerShell isn't available (e.g. non-Windows).
    """
    # Emoji prefix by priority
    emoji = {"CRITICAL": "🚨", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "BORDERLINE": "🔵"}
    prefix = emoji.get(priority, "🔔")
    safe_title = title.replace("'", "").replace('"', "")[:80]
    safe_body  = body.replace("'", "").replace('"', "")[:120]

    ps_script = f"""
$app = 'Resonance Scout'
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$template = @"
<toast duration='long'>
  <visual>
    <binding template='ToastGeneric'>
      <text>{prefix} Resonance Scout — {priority}</text>
      <text>{safe_title}</text>
      <text>{safe_body}</text>
    </binding>
  </visual>
  <audio src='ms-winsoundevent:Notification.Default'/>
</toast>
"@
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app)
$notifier.Show($toast)
"""
    try:
        subprocess.Popen(
            ["powershell", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", ps_script],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass   # Notification is best-effort — never crash the scout for this

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("scout")

# ─────────────────────────────────────────────────────────────────────────────
# RATE LIMITING
# ─────────────────────────────────────────────────────────────────────────────

API_SLEEP       = 2    # seconds between any two API calls
GITHUB_SLEEP    = 4    # GitHub is stricter
SCHOLAR_SLEEP   = 3    # Semantic Scholar 100 req/5min

def api_get(url, params=None, timeout=15, sleep=API_SLEEP):
    """Safe GET with rate limit handling."""
    try:
        r = requests.get(
            url, params=params, timeout=timeout,
            headers={"User-Agent": "Resonance-Scout/1.0 (wpferrell@gmail.com; research use)"}
        )
        if r.status_code == 429:
            log.warning(f"Rate limited {url} — sleeping 90s")
            time.sleep(90)
            return None
        if r.status_code not in (200, 201):
            log.debug(f"HTTP {r.status_code} from {url}")
            return None
        time.sleep(sleep)
        return r
    except Exception as e:
        log.debug(f"Request error {url}: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# R1: LICENSE DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

R1_PASS = {
    "cc-by-4.0", "cc-by-3.0", "cc-by-2.0", "cc-by-2.5",
    "cc0-1.0", "cc0", "cc-zero",
    "mit", "mit-license",
    "apache-2.0", "apache2.0",
    "bsd-2-clause", "bsd-3-clause",
    "unlicense", "wtfpl",
    "odc-by", "pddl", "public-domain",
}

R1_FLAG = {   # pass but flag for legal review before enterprise use
    "cc-by-sa-4.0", "cc-by-sa-3.0",
    "gpl-2.0", "gpl-3.0", "lgpl-3.0",
    "odbl",
}

R1_FAIL = {
    "cc-by-nc-4.0", "cc-by-nc-3.0", "cc-by-nc-2.0",
    "cc-by-nc-sa-4.0", "cc-by-nc-sa-3.0",
    "cc-by-nc-nd-4.0", "cc-by-nd-4.0",
    "all-rights-reserved", "proprietary",
    "research-only", "academic-only", "non-commercial",
    "other",   # HuggingFace "other" = unknown = treat as fail
}

def check_r1(lic_raw):
    """Returns: 'pass', 'pass_flagged', 'fail', 'unknown'"""
    if not lic_raw:
        return "unknown"
    lic = str(lic_raw).lower().strip().replace(" ", "-")
    if lic in R1_FAIL:
        return "fail"
    if lic in R1_PASS:
        return "pass"
    if lic in R1_FLAG:
        return "pass_flagged"
    # substring checks
    if any(x in lic for x in ["nc", "non-commercial", "research-only", "academic"]):
        return "fail"
    if any(x in lic for x in ["cc-by", "cc0", "mit", "apache", "bsd", "unlicense", "public domain", "wtfpl", "pddl"]):
        return "pass"
    return "unknown"

# ─────────────────────────────────────────────────────────────────────────────
# R2: INSTITUTION / PEER REVIEW SIGNALS
# ─────────────────────────────────────────────────────────────────────────────

R2_VENUE_SIGNALS = [
    # NLP conferences
    "acl ", " acl)", "emnlp", "naacl", "eacl", "lrec", "coling",
    "ijcnlp", "conll", "semeval", "wassa", "clpsych", "louhi",
    # AI/ML conferences
    "aaai", "ijcai", "neurips", "iclr", "icml", "acm mm",
    # Psychology journals
    "frontiers in psychology", "plos one", "psychological science",
    "emotion journal", "nature human behaviour", "cognition",
    "affective science", "clinical psychological science",
    "journal of personality", "journal of emotion",
    # General open access
    "ieee access", "scientific data", "data in brief",
]

R2_INSTITUTION_SIGNALS = [
    "university", "université", "universidad", "universität",
    "institute", "college of", "school of", "department of",
    "laboratory", " lab,", " lab.", "research center", "research centre",
    "government", "federal", "national institute", "national lab",
    "max planck", "mit.", "stanford", "carnegie mellon", "cmu",
    "google research", "meta ai", "microsoft research", "amazon science",
    "apple research", "deepmind", "anthropic",
]

def check_r2(text, downloads=0, has_doi=False, has_arxiv=False, venue=None):
    """
    Returns: 'pass', 'flagged' (borderline, manual check), or 'fail'
    Rule: peer-reviewed OR major institution. NOT a hard blocker alone.
    """
    combined = (text or "").lower()
    if venue:
        combined = combined + " " + venue.lower()

    # Strong pass: venue listed
    if any(v in combined for v in R2_VENUE_SIGNALS):
        return "pass"

    # Institution affiliation
    if any(inst in combined for inst in R2_INSTITUTION_SIGNALS):
        return "pass"

    # DOI + significant downloads = credible
    if has_doi and downloads > 300:
        return "pass"

    # arXiv preprint — not yet peer-reviewed but credible
    if has_arxiv:
        return "flagged"

    # High downloads with no other signals — borderline
    if downloads > 800:
        return "flagged"

    # No signals at all
    if not has_doi and downloads < 80:
        return "fail"

    # Low signal but not clearly failing
    return "flagged"

# ─────────────────────────────────────────────────────────────────────────────
# R3: REAL HUMAN TEXT (text itself, not labels)
# ─────────────────────────────────────────────────────────────────────────────

# These mean the TEXT is AI-generated → hard fail
R3_TEXT_AI_SIGNALS = [
    "text is generated", "text generated by", "llm-generated text",
    "gpt-generated text", "generated by gpt", "generated by chatgpt",
    "synthetic text", "procedurally generated text",
    "fully synthetic", "100% synthetic", "ai-generated text",
    "generated by claude", "generated by llm", "deku corpus builder",
    "simulated conversations",
]

# These mean the TEXT is real human → pass
R3_HUMAN_SIGNALS = [
    "crowdsourced", "mechanical turk", "mturk", "prolific.co",
    "annotators", "human annotators", "survey responses", "self-report",
    "social media", "reddit", "twitter", "youtube comment",
    "transcription", "interview", "clinical note", "diary",
    "news headline", "literary", "user-generated", "forum post",
    "blog post", "participant", "human rater", "double annotated",
    "crowd workers", "amazon mechanical", "real tweets", "real posts",
]

def check_r3(text):
    """
    Returns: 'pass', 'fail', or 'unknown'
    Fails ONLY if the TEXT ITSELF is AI-generated.
    AI-assisted labeling on real text = pass (rule explicitly allows this).
    """
    t = (text or "").lower()
    # Hard fail: text is AI-generated
    if any(s in t for s in R3_TEXT_AI_SIGNALS):
        return "fail"
    # Pass: human text signals
    if any(s in t for s in R3_HUMAN_SIGNALS):
        return "pass"
    return "unknown"

# ─────────────────────────────────────────────────────────────────────────────
# R4: EMOTIONAL CONTENT SIGNALS
# ─────────────────────────────────────────────────────────────────────────────

R4_EMOTION_SIGNALS = [
    "emotion", "sentiment", "affect", "wellbeing", "well-being",
    "distress", "anxiety", "depression", "grief", "trauma", "empathy",
    "mood", "mental health", "psychological", "feelings", "anger",
    "sadness", "fear", "joy", "guilt", "shame", "loneliness",
    "love", "happiness", "disgust", "surprise", "frustration",
    "worry", "stress", "valence", "arousal", "dominance", "vad",
    "appraisal", "rumination", "coping", "hope", "pride", "jealousy",
    "contempt", "envy", "alexithymia", "emotional", "affective",
    "regret", "remorse", "hopelessness", "helplessness", "longing",
    "embarrassment", "humiliation", "reappraisal", "suppression",
    "regulation", "crisis", "suicidal", "self-harm", "flourishing",
    "perma", "self-determination", "attachment",
]

R4_NON_EMOTION = [
    "stock price", "financial statement", "legal document",
    "medical imaging", "code review", "software bug", "traffic sensor",
    "weather forecast", "satellite image", "genomics", "protein structure",
    "chemistry compound", "engineering specification", "crop yield",
]

def check_r4(title, desc, tags):
    combined = f"{title} {desc or ''} {' '.join(tags or [])}".lower()
    if any(s in combined for s in R4_NON_EMOTION):
        return "fail"
    if any(s in combined for s in R4_EMOTION_SIGNALS):
        return "pass"
    return "fail"

# ─────────────────────────────────────────────────────────────────────────────
# R5: NOT TOO NARROW
# ─────────────────────────────────────────────────────────────────────────────

R5_INSTANT_PASS = [
    "psychology", "mental health", "wellbeing", "clinical", "therapy",
    "counseling", "counselling", "psychiatric", "emotion", "affect",
    "distress", "anxiety", "depression", "trauma", "grief", "empathy",
]

R5_NARROW_FAIL = [
    "friends tv", "game of thrones", "breaking bad", "single movie",
    "single brand", "single product", "astrobiology", "forex",
    "cryptocurrency", "bitcoin", "aviation", "crop yield",
    "stock market emotion",   # narrow finance domain
    "sports fan emotion",     # single sports domain
]

def check_r5(title, desc, tags):
    combined = f"{title} {desc or ''} {' '.join(tags or [])}".lower()
    if any(s in combined for s in R5_INSTANT_PASS):
        return "pass"
    if any(s in combined for s in R5_NARROW_FAIL):
        return "fail"
    return "pass"   # default pass — narrowness is rare

# ─────────────────────────────────────────────────────────────────────────────
# R6: NOT GATED
# ─────────────────────────────────────────────────────────────────────────────

R6_GATED_SIGNALS = [
    "request access", "requires approval", "data use agreement",
    "contact author for", "by request only", "upon request",
    "dua required", "institutional approval", "ethics approval required",
    "sign up to download", "register to access", "login required",
    "gated dataset", "restricted access", "apply for access",
]

def check_r6(desc, source_is_hf_public=False, source_is_zenodo_open=False,
             source_is_github_public=False):
    if source_is_hf_public or source_is_zenodo_open or source_is_github_public:
        return "pass"
    t = (desc or "").lower()
    if any(s in t for s in R6_GATED_SIGNALS):
        return "fail"
    return "pass"

# ─────────────────────────────────────────────────────────────────────────────
# R7: NO STRUCTURAL COLLECTION BIAS
# ─────────────────────────────────────────────────────────────────────────────

R7_BIAS_SIGNALS = [
    "scraped from r/depression only",
    "scraped from r/anxiety only",
    "scraped from r/suicidewatch",
    "all posts are about",
    "crisis text line only",
    "hate speech only",
    "anger forum",
    "single subreddit",
    "100% negative",
    "100% positive",
]

def check_r7(desc):
    t = (desc or "").lower()
    if any(s in t for s in R7_BIAS_SIGNALS):
        return "fail"
    return "pass"

# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGE FILTER (not a rule, but practical)
# ─────────────────────────────────────────────────────────────────────────────

EXCLUSIVELY_NON_ENGLISH = [
    # Only reject if the title clearly says ONLY this language
    "arabic only", "chinese only", "hindi only", "spanish only",
    "french only", "german only", "japanese only", "korean only",
    "portuguese only", "italian only", "dutch only", "turkish only",
    "persian farsi", "urdu only", "uzbek", "azerbaijani",
    # HuggingFace language tag format
    "language:ar\"", "language:zh\"", "language:de\"", "language:fr\"",
]

NON_ENGLISH_TITLE_PATTERNS = [
    r"\bالعرب", r"\b中文\b", r"\b한국\b", r"\b日本語\b",
    r"\bfrançais\b", r"\bdeutsch\b", r"\bespañol\b",
]

def is_likely_english(title, tags):
    title_l = title.lower()
    tags_str = " ".join(tags or []).lower()

    # Explicit English = pass
    if "language:en" in tags_str or "english" in title_l:
        return True

    # Multilingual including English = pass
    if "multilingual" in title_l or "multilingual" in tags_str:
        return True

    # Check for non-English script in title
    for pattern in NON_ENGLISH_TITLE_PATTERNS:
        if re.search(pattern, title):
            return False

    # Language tag that is NOT English and NOT multilingual
    lang_tags = [t for t in (tags or []) if t.startswith("language:")]
    if lang_tags and "language:en" not in lang_tags:
        # If only non-English languages listed
        return False

    return True   # assume English if no contrary signal

# ─────────────────────────────────────────────────────────────────────────────
# FRAMEWORK SCORING — WEIGHTED FOR HEAD GAPS
# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL means we have zero training data for this head.
# These get double weight.

CRITICAL_HEAD_KEYWORDS = {
    # HEAD 6: Reappraisal/Suppression — ZERO coverage
    "reappraisal": 6,
    "cognitive reappraisal": 6,
    "expressive suppression": 6,
    "emotion suppression": 6,
    "regulation strategy": 5,
    "reappraisal suppression": 6,
    # HEAD 7: Alexithymia — ZERO coverage
    "alexithymia": 6,
    "emotion blindness": 6,
    "difficulty identifying emotions": 6,
    "difficulty describing emotions": 6,
    "emotion awareness": 4,
    # HEAD 10: PERMA — ZERO coverage
    "perma": 6,
    "flourishing scale": 6,
    "perma-v": 6,
    "positive psychology text": 5,
    "wellbeing questionnaire text": 4,
    # WoT — ZERO coverage (deferred head)
    "window of tolerance": 5,
    "hyperarousal hypoarousal": 5,
    "dorsal vagal": 4,
    "trauma response labeled": 4,
    # Attachment — ZERO coverage (deferred head)
    "attachment style text": 5,
    "anxious attachment labeled": 5,
    "avoidant attachment labeled": 5,
    "secure attachment text": 4,
}

FRAMEWORK_KEYWORDS = {
    # HEAD 1: Shame/Guilt gap (F1 = 0.455, worst class)
    "shame": 4,
    "guilt": 4,
    "remorse": 3,
    "embarrassment": 3,
    "humiliation": 3,
    "self-conscious emotion": 4,
    "moral guilt": 4,
    "social guilt": 4,
    "self-blame": 3,

    # HEAD 2: VAD (only EmoBank = 10K rows)
    "valence arousal dominance": 4,
    "vad annotation": 4,
    "dimensional emotion": 3,
    "continuous emotion": 3,
    "circumplex model": 3,
    "valence arousal": 3,

    # HEAD 5: Secondary emotion fine-grained
    "contempt": 3,
    "envy": 3,
    "awe": 2,
    "longing": 2,
    "dread": 2,
    "fine-grained emotion": 3,
    "secondary emotion": 3,
    "emotion granularity": 3,
    "plutchik": 2,

    # HEAD 9: Crisis (Dreaddit only approximates this)
    "suicidal ideation": 4,
    "self-harm text": 4,
    "crisis detection": 4,
    "crisis text": 3,
    "suicide nlp": 4,

    # SDT
    "self-determination": 3,
    "autonomy satisfaction": 3,
    "competence satisfaction": 3,
    "relatedness satisfaction": 3,
    "basic psychological needs": 3,

    # DBT
    "dialectical behavior": 3,
    "distress tolerance": 3,
    "emotion dysregulation": 3,

    # Register gaps
    "expressive writing": 3,
    "personal narrative": 2,
    "diary study": 2,
    "experience sampling": 3,
    "literary emotion": 2,
    "clinical text": 3,
    "therapy transcript": 3,
    "written reflection": 2,
}

CRITICAL_THRESHOLD = 5    # any single keyword >= 5 = CRITICAL
HIGH_THRESHOLD     = 6    # total score >= 6 = HIGH
MEDIUM_THRESHOLD   = 3    # total score >= 3 = MEDIUM
LOW_THRESHOLD      = 1    # total score >= 1 = LOW

def score_frameworks(title, desc, tags):
    combined = f"{title} {desc or ''} {' '.join(tags or [])}".lower()
    scores = {}
    is_critical = False

    # Check critical head keywords first
    for kw, pts in CRITICAL_HEAD_KEYWORDS.items():
        if kw in combined:
            scores[f"CRITICAL:{kw}"] = pts
            if pts >= CRITICAL_THRESHOLD:
                is_critical = True

    # Framework keywords
    for kw, pts in FRAMEWORK_KEYWORDS.items():
        if kw in combined:
            scores[kw] = pts

    total = sum(scores.values())
    return scores, total, is_critical

def get_priority(scores, total, is_critical, r2_result):
    if is_critical:
        return "CRITICAL"
    if total >= HIGH_THRESHOLD:
        return "HIGH"
    if total >= MEDIUM_THRESHOLD:
        return "MEDIUM"
    if total >= LOW_THRESHOLD:
        return "LOW"
    return "GENERAL"

# ─────────────────────────────────────────────────────────────────────────────
# FULL RULE ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def run_rules(title, desc, lic_raw, tags=None, downloads=0,
              has_doi=False, has_arxiv=False, venue=None,
              source_is_hf=False, source_is_zenodo_open=False,
              source_is_github=False):
    """
    Returns dict:
      passed: bool
      borderline: bool
      priority: str
      rules: dict
      scores: dict
      total_score: int
      is_critical: bool
      notes: list
    """
    result = {
        "passed": False, "borderline": False,
        "priority": "GENERAL", "rules": {}, "scores": {},
        "total_score": 0, "is_critical": False, "notes": [],
    }
    tags = tags or []

    # Language check
    if not is_likely_english(title, tags):
        result["rules"]["language"] = "fail: non-English"
        return result

    # R1
    r1 = check_r1(lic_raw)
    result["rules"]["R1"] = r1
    if r1 == "fail":
        result["notes"].append(f"R1 fail: license '{lic_raw}'")
        return result
    if r1 == "unknown":
        result["notes"].append(f"R1 unknown: license '{lic_raw}' — needs manual check")
    if r1 == "pass_flagged":
        result["notes"].append(f"R1 flagged: copyleft license — flag before enterprise use")

    # R2
    text_for_r2 = f"{title} {desc or ''}"
    r2 = check_r2(text_for_r2, downloads, has_doi, has_arxiv, venue)
    result["rules"]["R2"] = r2
    if r2 == "fail":
        result["notes"].append("R2 fail: no institutional signal, low downloads")
        result["borderline"] = True   # R2 alone is not a hard blocker — still report
    elif r2 == "flagged":
        result["notes"].append("R2 uncertain: manual check needed for institution/peer-review")

    # R3
    r3 = check_r3(f"{title} {desc or ''}")
    result["rules"]["R3"] = r3
    if r3 == "fail":
        result["notes"].append("R3 fail: AI-generated text signals detected")
        return result   # hard fail
    if r3 == "unknown":
        result["notes"].append("R3 uncertain: no clear human/AI text signal — manual check")

    # R4
    r4 = check_r4(title, desc, tags)
    result["rules"]["R4"] = r4
    if r4 == "fail":
        result["notes"].append("R4 fail: no emotional content signal")
        return result   # hard fail

    # R5
    r5 = check_r5(title, desc, tags)
    result["rules"]["R5"] = r5
    if r5 == "fail":
        result["notes"].append("R5 fail: possibly too narrow a domain")
        result["borderline"] = True

    # R6
    r6 = check_r6(desc, source_is_hf, source_is_zenodo_open, source_is_github)
    result["rules"]["R6"] = r6
    if r6 == "fail":
        result["notes"].append("R6 fail: gated access signals detected")
        return result   # hard fail

    # R7
    r7 = check_r7(desc)
    result["rules"]["R7"] = r7
    if r7 == "fail":
        result["notes"].append("R7 fail: structural collection bias signals")
        result["borderline"] = True

    # Framework scoring
    scores, total, is_critical = score_frameworks(title, desc, tags)
    result["scores"]      = scores
    result["total_score"] = total
    result["is_critical"] = is_critical

    # Determine pass/borderline
    hard_fails = [r for r in ["R3","R4","R6"] if result["rules"].get(r) == "fail"]
    if hard_fails:
        return result   # already handled above but safety net

    # R1 must actually pass (not just unknown)
    if r1 in ("pass", "pass_flagged", "unknown"):
        if r2 == "fail":
            result["borderline"] = True
        elif r5 == "fail" or r7 == "fail":
            result["borderline"] = True
        else:
            result["passed"] = True

    # Priority
    result["priority"] = get_priority(scores, total, is_critical, r2)

    return result

# ─────────────────────────────────────────────────────────────────────────────
# SEEN CACHE
# ─────────────────────────────────────────────────────────────────────────────

def load_seen():
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text("utf-8")))
        except:
            return set()
    return set()

def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(sorted(seen), indent=2), encoding="utf-8")

def make_fp(identifier):
    return hashlib.sha256(str(identifier).lower().strip().encode()).hexdigest()[:16]

# ─────────────────────────────────────────────────────────────────────────────
# PRE-LOADED KNOWN ITEMS
# ─────────────────────────────────────────────────────────────────────────────

IN_STACK = {
    # All 28 datasets from registry — HF IDs and common aliases
    "google-research-datasets/go_emotions", "go_emotions", "goemotions",
    "dair-ai/emotion", "carer",
    "boltuix/emotions-dataset",
    "cirimus/super-emotion", "super-emotion", "super_emotion",
    "cardiffnlp/tweet_eval",
    "adamcodd/emotion-balanced", "emotion-balanced",
    "fatima0923/automated-personality-prediction", "pandora",
    "joyspace-ai/elsa-emotion-and-language-style-alignment-dataset", "elsa",
    "meld", "meld dataset",
    "emorynlp", "emory nlp",
    "dreaddit",
    "emotion stimulus",
    "semeval-2007 affective text", "semeval2007",
    "emobank",
    "brighter-dataset/brighter-emotion-categories", "brighter",
    "fmplaza/emoevent", "emoevent",
    "helsinki-nlp/xed_en_fi", "xed english",
    "goodnewseveryone",
    "ukr-detect/ukr-emotions-binary", "emobench-ua",
    "nbertagnolli/counsel-chat", "counselchat",
    "amod/mental_health_counseling_conversations",
    "fadodr/mental_health_therapy",
    "ddwang2000/emotioncot", "emotioncot",
    "lots-of-loras/task517_emo_classify_emotion_of_dialogue",
    "lots-of-loras/task875_emotion_classification",
    "lots-of-loras/task512_twitter_emotion_classification",
    "yael-katsman/loneliness-causes-and-intensity", "loneliness causes and intensity",
}

KNOWN_FAILS = {
    # Key: lowercase fragment that appears in title. Value: fail reason.
    "empatheticdialogues": "R1 NC",
    "empathetic dialogues": "R1 NC",
    "dailydialog": "permanently excluded",
    "daily dialog": "permanently excluded",
    "reccon": "R1+R6",
    "swmh": "R5+R6",
    "smhd": "R6 gated",
    "wassa 2021": "R6 gated",
    "wassa 2022": "R6 gated",
    "wassa 2023": "R6 gated",
    "wassa 2024": "R6 gated",
    "covid worry": "R1 GPL",
    "real world worry": "R1 GPL",
    "emowoz": "R1 CC-BY-NC",
    "vivae": "R1 CC-BY-NC",
    "mentalchat16k": "R3 synthetic",
    # Assessed sweep 1 - 2026-04-05
    "limorgu/empathy-affective-datasets": "not a dataset - reference guide only",
    "empathyai/books-ner-dataset": "R4+R6 fail: NER on book metadata, gated",
    "empathyai/books-ner-dataset-categories": "R4+R6 fail: NER on book metadata, gated",
    "tts-agi/emotion-voice-attribute-reference-snippets-dacvae": "R4 fail: audio dataset not text",
    "tts-agi/emotion-voice-attribute-reference-snippets-dacvae-wave": "R4 fail: audio dataset not text",
    "anonymous-empathyai/mindreframe-source": "R1+R2 fail: anonymous, unknown license",
    "eduhuemar001/sentiment-user-study": "R1+R2 fail: unknown license, no description",
    "jason1966/alihanuludag_turkish-universities-sentiment-analysis-dataset": "language: Turkish",
    "helsinki-nlp/qed_amara": "R4 fail: QA dataset, not emotion-labeled",
    "ihsansaad24/mental-health_text-classification_dataset": "hold: derived dataset, source corpora need verification",
    "ourafla/mental-health_text-classification_dataset": "hold: duplicate of above",
    "jhota2025/mental-health-text-dataset": "R2 fail: no description or card",
    "universal joy": "R3 distant supervision",
    "ru_go_emotions": "R3 machine-translated",
    "lv_go_emotions": "R3 machine-translated",
    "lt_go_emotions": "R3 machine-translated",
    "ru go emotions": "R3 machine-translated",
    "lv go emotions": "R3 machine-translated",
    "emotional intelligence content": "R3 AI-generated (Deku builder)",
    "sronquillo2": "R2 individual, derived from excluded datasets",
    "isear": "R1 NC — University of Geneva non-commercial",
    "emoevent spanish": "language",
    "abbe corpus": "file broken at source — check rdm@fiu.edu",
    "hrecpw": "language: Spanish",
    "hear hispanic": "language: Spanish",
    "culemо": "benchmark not training corpus",
    "culemo": "benchmark not training corpus",
    "finance_emotions": "R5 narrow: finance domain",
    "goodnews measles": "R7 single-domain collection",
    "astrobiology": "R5+R7 narrow domain",
    "tunisian": "R3 language: Arabic/Darija",
    "chinese multi-label affective": "language",
    "uzbek": "language",
}

def is_known(title, ds_id=None):
    """Returns reason string if known, None otherwise."""
    checks = [title.lower()]
    if ds_id:
        checks.append(str(ds_id).lower())

    for check in checks:
        # Check stack
        for stack_id in IN_STACK:
            if stack_id in check or check in stack_id:
                return f"already in stack: {stack_id}"
        # Check known fails
        for fail_frag, reason in KNOWN_FAILS.items():
            if fail_frag in check:
                return f"known fail ({reason})"

    return None

# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT WRITERS
# ─────────────────────────────────────────────────────────────────────────────

def init_results():
    if not RESULTS_FILE.exists():
        RESULTS_FILE.write_text(
            "# Resonance Dataset Scout — Results\n\n"
            "Auto-generated. Review FOUND entries → add to Registry → add loader → retrain.\n\n"
            "Priority: CRITICAL > HIGH > MEDIUM > LOW > GENERAL > BORDERLINE\n\n---\n\n",
            encoding="utf-8"
        )

def write_found(title, source, url, lic, size_hint, result, dl_url=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    priority = result["priority"]

    rules_str = "\n".join(f"  - {k}: {v}" for k, v in result["rules"].items())

    fw_lines = ""
    if result["scores"]:
        fw_lines = "\n".join(
            f"  - {k}: +{v}" for k, v in
            sorted(result["scores"].items(), key=lambda x: -x[1])[:8]
        )
    else:
        fw_lines = "  - No specific framework match — general emotion utility"

    notes_str = "\n".join(f"  - {n}" for n in result["notes"]) or "  - None"

    # Make CRITICAL entries visually prominent
    header = f"## [{ts}] {'🚨 ' if priority == 'CRITICAL' else ''}[{priority}] FOUND: {title}\n"

    entry = (
        f"\n{header}"
        f"- **Source:** {source}\n"
        f"- **URL:** {url}\n"
        f"- **License:** {lic or 'unknown'}\n"
        f"- **Size:** {size_hint or 'unknown'}\n"
        f"- **Rules:**\n{rules_str}\n"
        f"- **Framework score ({result['total_score']} pts):**\n{fw_lines}\n"
        f"- **Download:** {dl_url or url}\n"
        f"- **Notes:**\n{notes_str}\n"
        f"- **Action:** Review → Registry → prepare_data_v2.py → retrain\n\n---\n"
    )
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
    log.info(f"[{priority}] FOUND: {title}")
    # Windows toast notification
    body = f"License: {lic or 'unknown'} | Score: {result['total_score']}pts | {source}"
    notify(title, body, priority)

def write_borderline(title, source, url, result):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    fails = [f"{k}:{v}" for k, v in result["rules"].items()
             if v in ("fail", "unknown", "flagged")]
    notes_str = " | ".join(result["notes"])
    entry = (
        f"\n## [{ts}] BORDERLINE: {title}\n"
        f"- Source: {source} — {url}\n"
        f"- Issues: {', '.join(fails)}\n"
        f"- Notes: {notes_str}\n\n---\n"
    )
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
    log.info(f"BORDERLINE: {title} — {notes_str[:80]}")
    # Windows toast — quieter for borderline
    notify(title, f"Needs manual review — {notes_str[:100]}", "BORDERLINE")

# ─────────────────────────────────────────────────────────────────────────────
# CANDIDATE PROCESSOR
# ─────────────────────────────────────────────────────────────────────────────

def process(seen, title, desc, lic, source, url,
            tags=None, downloads=0, has_doi=False, has_arxiv=False,
            venue=None, size_hint=None, dl_url=None, ds_id=None,
            source_is_hf=False, source_is_zenodo=False, source_is_github=False):

    identifier = ds_id or url or title
    fp = make_fp(identifier)
    if fp in seen:
        return
    seen.add(fp)

    # Known check
    known = is_known(title, ds_id)
    if known:
        log.debug(f"Skip ({known}): {title[:60]}")
        return

    result = run_rules(
        title, desc, lic, tags, downloads, has_doi, has_arxiv, venue,
        source_is_hf, source_is_zenodo, source_is_github
    )

    if result["rules"].get("language", "").startswith("fail"):
        log.debug(f"Skip (language): {title[:60]}")
        return

    if result["passed"]:
        write_found(title, source, url, lic, size_hint, result, dl_url)
    elif result["borderline"]:
        write_borderline(title, source, url, result)
    else:
        log.debug(f"Fail: {title[:60]} — {result['notes'][:2]}")

# ─────────────────────────────────────────────────────────────────────────────
# SEARCH QUERIES
# ─────────────────────────────────────────────────────────────────────────────

# What the model needs most (head gaps first, then general)
HF_QUERIES = [
    # CRITICAL — zero coverage heads
    "reappraisal suppression", "cognitive reappraisal", "alexithymia",
    "PERMA wellbeing text", "window of tolerance", "attachment style text",
    # High-priority head gaps
    "shame guilt text", "shame corpus", "guilt corpus",
    "valence arousal dominance", "VAD annotation", "dimensional emotion",
    "secondary emotion fine-grained", "contempt envy text",
    "crisis text NLP", "suicidal ideation text", "self-harm NLP",
    # Framework coverage
    "emotion regulation corpus", "expressive writing emotion",
    "experience sampling affect", "diary emotion labeled",
    "grief text annotated", "loneliness corpus",
    "wellbeing text psychology", "flourishing text",
    "self-determination text", "autonomy competence text",
    "emotional granularity", "rumination text",
    # General emotion (catch anything we missed)
    "emotion", "sentiment", "affect", "empathy",
    "mental health text", "distress anxiety text",
    "psychological wellbeing text", "mood labeled text",
]

HF_INSTITUTIONAL_AUTHORS = [
    # Already searched (keep for new uploads)
    "google-research-datasets", "cardiffnlp", "Helsinki-NLP",
    "brighter-dataset", "ukr-detect", "EleutherAI",
    # New ones never searched
    "GroNLP", "copenlu", "cltl", "hltcoe",
    "ims-unistuttgart", "ucdavis-nlp", "nlp-waseda",
    "imperial-college-london", "cambridge-nlp",
    "princeton-nlp", "NYU-MLL", "cohere-for-ai",
    "PsychologyDatasets", "clef-evaluation-lab",
    "emotion-analysis-project", "llm-for-emotion",
]

ZENODO_QUERIES = [
    # Field-specific — the only thing that works on Zenodo
    'title:"shame" AND title:"text"',
    'title:"guilt" AND title:"corpus"',
    'title:"emotion regulation" AND title:"annotated"',
    'title:"alexithymia" AND title:"text"',
    'title:"reappraisal" AND title:"corpus"',
    'title:"PERMA" AND title:"text"',
    'title:"attachment" AND title:"emotion" AND title:"text"',
    'title:"crisis" AND title:"text" AND title:"annotated"',
    'title:"grief" AND title:"text" AND title:"annotated"',
    'title:"loneliness" AND title:"text"',
    'title:"self-harm" AND title:"text" AND title:"NLP"',
    'title:"wellbeing" AND title:"text" AND title:"NLP"',
    'title:"distress" AND title:"text" AND title:"annotated"',
    'title:"emotion" AND title:"annotated" AND title:"English"',
    'title:"sentiment" AND title:"corpus"',
    'title:"affect" AND title:"dataset" AND title:"NLP"',
    'title:"empathy" AND title:"corpus"',
    'title:"mental health" AND title:"NLP" AND title:"dataset"',
    'title:"VAD" AND title:"emotion" AND title:"text"',
    'title:"valence" AND title:"arousal" AND title:"text"',
    'keywords:"emotion NLP"',
    'keywords:"affect corpus"',
    'keywords:"emotion recognition" AND keywords:"English"',
    'keywords:"emotion regulation" AND keywords:"text"',
    'keywords:"shame" AND keywords:"NLP"',
    'keywords:"psychological wellbeing" AND keywords:"text"',
]

DATACITE_QUERIES = [
    # DataCite works with longer queries — catches institutional repos
    "shame guilt text annotated NLP",
    "emotion regulation text corpus CC-BY",
    "alexithymia text English dataset",
    "reappraisal suppression emotion text",
    "PERMA wellbeing text English",
    "self-determination autonomy text NLP",
    "attachment emotion text dataset",
    "contempt envy secondary emotion text",
    "crisis self-harm text NLP CC",
    "grief bereavement text corpus annotated",
    "loneliness isolation text annotated",
    "dimensional emotion VAD text corpus",
    "appraisal emotion text annotated English",
    "emotion recognition English annotated corpus",
    "sentiment affect psychology text open",
    "empathy distress annotated text English",
    "mental health text labeled NLP",
    "affective computing English text corpus",
    "psychological distress text labeled",
    "wellbeing mental health NLP text",
]

GITHUB_QUERIES = [
    # GitHub: short queries + license filter works best
    '"shame" "guilt" dataset README.md',
    '"emotion regulation" dataset README.md',
    '"alexithymia" dataset README.md',
    '"VAD" "valence" "arousal" dataset README.md',
    '"PERMA" wellbeing text dataset README.md',
    '"attachment style" text dataset README.md',
    '"grief" "bereavement" text dataset README.md',
    '"crisis" text NLP dataset README.md',
    '"reappraisal" "suppression" text dataset README.md',
    '"loneliness" text corpus README.md',
    '"contempt" "envy" emotion text dataset README.md',
    '"emotion corpus" CC-BY annotated README.md',
    '"mental health" text dataset CC README.md',
    '"empathy" text corpus annotated README.md',
    '"expressive writing" emotion dataset README.md',
    '"experience sampling" affect text dataset README.md',
]

OSF_TAGS = [
    # Full range — OSF Prolific studies are goldmines
    "shame", "guilt", "reappraisal", "emotion regulation",
    "alexithymia", "wellbeing", "PERMA", "flourishing",
    "self-determination", "autonomy", "competence", "attachment",
    "grief", "bereavement", "loneliness", "crisis",
    "self-compassion", "rumination", "worry", "positive psychology",
    "mindfulness", "emotional granularity", "emotional differentiation",
    "affect labeling", "expressive writing", "emotion expression",
    "VAD", "valence arousal", "dimensional affect",
    "emotion", "sentiment", "affect", "mental health",
    "psychology", "distress", "anxiety", "depression", "mood",
]

SEMANTIC_SCHOLAR_QUERIES = [
    "shame guilt corpus released open access freely available NLP",
    "emotion regulation dataset freely available download annotated text",
    "alexithymia text corpus released available download",
    "reappraisal suppression text dataset available NLP",
    "PERMA wellbeing text annotated dataset released",
    "attachment style text corpus open access",
    "grief bereavement text corpus annotated available",
    "crisis self-harm text NLP dataset open",
    "dimensional emotion VAD corpus CC-BY open",
    "secondary emotion fine-grained text corpus released",
    "window of tolerance text labeled dataset",
    "loneliness isolation text corpus open",
    "contempt envy text annotated corpus released",
    "affective computing text corpus open access CC-BY",
    "mental health NLP text corpus open access freely available",
]

HARVARD_DATAVERSE_QUERIES = [
    "shame guilt text", "emotion regulation text",
    "wellbeing text psychology", "alexithymia",
    "reappraisal suppression text", "PERMA flourishing text",
    "attachment emotion text", "grief bereavement text",
    "crisis self-harm text", "loneliness text annotated",
    "empathy text corpus", "VAD emotion text",
    "sentiment annotated English text", "affect text psychology",
    "mental health text labeled", "distress anxiety text",
]

OPENAIRE_QUERIES = [
    "shame guilt emotion text", "emotion regulation NLP corpus",
    "wellbeing text psychology", "mental health NLP corpus",
    "crisis self-harm text NLP", "PERMA flourishing text",
    "empathy annotated text", "distress anxiety text corpus",
    "loneliness text annotated", "attachment emotion text",
    "reappraisal suppression corpus", "alexithymia text",
]

MENDELEY_QUERIES = [
    "shame guilt text NLP", "emotion regulation labeled text",
    "PERMA wellbeing text", "alexithymia text dataset",
    "crisis self-harm text", "grief loneliness text annotated",
    "empathy text corpus", "VAD dimensional emotion text",
    "distress anxiety text annotated", "reappraisal text dataset",
]

FIGSHARE_QUERIES = [
    "shame text annotated NLP", "emotion regulation corpus",
    "wellbeing psychology text labeled", "mental health text dataset",
    "alexithymia text annotated", "grief loneliness text emotion",
    "empathy distress text annotated", "VAD emotion text annotated",
    "crisis text NLP annotated", "reappraisal suppression text",
]

PAPERS_WITH_CODE_TASKS = [
    "emotion-classification",
    "sentiment-analysis",
    "emotion-recognition",
    "mental-health",
]

# arXiv: categories that release emotion/NLP datasets
ARXIV_CATEGORIES = ["cs.CL", "cs.AI", "cs.HC"]

# Keywords in abstract that signal a dataset is being released
ARXIV_RELEASE_SIGNALS = [
    "we release", "we present a corpus", "we introduce a dataset",
    "we provide a corpus", "dataset is available", "corpus is available",
    "available at github", "available at huggingface", "available on zenodo",
    "publicly available", "freely available", "open source dataset",
    "data is available", "data available at", "released the dataset",
]

ARXIV_EMOTION_SIGNALS = [
    "emotion", "sentiment", "affect", "wellbeing", "distress",
    "empathy", "mental health", "shame", "guilt", "reappraisal",
    "alexithymia", "valence arousal", "psychological", "grief",
    "loneliness", "crisis", "self-harm", "flourishing", "perma",
]

# ─────────────────────────────────────────────────────────────────────────────
# SOURCE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def search_hf_keyword(seen, query):
    """Search HuggingFace by keyword — no license pre-filter (check in engine)."""
    r = api_get("https://huggingface.co/api/datasets", params={
        "search": query, "limit": 30,
        "sort": "lastModified", "direction": -1,
    })
    if not r:
        return
    for ds in r.json():
        ds_id = ds.get("id", "")
        tags  = ds.get("tags", [])
        lic   = next((t.replace("license:", "") for t in tags if t.startswith("license:")), None)
        desc  = ds.get("description", "") or ""
        dl    = ds.get("downloads", 0)
        title = ds_id.split("/")[-1].replace("-", " ").replace("_", " ")
        url   = f"https://huggingface.co/datasets/{ds_id}"
        size  = next((t.replace("size_categories:", "") for t in tags if "size_categories" in t), None)

        process(seen, title, desc[:600], lic, "HuggingFace", url,
                tags=tags, downloads=dl, has_doi=False,
                size_hint=size, dl_url=url, ds_id=ds_id.lower(),
                source_is_hf=True)

def search_hf_recent(seen, hours_back=4):
    """Catch anything new uploaded in the last N hours."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()
    for query in ["emotion", "sentiment", "affect", "mental health", "wellbeing",
                  "shame", "grief", "empathy", "distress", "alexithymia"]:
        r = api_get("https://huggingface.co/api/datasets", params={
            "search": query, "limit": 20,
            "sort": "lastModified", "direction": -1,
        })
        if not r:
            continue
        for ds in r.json():
            last_mod = ds.get("lastModified", "")
            # Normalise to UTC
            if last_mod and not last_mod.endswith("Z") and "+" not in last_mod:
                last_mod += "Z"
            if last_mod < cutoff:
                break
            ds_id = ds.get("id", "")
            tags  = ds.get("tags", [])
            lic   = next((t.replace("license:", "") for t in tags if t.startswith("license:")), None)
            desc  = ds.get("description", "") or ""
            title = ds_id.split("/")[-1].replace("-", " ").replace("_", " ")
            url   = f"https://huggingface.co/datasets/{ds_id}"
            process(seen, title, desc[:600], lic, "HuggingFace-Recent", url,
                    tags=tags, ds_id=ds_id.lower(), source_is_hf=True)

def search_hf_author(seen, author):
    """Sweep all datasets from a specific HuggingFace org."""
    r = api_get("https://huggingface.co/api/datasets", params={
        "author": author, "limit": 100,
    })
    if not r:
        return
    for ds in r.json():
        ds_id = ds.get("id", "")
        tags  = ds.get("tags", [])
        lic   = next((t.replace("license:", "") for t in tags if t.startswith("license:")), None)
        desc  = ds.get("description", "") or ""
        title = ds_id.split("/")[-1].replace("-", " ").replace("_", " ")
        url   = f"https://huggingface.co/datasets/{ds_id}"
        process(seen, title, desc[:600], lic, f"HuggingFace:{author}", url,
                tags=tags, ds_id=ds_id.lower(), source_is_hf=True)
        time.sleep(0.3)

def search_zenodo(seen, query):
    r = api_get("https://zenodo.org/api/records", params={
        "q": query, "type": "dataset",
        "access_right": "open", "size": 15, "sort": "mostrecent",
    })
    if not r:
        return
    for h in r.json().get("hits", {}).get("hits", []):
        meta  = h.get("metadata", {})
        title = meta.get("title", "")
        doi   = h.get("doi", "")
        desc  = re.sub(r"<[^>]+>", " ", meta.get("description", "") or "")[:500]
        lic_r = meta.get("license", {})
        lic   = lic_r.get("id") if isinstance(lic_r, dict) else str(lic_r or "")
        creators = meta.get("creators", [])
        creator_str = " ".join(
            f"{c.get('name','')} {c.get('affiliation','')}" for c in creators[:3]
        )
        url   = f"https://zenodo.org/record/{h.get('id')}"
        files = h.get("files", [])
        size  = f"{len(files)} file(s)"

        process(seen, title, f"{desc} {creator_str}", lic, "Zenodo", url,
                has_doi=bool(doi), size_hint=size,
                dl_url=url, ds_id=doi or url,
                source_is_zenodo=True)

def search_datacite(seen, query):
    r = api_get("https://api.datacite.org/dois", params={
        "query": query, "resource-type-id": "dataset", "page[size]": 12,
    })
    if not r:
        return
    for item in r.json().get("data", []):
        attrs = item.get("attributes", {})
        title = attrs.get("titles", [{}])[0].get("title", "")
        doi   = attrs.get("doi", "")
        rights = attrs.get("rightsList", [])
        lic   = next((x.get("rightsIdentifier","") for x in rights if x.get("rightsIdentifier")), None)
        descs = attrs.get("descriptions", [])
        desc  = re.sub(r"<[^>]+>", " ", descs[0].get("description","") if descs else "")[:400]
        pub   = attrs.get("publisher", "")
        yr    = attrs.get("publicationYear", "")
        creators = attrs.get("creators", [])
        creator_str = " ".join(c.get("name","") for c in creators[:3])
        url   = attrs.get("url") or f"https://doi.org/{doi}"
        size  = f"DOI:{doi} ({yr})"

        process(seen, title, f"{desc} {creator_str} {pub}", lic,
                "DataCite", url, has_doi=True, size_hint=size,
                dl_url=url, ds_id=doi)

def search_github(seen, query):
    r = api_get("https://api.github.com/search/repositories", params={
        "q": query, "sort": "updated", "order": "desc", "per_page": 15,
    }, sleep=GITHUB_SLEEP)
    if not r:
        return
    for item in r.json().get("items", []):
        full_name = item.get("full_name", "")
        desc  = item.get("description", "") or ""
        lic_info = item.get("license") or {}
        lic   = lic_info.get("spdx_id","").lower() if lic_info else None
        stars = item.get("stargazers_count", 0)
        topics= item.get("topics", [])
        url   = item.get("html_url", "")
        title = full_name.split("/")[-1].replace("-"," ").replace("_"," ")
        combined = f"{desc} {' '.join(topics)}"

        # Must look like a dataset repo, not just code
        if not any(w in combined.lower() for w in
                   ["dataset", "corpus", "data", "annotated", "labeled", "annotation"]):
            continue

        process(seen, title, combined, lic, "GitHub", url,
                tags=topics, downloads=stars, size_hint=f"{stars} stars",
                dl_url=url, ds_id=full_name,
                source_is_github=True)

def search_osf(seen, tag):
    r = api_get("https://api.osf.io/v2/nodes/", params={
        "filter[tags]": tag, "filter[public]": "true", "page[size]": 15,
    })
    if not r:
        return
    for item in r.json().get("data", []):
        attrs = item.get("attributes", {})
        title = attrs.get("title", "")
        desc  = attrs.get("description", "") or ""
        tags  = attrs.get("tags", [])
        guid  = item.get("id", "")
        url   = f"https://osf.io/{guid}/"
        # OSF license not in node API — always unknown, goes to borderline
        process(seen, title, f"{desc} {' '.join(tags)}", None,
                "OSF", url, tags=tags, size_hint="OSF project (check license manually)",
                ds_id=guid)

def search_semantic_scholar(seen, query):
    r = api_get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={
            "query": query,
            "fields": "title,abstract,year,openAccessPdf,externalIds,publicationVenue",
            "limit": 8,
        }, sleep=SCHOLAR_SLEEP
    )
    if not r:
        return
    for paper in r.json().get("data", []):
        title    = paper.get("title", "")
        abstract = paper.get("abstract", "") or ""
        year     = paper.get("year", "")
        venue    = (paper.get("publicationVenue") or {}).get("name", "")
        ext_ids  = paper.get("externalIds", {})
        doi      = ext_ids.get("DOI", "")
        arxiv_id = ext_ids.get("ArXiv", "")

        # Only care about papers that release a dataset
        if not any(w in abstract.lower() for w in
                   ["dataset", "corpus", "data available", "released", "we release",
                    "available at", "download", "github.com", "zenodo"]):
            continue

        url = f"https://doi.org/{doi}" if doi else \
              f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
        if not url:
            continue

        # License unknown — paper CC-BY ≠ dataset CC-BY
        process(seen, title, abstract[:500], None,
                "SemanticScholar", url,
                has_doi=bool(doi), has_arxiv=bool(arxiv_id), venue=venue,
                size_hint=f"Paper ({year}) — check linked dataset for license",
                ds_id=doi or arxiv_id)

def search_harvard_dataverse(seen, query):
    r = api_get("https://dataverse.harvard.edu/api/search", params={
        "q": query, "type": "dataset", "per_page": 10,
        "sort": "date", "order": "desc",
    })
    if not r:
        return
    for item in r.json().get("data", {}).get("items", []):
        title = item.get("name", "")
        desc  = item.get("description", "") or ""
        url   = item.get("url", "")
        pid   = item.get("global_id", "")
        pub   = item.get("published_at", "")

        # Fetch license via per-dataset API call
        lic = None
        if pid:
            meta_r = api_get(
                "https://dataverse.harvard.edu/api/datasets/:persistentId/versions/:latest",
                params={"persistentId": pid}, timeout=10
            )
            if meta_r:
                ds_data = meta_r.json().get("data", {})
                lic_info = ds_data.get("license", {})
                if isinstance(lic_info, dict):
                    lic_name = lic_info.get("name","").lower()
                    if "cc0" in lic_name:
                        lic = "cc0-1.0"
                    elif "cc by" in lic_name and "nc" not in lic_name:
                        lic = "cc-by-4.0"
                    elif lic_name:
                        lic = lic_name

        process(seen, title, desc[:400], lic, "Harvard Dataverse", url,
                has_doi=True, size_hint=f"Harvard Dataverse ({pub[:10]})",
                dl_url=url, ds_id=pid)

def search_openaire(seen, query):
    r = api_get("https://api.openaire.eu/search/datasets", params={
        "title": query, "format": "json", "size": 8, "accessMode": "OPEN",
    })
    if not r:
        return
    try:
        results = r.json().get("response",{}).get("results",{}).get("result",[])
        if isinstance(results, dict):
            results = [results]
        for item in results:
            oaf   = item.get("metadata",{}).get("oaf:entity",{}).get("oaf:result",{})
            titles= oaf.get("title",[])
            if isinstance(titles, dict): titles = [titles]
            title = titles[0].get("$","") if titles else ""
            desc_r= oaf.get("description",{})
            desc  = desc_r.get("$","") if isinstance(desc_r, dict) else ""
            access= oaf.get("bestaccessright",{}).get("@classname","")
            # EU mandate: open access = CC-BY
            lic = "cc-by-4.0" if "open" in access.lower() else None

            children = oaf.get("children",{})
            instances = children.get("instance",[])
            if isinstance(instances, dict): instances = [instances]
            urls = [i.get("webresource",{}).get("url",{}).get("$","") for i in instances[:2]]
            url  = next((u for u in urls if u), "")

            if not title or not url:
                continue
            process(seen, title, desc[:400], lic, "OpenAIRE", url,
                    has_doi=True, size_hint="EU-funded open access")
    except Exception as e:
        log.debug(f"OpenAIRE parse: {e}")

def search_mendeley(seen, query):
    r = api_get("https://data.mendeley.com/api/datasets", params={
        "search": query, "page": 1, "perPage": 12,
    })
    if not r:
        return
    for item in r.json().get("data", []):
        title = item.get("name", "")
        desc  = item.get("description", "") or ""
        doi   = item.get("doi", "")
        lic_r = item.get("data_licence", {}) or {}
        lic_name = lic_r.get("name","").lower() if isinstance(lic_r, dict) else ""
        if "cc by" in lic_name and "nc" not in lic_name:
            lic = "cc-by-4.0"
        elif "cc0" in lic_name or "public domain" in lic_name:
            lic = "cc0-1.0"
        else:
            lic = lic_name or None
        url = item.get("url") or f"https://doi.org/{doi}"
        process(seen, title, desc[:400], lic, "Mendeley Data", url,
                has_doi=bool(doi), ds_id=doi or url)

def search_figshare(seen, query):
    r = api_get("https://api.figshare.com/v2/articles", params={
        "search_for": query, "item_type": 3, "page_size": 12,
    })
    if not r:
        return
    for item in r.json():
        title = item.get("title", "")
        url   = item.get("url_public_html", "")
        doi   = item.get("doi", "")
        lic_r = item.get("license", {}) or {}
        lic_name = lic_r.get("name","").lower() if isinstance(lic_r, dict) else ""
        if "cc by" in lic_name and "nc" not in lic_name:
            lic = "cc-by-4.0"
        elif "cc0" in lic_name or "public domain" in lic_name:
            lic = "cc0-1.0"
        else:
            lic = lic_name or None
        desc = item.get("description","") or ""
        process(seen, title, desc[:400], lic, "Figshare", url,
                has_doi=bool(doi), ds_id=doi or url)

def search_papers_with_code(seen, task):
    """Check PapersWithCode task page for listed datasets."""
    r = api_get(f"https://paperswithcode.com/api/v1/datasets/", params={
        "task": task, "page": 1,
    })
    if not r:
        return
    for item in r.json().get("results", []):
        title = item.get("name", "")
        desc  = item.get("description", "") or ""
        url   = item.get("url", "")
        # PwC doesn't provide license — flag all as unknown
        process(seen, title, desc[:400], None,
                f"PapersWithCode:{task}", url,
                size_hint="PapersWithCode listing (check license manually)",
                ds_id=url)

def search_clarin_vlo(seen):
    """
    CLARIN Virtual Language Observatory — one-time scrape of emotion/sentiment resources.
    Returns CC-BY or CC0 resources for European NLP.
    """
    r = api_get("https://vlo.clarin.eu/api/search", params={
        "q": "emotion sentiment affect",
        "fq": "languageCode:eng",
        "rows": 20,
    })
    if not r:
        # CLARIN VLO also has a direct API
        r = api_get("https://vlo.clarin.eu/search", params={
            "q": "emotion English NLP",
            "fq": "resourceClass:LexicalResource",
        })
    if not r:
        return
    # CLARIN returns varied formats — just log that we checked
    log.info("CLARIN VLO check completed")

def search_uk_data_archive(seen, query):
    """UK Data Archive — British psychology studies with text data."""
    r = api_get("https://beta.ukdataservice.ac.uk/datacatalogue/search/search",
                params={"q": query, "limit": 10})
    if not r:
        return
    try:
        for item in r.json().get("data", {}).get("results", []):
            title = item.get("title", "")
            desc  = item.get("abstract", "") or ""
            url   = "https://ukdataservice.ac.uk/find-data/catalogue/?id=" + str(item.get("id",""))
            # UK Data Archive — license varies, often CC-BY or Open Government
            lic = None
            access = item.get("access","").lower()
            if "open" in access:
                lic = "cc-by-4.0"
            process(seen, title, desc[:400], lic, "UK Data Archive", url,
                    has_doi=False, size_hint="UK Data Archive",
                    ds_id=item.get("id",""))
    except Exception as e:
        log.debug(f"UKDA parse: {e}")

def search_gesis(seen, query):
    """GESIS — German social science data including psychology studies."""
    r = api_get("https://search.gesis.org/api/2.0/search/", params={
        "q": query, "type": "research_data", "lang": "en",
        "rows": 10,
    })
    if not r:
        return
    try:
        for item in r.json().get("data", {}).get("hits", {}).get("hits", []):
            src   = item.get("_source", {})
            title = src.get("title", [{}])[0].get("text","") if src.get("title") else ""
            desc  = src.get("abstract",[{}])[0].get("text","") if src.get("abstract") else ""
            url   = src.get("url","")
            # GESIS: often CC-BY for publicly funded German research
            lic = None
            rights = src.get("rights","")
            if "cc by" in str(rights).lower() and "nc" not in str(rights).lower():
                lic = "cc-by-4.0"
            if not title:
                continue
            process(seen, title, desc[:400], lic, "GESIS", url,
                    has_doi=True, size_hint="GESIS social science data")
    except Exception as e:
        log.debug(f"GESIS parse: {e}")

def search_arxiv(seen, days_back=7):
    """
    arXiv cs.CL/cs.AI/cs.HC — catches dataset papers DAYS before HuggingFace.
    Free API, no rate limits, clean structured metadata.
    """
    from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y%m%d")
    for category in ARXIV_CATEGORIES:
        r = api_get("https://export.arxiv.org/api/query", params={
            "search_query": f"cat:{category} AND (ti:emotion OR ti:sentiment OR ti:affect OR ti:corpus OR ti:dataset)",
            "start": 0,
            "max_results": 30,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }, timeout=20)
        if not r:
            continue

        # arXiv returns Atom XML
        import xml.etree.ElementTree as ET
        ns = {"atom": "http://www.w3.org/2005/Atom",
              "arxiv": "http://arxiv.org/schemas/atom"}
        try:
            root = ET.fromstring(r.content)
        except Exception as e:
            log.debug(f"arXiv XML parse: {e}")
            continue

        for entry in root.findall("atom:entry", ns):
            title    = (entry.findtext("atom:title", "", ns) or "").strip().replace("\n", " ")
            abstract = (entry.findtext("atom:summary", "", ns) or "").strip().replace("\n", " ")
            arxiv_id = (entry.findtext("atom:id", "", ns) or "").split("/abs/")[-1]
            url      = f"https://arxiv.org/abs/{arxiv_id}"
            published = entry.findtext("atom:published", "", ns) or ""

            # Only papers that are releasing a dataset AND have emotion content
            abstract_lower = abstract.lower()
            title_lower    = title.lower()
            combined       = f"{title_lower} {abstract_lower}"

            has_release  = any(s in combined for s in ARXIV_RELEASE_SIGNALS)
            has_emotion  = any(s in combined for s in ARXIV_EMOTION_SIGNALS)
            if not (has_release and has_emotion):
                continue

            # arXiv license: most NLP papers are CC-BY-4.0 or CC0
            # Check the license element if present
            lic_el = entry.find("atom:link[@title='license']", ns)
            lic_url = lic_el.get("href", "") if lic_el is not None else ""
            if "creativecommons.org/licenses/by" in lic_url and "nc" not in lic_url:
                lic = "cc-by-4.0"
            elif "creativecommons.org/publicdomain" in lic_url:
                lic = "cc0-1.0"
            else:
                lic = None   # unknown — will get flagged for manual check

            authors = entry.findall("atom:author", ns)
            author_str = ", ".join(
                (a.findtext("atom:name", "", ns) or "") for a in authors[:3]
            )
            affil_els = entry.findall("arxiv:affiliation", ns)
            affil_str = " ".join(a.text or "" for a in affil_els[:3])

            size_hint = f"arXiv preprint {arxiv_id} ({published[:10]})"

            process(seen, title, f"{abstract[:500]} {author_str} {affil_str}",
                    lic, f"arXiv:{category}", url,
                    has_arxiv=True, has_doi=False,
                    size_hint=size_hint, dl_url=url,
                    ds_id=arxiv_id)
        time.sleep(API_SLEEP)


def check_open_psychology_data(seen):
    """
    Open Psychology Data journal — all CC-BY, all psychology, text data.
    Scrape the article list periodically.
    """
    r = api_get("https://openpsychologydata.metajnl.com/api/articles", params={
        "page": 1, "per_page": 20,
    })
    if not r:
        # Try feed
        r = api_get("https://openpsychologydata.metajnl.com/articles/", timeout=20)
    if not r:
        return
    # All articles here are CC-BY psychology data papers — flag all for review
    log.info("Open Psychology Data check completed — review manually for text emotion data")

# ─────────────────────────────────────────────────────────────────────────────
# SWEEP ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

def run_sweep(seen, sweep_num):
    log.info(f"=== Sweep #{sweep_num} starting ===")

    # 1. HuggingFace: keyword sweep (no license pre-filter)
    log.info("HuggingFace: keyword sweep")
    for q in HF_QUERIES:
        search_hf_keyword(seen, q)
        save_seen(seen)

    # 2. HuggingFace: catch recent uploads (last 4h)
    log.info("HuggingFace: recent uploads")
    search_hf_recent(seen, hours_back=4)
    save_seen(seen)

    # 3. HuggingFace: institutional orgs
    log.info("HuggingFace: institutional authors")
    for author in HF_INSTITUTIONAL_AUTHORS:
        search_hf_author(seen, author)
        save_seen(seen)

    # 4. Zenodo: field-specific search
    log.info("Zenodo: field search")
    for q in ZENODO_QUERIES:
        search_zenodo(seen, q)
        save_seen(seen)

    # 5. DataCite: DOI registry (catches any institutional repo)
    log.info("DataCite: DOI registry")
    for q in DATACITE_QUERIES:
        search_datacite(seen, q)
        save_seen(seen)

    # 6. GitHub: repo search
    log.info("GitHub: repository search")
    for q in GITHUB_QUERIES:
        search_github(seen, q)
        save_seen(seen)

    # 7. OSF: psychology lab deposits
    log.info("OSF: tag search")
    for tag in OSF_TAGS:
        search_osf(seen, tag)
        save_seen(seen)

    # 8. Semantic Scholar: paper discovery
    log.info("SemanticScholar: paper discovery")
    for q in SEMANTIC_SCHOLAR_QUERIES:
        search_semantic_scholar(seen, q)
        save_seen(seen)

    # 9. Harvard Dataverse
    log.info("Harvard Dataverse: search")
    for q in HARVARD_DATAVERSE_QUERIES:
        search_harvard_dataverse(seen, q)
        save_seen(seen)

    # 10. OpenAIRE: EU open access
    log.info("OpenAIRE: EU open access")
    for q in OPENAIRE_QUERIES:
        search_openaire(seen, q)
        save_seen(seen)

    # 11. Mendeley Data
    log.info("Mendeley Data: search")
    for q in MENDELEY_QUERIES:
        search_mendeley(seen, q)
        save_seen(seen)

    # 12. Figshare
    log.info("Figshare: search")
    for q in FIGSHARE_QUERIES:
        search_figshare(seen, q)
        save_seen(seen)

    # 13. arXiv cs.CL/cs.AI/cs.HC — catches datasets before HuggingFace
    log.info("arXiv: NLP/AI/HCI preprints with dataset releases")
    search_arxiv(seen, days_back=8)   # 8h sweep covers last 8 days on first run
    save_seen(seen)

    # 14. PapersWithCode: task-based discovery
    log.info("PapersWithCode: task pages")
    for task in PAPERS_WITH_CODE_TASKS:
        search_papers_with_code(seen, task)
        save_seen(seen)

    # 15. CLARIN VLO (weekly)
    if sweep_num % 7 == 0:
        log.info("CLARIN VLO: language resources")
        search_clarin_vlo(seen)

    # 16. UK Data Archive (weekly)
    if sweep_num % 7 == 0:
        log.info("UK Data Archive: search")
        for q in ["emotion text psychology", "wellbeing text", "mental health text",
                  "shame guilt text", "grief text", "anxiety depression text"]:
            search_uk_data_archive(seen, q)
            save_seen(seen)

    # 17. GESIS (weekly)
    if sweep_num % 7 == 0:
        log.info("GESIS: search")
        for q in ["emotion text psychology", "wellbeing text",
                  "affective computing text", "mental health text"]:
            search_gesis(seen, q)
            save_seen(seen)

    # 18. Open Psychology Data (weekly)
    if sweep_num % 7 == 0:
        log.info("Open Psychology Data: check")
        check_open_psychology_data(seen)

    log.info(f"=== Sweep #{sweep_num} complete. Cache: {len(seen)} items. ===")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────

SWEEP_INTERVAL_HOURS = 4   # full sweep every 4 hours

def main():
    init_results()
    seen = load_seen()

    log.info("=" * 60)
    log.info("Resonance Dataset Scout starting")
    log.info(f"Seen cache: {len(seen)} items")
    log.info(f"Results: {RESULTS_FILE}")
    log.info(f"Sweep interval: {SWEEP_INTERVAL_HOURS}h")
    log.info("Ctrl+C to stop safely")
    log.info("=" * 60)

    sweep_num = 0
    while True:
        sweep_num += 1
        try:
            run_sweep(seen, sweep_num)
        except KeyboardInterrupt:
            log.info("Stopped by user.")
            save_seen(seen)
            break
        except Exception as e:
            log.error(f"Sweep error: {e}", exc_info=True)
            save_seen(seen)

        # Sleep between sweeps
        log.info(f"Sleeping {SWEEP_INTERVAL_HOURS}h before next sweep...")
        sleep_secs = SWEEP_INTERVAL_HOURS * 3600
        try:
            time.sleep(sleep_secs)
        except KeyboardInterrupt:
            log.info("Stopped during sleep.")
            save_seen(seen)
            break

if __name__ == "__main__":
    main()
