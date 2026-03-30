# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_chips.py

import re

content = open('resonance/dashboard.py', 'r', encoding='utf-8').read()

# Replace chip_map with emoji-free version
old = '''    chip_map = {
        "happy":   [{"e":"happy","n":"happy","d":True},{"e":"calm","n":"calm"},{"e":"excited","n":"excited"},{"e":"okay","n":"just okay"}],
        "angry":   [{"e":"angry","n":"angry","d":True},{"e":"frustrated","n":"frustrated"},{"e":"hurt","n":"hurt underneath"},{"e":"irritated","n":"irritated"}],
        "anxious": [{"e":"worried","n":"worried","d":True},{"e":"overwhelmed","n":"overwhelmed"},{"e":"stressed","n":"stressed"},{"e":"uneasy","n":"uneasy"}],
        "sad":     [{"e":"sad","n":"sad","d":True},{"e":"empty","n":"empty"},{"e":"hurt","n":"hurt"},{"e":"done","n":"done"}],
        "neutral": [{"e":"okay","n":"okay","d":True},{"e":"calm","n":"calm"},{"e":"numb","n":"numb"},{"e":"down","n":"a little down"}],
    }
    chips = chip_map.get(dominant, [
        {"e": dominant, "n": dominant, "d": True},
        {"e": "calm", "n": "calm"},
        {"e": "sad", "n": "sad"},
        {"e": "anxious", "n": "anxious"}
    ])'''

new = '''    chip_map = {
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

if old in content:
    content = content.replace(old, new)
    print('Fixed: chip_map updated - emoji removed, all 7 emotions mapped')
else:
    # Try to find and replace any chip_map
    print('WARNING: exact pattern not found, trying broader fix...')
    # Find chip_map block and replace
    start = content.find('    chip_map = {')
    end = content.find('    ])', start) + 6
    if start > 0 and end > 0:
        content = content[:start] + new + content[end:]
        print('Fixed: chip_map replaced using position')
    else:
        print('ERROR: could not find chip_map')

open('resonance/dashboard.py', 'w', encoding='utf-8').write(content)
print('Done.')
