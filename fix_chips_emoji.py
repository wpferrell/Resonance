# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_chips_emoji.py

content = open('resonance/dashboard.py', 'r', encoding='utf-8').read()

# Add emoji back to chip_map
old = '''    chip_map = {
        "happy":   [{"n":"happy","d":True},{"n":"calm"},{"n":"excited"},{"n":"just okay"}],
        "angry":   [{"n":"angry","d":True},{"n":"frustrated"},{"n":"hurt underneath"},{"n":"irritated"}],
        "fear":    [{"n":"worried","d":True},{"n":"overwhelmed"},{"n":"stressed"},{"n":"uneasy"}],
        "sadness": [{"n":"sad","d":True},{"n":"empty"},{"n":"hurt"},{"n":"done"}],
        "neutral": [{"n":"okay","d":True},{"n":"calm"},{"n":"numb"},{"n":"a little down"}],
        "shame":   [{"n":"ashamed","d":True},{"n":"embarrassed"},{"n":"guilty"},{"n":"regretful"}],
        "anger":   [{"n":"angry","d":True},{"n":"frustrated"},{"n":"irritated"},{"n":"upset"}],
        "surprise":[{"n":"surprised","d":True},{"n":"confused"},{"n":"shocked"},{"n":"unsure"}],
    }
    chips = chip_map.get(dominant, [
        {"n": dominant, "d": True},
        {"n": "calm"},
        {"n": "sad"},
        {"n": "anxious"}
    ])'''

new = '''    chip_map = {
        "happy":   [{"e":"😊","n":"happy","d":True},{"e":"😌","n":"calm"},{"e":"😁","n":"excited"},{"e":"🙂","n":"just okay"}],
        "angry":   [{"e":"😡","n":"angry","d":True},{"e":"😤","n":"frustrated"},{"e":"🥺","n":"hurt underneath"},{"e":"😒","n":"irritated"}],
        "fear":    [{"e":"😟","n":"worried","d":True},{"e":"😰","n":"overwhelmed"},{"e":"😓","n":"stressed"},{"e":"😬","n":"uneasy"}],
        "sadness": [{"e":"😔","n":"sad","d":True},{"e":"😶","n":"empty"},{"e":"🥺","n":"hurt"},{"e":"😑","n":"done"}],
        "neutral": [{"e":"🙂","n":"okay","d":True},{"e":"😌","n":"calm"},{"e":"😐","n":"numb"},{"e":"😔","n":"a little down"}],
        "shame":   [{"e":"😳","n":"ashamed","d":True},{"e":"🫣","n":"embarrassed"},{"e":"😞","n":"guilty"},{"e":"😔","n":"regretful"}],
        "anger":   [{"e":"😡","n":"angry","d":True},{"e":"😤","n":"frustrated"},{"e":"😒","n":"irritated"},{"e":"😠","n":"upset"}],
        "surprise":[{"e":"😮","n":"surprised","d":True},{"e":"😕","n":"confused"},{"e":"😲","n":"shocked"},{"e":"🤔","n":"unsure"}],
        "joy":     [{"e":"😊","n":"happy","d":True},{"e":"😁","n":"excited"},{"e":"😌","n":"calm"},{"e":"🙂","n":"content"}],
    }
    chips = chip_map.get(dominant, [
        {"e":"🙂","n": dominant, "d": True},
        {"e":"😌","n": "calm"},
        {"e":"😔","n": "sad"},
        {"e":"😟","n": "anxious"}
    ])'''

if old in content:
    content = content.replace(old, new)
    open('resonance/dashboard.py', 'w', encoding='utf-8').write(content)
    print('Fixed: emoji added back to chips')
else:
    print('WARNING: pattern not found, trying to find chip_map...')
    idx = content.find('chip_map = {')
    if idx > 0:
        print(f'Found chip_map at position {idx}')
        print(content[idx:idx+200])
    else:
        print('chip_map not found in dashboard.py')

# Also fix the HTML to show emoji + name
html = open('resonance/templates/dashboard.html', 'r', encoding='utf-8').read()
old_h = "    el.textContent=c.n;"
new_h = "    el.textContent=(c.e ? c.e+' ' : '')+c.n;"

if old_h in html:
    html = html.replace(old_h, new_h)
    open('resonance/templates/dashboard.html', 'w', encoding='utf-8').write(html)
    print('Fixed: HTML chips show emoji + name')
else:
    print('WARNING: HTML chip pattern not found')

print('Done.')
