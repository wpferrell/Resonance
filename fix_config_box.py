# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_config_box.py

content = open('resonance/config.py', 'r', encoding='utf-8').read()

# Fix the box - each line must be exactly 60 chars wide including the | | borders
# Format: |  TEXT<spaces>|  where total width = 60

def box_line(text=''):
    width = 58  # inner width between | and |
    padded = '  ' + text
    spaces = width - len(padded)
    if spaces < 0:
        padded = padded[:width]
        spaces = 0
    return f'|{padded}{" " * spaces}|'

old_box = '''    print("\\n+----------------------------------------------------------+")
    print("|                                                       |")
    print("|  Before we begin — one question:                     |")
    print("|                                                       |")
    print("|  Help improve Resonance by sharing anonymous          |")
    print("|  correction data?                                     |")
    print("|                                                       |")
    print("|  Corrections only. No message text. No identity.     |")
    print("|  You can change this any time:                       |")
    print("|  resonance config --feedback on/off                  |")
    print("|                                                       |")
    print("|  [1] Yes, I want to help improve Resonance           |")
    print("|  [2] No, keep everything local                       |")
    print("|                                                       |")
    print("+----------------------------------------------------------+")'''

# Build perfectly aligned box
sep = '+' + '-' * 58 + '+'
lines = [
    box_line(),
    box_line('Before we begin - one question:'),
    box_line(),
    box_line('Help improve Resonance by sharing anonymous'),
    box_line('correction data?'),
    box_line(),
    box_line('Corrections only. No message text. No identity.'),
    box_line('You can change this any time:'),
    box_line('resonance config --feedback on/off'),
    box_line(),
    box_line('[1] Yes, I want to help improve Resonance'),
    box_line('[2] No, keep everything local'),
    box_line(),
]

new_box_lines = [f'    print("\\n{sep}")']
for line in lines:
    new_box_lines.append(f'    print("{line}")')
new_box_lines.append(f'    print("{sep}")')

new_box = '\n'.join(new_box_lines)

if old_box in content:
    content = content.replace(old_box, new_box)
    open('resonance/config.py', 'w', encoding='utf-8').write(content)
    print('Fixed: config.py box alignment')
else:
    print('WARNING: box pattern not found - showing what is there:')
    for line in content.split('\n'):
        if 'print(' in line and ('|' in line or '+' in line or 'before' in line.lower()):
            print(repr(line))

# Now fix the Qdrant warning by suppressing it in __init__.py
init_content = open('resonance/__init__.py', 'r', encoding='utf-8').read()

suppress = '''import warnings
warnings.filterwarnings("ignore", message=".*sys.meta_path.*")
warnings.filterwarnings("ignore", category=ImportError)
'''

if 'warnings.filterwarnings' not in init_content:
    # Add after the first import line
    init_content = suppress + init_content
    open('resonance/__init__.py', 'w', encoding='utf-8').write(init_content)
    print('Fixed: __init__.py - Qdrant shutdown warning suppressed')
else:
    print('Warning suppression already present')

print('Done.')
