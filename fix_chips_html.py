# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_chips_html.py

content = open('resonance/templates/dashboard.html', 'r', encoding='utf-8').read()

# Fix chip rendering - remove c.e reference
old = "    el.textContent=c.e+' '+c.n;"
new = "    el.textContent=c.n;"

if old in content:
    content = content.replace(old, new)
    print('Fixed: chip rendering - removed emoji reference')
else:
    print('WARNING: pattern not found, checking...')
    for i, line in enumerate(content.split('\n')):
        if 'c.e' in line or 'textContent' in line:
            print(f'{i}: {line}')

# Also fix the saved state text
old2 = "el.textContent='saved: '+c.n;"
new2 = "el.textContent='saved: '+c.n;"  # already correct

# Fix the header emoji - replace emoji with text label
old3 = '''      <div class="feeling-emoji">${data.pill.emoji}</div>'''
new3 = '''      <div class="feeling-emoji">${data.pill.word.toUpperCase()}</div>'''

if old3 in content:
    content = content.replace(old3, new3)
    print('Fixed: header label uses word instead of emoji key')

open('resonance/templates/dashboard.html', 'w', encoding='utf-8').write(content)
print('Done.')
