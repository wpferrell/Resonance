# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_model_loader.py

content = open('resonance/model_loader.py', 'r', encoding='utf-8').read()

old = '''        hf_hub_download(
            repo_id=REPO_ID,
            filename="label_map.json",
            local_dir=str(CACHE_DIR),
            token=HF_TOKEN,
        )'''

new = '''        hf_hub_download(
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
        )'''

if old in content:
    content = content.replace(old, new)
    open('resonance/model_loader.py', 'w', encoding='utf-8').write(content)
    print('Fixed: model_loader.py — tokenizer files added')
else:
    print('WARNING: pattern not found — showing current download section:')
    for i, line in enumerate(content.split('\n')):
        if 'hf_hub_download' in line or 'filename' in line:
            print(f'{i}: {line}')
