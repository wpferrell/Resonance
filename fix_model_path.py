# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_model_path.py

from pathlib import Path

# Fix model_loader.py — add label_map.json download
content = open('resonance/model_loader.py', 'r', encoding='utf-8').read()

old = '''        hf_hub_download(
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
        )'''

new = '''        hf_hub_download(
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
        )'''

if old in content:
    content = content.replace(old, new)
    open('resonance/model_loader.py', 'w', encoding='utf-8').write(content)
    print('Fixed: model_loader.py — label_map.json download added')
else:
    print('WARNING: pattern not found in model_loader.py')

# Fix extractor.py — point MODEL_PATH to ~/.resonance/model_cache
content = open('resonance/extractor.py', 'r', encoding='utf-8').read()

old = '''MODEL_PATH = Path(__file__).parent / "resonance" / "model"
if not MODEL_PATH.exists():
    MODEL_PATH = Path(__file__).parent / "model"'''

new = '''MODEL_PATH = Path.home() / ".resonance" / "model_cache"
if not MODEL_PATH.exists():
    # fallback to local model directory for development
    _local = Path(__file__).parent / "model"
    if _local.exists():
        MODEL_PATH = _local'''

if old in content:
    content = content.replace(old, new)
    open('resonance/extractor.py', 'w', encoding='utf-8').write(content)
    print('Fixed: extractor.py — MODEL_PATH updated to ~/.resonance/model_cache')
else:
    print('WARNING: pattern not found in extractor.py')

print('Done.')
