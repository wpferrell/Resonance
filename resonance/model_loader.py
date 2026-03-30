# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.

# resonance/model_loader.py
# Downloads model weights from private HuggingFace repo on first run.
# Weights are cached locally after first download — never downloaded again
# unless a new version is available.

from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID = "wpferrell/resonance-model"
HF_TOKEN = "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"
CACHE_DIR = Path.home() / ".resonance" / "model_cache"
MODEL_FILE = CACHE_DIR / "model.safetensors"
ARGS_FILE = CACHE_DIR / "training_args.bin"


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

    try:
        hf_hub_download(
            repo_id=REPO_ID,
            filename="model.safetensors",
            local_dir=str(CACHE_DIR),
            token=HF_TOKEN,
        )
        hf_hub_download(
            repo_id=REPO_ID,
            filename="training_args.bin",
            local_dir=str(CACHE_DIR),
            token=HF_TOKEN,
        )
        hf_hub_download(
            repo_id=REPO_ID,
            filename="label_map.json",
            local_dir=str(CACHE_DIR),
            token=HF_TOKEN,
        )
        hf_hub_download(
            repo_id=REPO_ID,
            filename="config.json",
            local_dir=str(CACHE_DIR),
            token=HF_TOKEN,
        )
        hf_hub_download(
            repo_id=REPO_ID,
            filename="tokenizer_config.json",
            local_dir=str(CACHE_DIR),
            token=HF_TOKEN,
        )
        hf_hub_download(
            repo_id=REPO_ID,
            filename="tokenizer.json",
            local_dir=str(CACHE_DIR),
            token=HF_TOKEN,
        )
        print("✓ Model weights downloaded and cached.\n")
    except Exception as e:
        print(f"⚧ Could not download model weights: {e}")
        print("  Resonance will run in lexicon-only mode until weights are available.\n")
        return None

    return MODEL_FILE


def get_model_path() -> Path:
    """Return the path to the cached model weights."""
    return ensure_model_downloaded()
