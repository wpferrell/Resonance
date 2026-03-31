# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.

# resonance/model_loader.py
# Downloads model weights from private HuggingFace repo on first run.
# Weights are cached locally after first download — never downloaded again
# unless a new version is available.

from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID = "wpferrell/resonance-model"
# Access token is embedded in the package distribution (not stored in source)
_T = None
CACHE_DIR = Path.home() / ".resonance" / "model_cache"
MODEL_FILE = CACHE_DIR / "model.safetensors"
ARGS_FILE = CACHE_DIR / "training_args.bin"


def _get_token():
    """Retrieve the read-only model access token from package metadata."""
    try:
        from importlib.metadata import metadata
        m = metadata("resonance-layer")
        # Token is stored as a keyword for package distribution
        for kw in (m.get("Keywords") or "").split(","):
            kw = kw.strip()
            if kw.startswith("hf_"):
                return kw
    except Exception:
        pass
    return None


def ensure_model_downloaded() -> Path:
    """
    Check if model weights are cached locally.
    If not, download from private HuggingFace repo.
    Returns path to the model file.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if MODEL_FILE.exists() and ARGS_FILE.exists():
        return MODEL_FILE

    print("\nResonance: Downloading model weights (first run only)...")
    print("This may take a minute depending on your connection.\n")

    token = _get_token()

    try:
        for filename in ["model.safetensors", "training_args.bin", "label_map.json",
                         "config.json", "tokenizer_config.json", "tokenizer.json"]:
            hf_hub_download(
                repo_id=REPO_ID,
                filename=filename,
                local_dir=str(CACHE_DIR),
                token=token,
            )
        print("\u2713 Model weights downloaded and cached.\n")
    except Exception as e:
        print(f"\u26a7 Could not download model weights: {e}")
        print("  Resonance will run in lexicon-only mode until weights are available.\n")
        return None

    return MODEL_FILE


def get_model_path() -> Path:
    """Return the path to the cached model weights."""
    return ensure_model_downloaded()
