# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_paths.py

from pathlib import Path

files_to_fix = {
    'resonance/config.py': [
        ('CONFIG_DIR = Path("resonance_data")', 'CONFIG_DIR = Path.home() / ".resonance"'),
    ],
    'resonance/feedback.py': [
        ('QUEUE_DIR = Path("resonance_data/feedback_queue")', 'QUEUE_DIR = Path.home() / ".resonance" / "feedback_queue"'),
    ],
}

for filepath, replacements in files_to_fix.items():
    content = open(filepath, 'r', encoding='utf-8').read()
    for old, new in replacements:
        content = content.replace(old, new)
    open(filepath, 'w', encoding='utf-8').write(content)
    print(f'Fixed: {filepath}')

# Fix temporal_graph.py — add Path import and fix hardcoded path
tg = open('resonance/temporal_graph.py', 'r', encoding='utf-8').read()
if 'from pathlib import Path' not in tg:
    tg = 'from pathlib import Path\n' + tg
tg = tg.replace(
    '"C:/Users/Shadow/Documents/Resonance/resonance/resonance_data/temporal"',
    'str(Path.home() / ".resonance" / "temporal")'
)
open('resonance/temporal_graph.py', 'w', encoding='utf-8').write(tg)
print('Fixed: resonance/temporal_graph.py')

# Fix reinforcement.py — add Path import and fix hardcoded path
rf = open('resonance/reinforcement.py', 'r', encoding='utf-8').read()
if 'from pathlib import Path' not in rf:
    rf = 'from pathlib import Path\n' + rf
rf = rf.replace(
    '"C:/Users/Shadow/Documents/Resonance/resonance/resonance_data/reinforcement"',
    'str(Path.home() / ".resonance" / "reinforcement")'
)
open('resonance/reinforcement.py', 'w', encoding='utf-8').write(rf)
print('Fixed: resonance/reinforcement.py')

print('All paths fixed. All data now stored in ~/.resonance/')
