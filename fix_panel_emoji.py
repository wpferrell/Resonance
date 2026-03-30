# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_panel_emoji.py

# Fix dashboard.py - add emoji back to pill data
content = open('resonance/dashboard.py', 'r', encoding='utf-8').read()

old = '''    emotion_map = {
        "joy":      {"word": "happy",      "color": "#68d391", "emoji": "happy",  "short": "Lighter today."},
        "anger":    {"word": "angry",      "color": "#fc8181", "emoji": "angry",  "short": "Something's been crossed."},
        "fear":     {"word": "anxious",    "color": "#f6ad55", "emoji": "anxious","short": "On edge right now."},
        "sadness":  {"word": "sad",        "color": "#a0aec0", "emoji": "sad",    "short": "Something's weighing on you."},
        "surprise": {"word": "surprised",  "color": "#f6ad55", "emoji": "surprised","short": "Didn't see that coming."},
        "shame":    {"word": "ashamed",    "color": "#ed93b1", "emoji": "ashamed","short": "Something feels wrong inside."},
        "neutral":  {"word": "okay",       "color": "#4fd1c5", "emoji": "okay",   "short": "Getting by."},
    }'''

new = '''    emotion_map = {
        "joy":      {"word": "happy",      "color": "#68d391", "emoji": "😊", "short": "Lighter today."},
        "anger":    {"word": "angry",      "color": "#fc8181", "emoji": "😡", "short": "Something's been crossed."},
        "fear":     {"word": "anxious",    "color": "#f6ad55", "emoji": "😟", "short": "On edge right now."},
        "sadness":  {"word": "sad",        "color": "#a0aec0", "emoji": "😔", "short": "Something's weighing on you."},
        "surprise": {"word": "surprised",  "color": "#f6ad55", "emoji": "😮", "short": "Didn't see that coming."},
        "shame":    {"word": "ashamed",    "color": "#ed93b1", "emoji": "😳", "short": "Something feels wrong inside."},
        "neutral":  {"word": "okay",       "color": "#4fd1c5", "emoji": "🙂", "short": "Getting by."},
    }'''

if old in content:
    content = content.replace(old, new)
    open('resonance/dashboard.py', 'w', encoding='utf-8').write(content)
    print('Fixed: emoji restored in pill data')
else:
    print('WARNING: pattern not found')

# Fix dashboard.html - restore large emoji above feeling word
html = open('resonance/templates/dashboard.html', 'r', encoding='utf-8').read()

old_h = '      <div class="feeling-emoji">${data.pill.word.toUpperCase()}</div>'
new_h = '      <span style="font-size:44px;display:block;margin-bottom:10px;line-height:1">${data.pill.emoji}</span>'

if old_h in html:
    html = html.replace(old_h, new_h)
    open('resonance/templates/dashboard.html', 'w', encoding='utf-8').write(html)
    print('Fixed: large emoji restored above feeling word')
else:
    # try alternate
    old_h2 = '      <div class="feeling-emoji">${data.pill.emoji}</div>'
    if old_h2 in html:
        html = html.replace(old_h2, '      <span style="font-size:44px;display:block;margin-bottom:10px;line-height:1">${data.pill.emoji}</span>')
        open('resonance/templates/dashboard.html', 'w', encoding='utf-8').write(html)
        print('Fixed: large emoji restored (alternate pattern)')
    else:
        print('WARNING: HTML emoji pattern not found, checking...')
        for i, line in enumerate(html.split('\n')):
            if 'feeling-emoji' in line or 'pill.emoji' in line:
                print(f'{i}: {repr(line)}')

print('Done.')
