# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_final_panel.py

from pathlib import Path

# Fix dashboard.py - increase browser open delay to 15 seconds
for filepath in ['resonance/dashboard.py', r'C:\Users\Shadow\resonance\Lib\site-packages\resonance\dashboard.py']:
    try:
        content = open(filepath, 'r', encoding='utf-8').read()
        content = content.replace('time.sleep(1.5)', 'time.sleep(15)')
        content = content.replace('time.sleep(3)', 'time.sleep(15)')
        open(filepath, 'w', encoding='utf-8').write(content)
        print(f'Fixed browser delay: {filepath}')
    except Exception as e:
        print(f'Error: {filepath}: {e}')

print('Done. Browser will open after 15 seconds.')
