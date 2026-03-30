# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_suppress_diagnostics.py

content = open('resonance/extractor.py', 'r', encoding='utf-8').read()

# Suppress the verbose model load messages - keep only errors
old1 = '''            print(f"[Resonance] Trained model loaded from {MODEL_PATH}")
            print(f"[Resonance] Classes: {list(self._label_map.values())}")
            print(f"[Resonance] Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")'''

new1 = ''

if old1 in content:
    content = content.replace(old1, new1)
    print('Fixed: removed verbose model load messages')
else:
    print('WARNING: verbose messages pattern not found - checking...')
    for i, line in enumerate(content.split('\n')):
        if 'Trained model loaded' in line or 'Classes:' in line or 'Device:' in line:
            print(f'{i}: {line}')

# Also suppress the "No trained model found" message - replace with silent fallback
old2 = '                print("[Resonance] No trained model found — using rule-based fallback.")'
new2 = ''

if old2 in content:
    content = content.replace(old2, new2)
    print('Fixed: removed fallback message')

# Also fix model load failed message to be silent
old3 = '            print(f"[Resonance] Model load failed ({e}) — using rule-based fallback.")'
new3 = ''

if old3 in content:
    content = content.replace(old3, new3)
    print('Fixed: removed model load failed message')

open('resonance/extractor.py', 'w', encoding='utf-8').write(content)
print('Done.')
