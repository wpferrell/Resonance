# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1  -  see LICENSE for details.

# resonance/model_loader.py
# Downloads model weights from HuggingFace on first run.
# Weights are cached locally after first download  -  never downloaded again.

from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID = "wpferrell/resonance-model"
CACHE_DIR = Path.home() / ".resonance" / "model_cache"

FILES = [
    "model.safetensors",
    "config.json",
    "tokenizer_config.json",
    "tokenizer.json",
    "label_map.json",
    "confidence_profile.json",
]


def ensure_model_downloaded() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    missing = [f for f in FILES if not (CACHE_DIR / f).exists()]
    if not missing:
        return CACHE_DIR
    print("Downloading Resonance model weights (first run only)...")
    print("This may take a minute depending on your connection.")
    print("")
    for i, filename in enumerate(missing, 1):
        print(f"  [{i}/{len(missing)}] {filename}...")
        hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            local_dir=str(CACHE_DIR),
        )
    print("")
    print("OK: Model weights downloaded and cached.")
    print("")
    return CACHE_DIR
