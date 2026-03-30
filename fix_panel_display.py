# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_panel_display.py

content = open('resonance/templates/dashboard.html', 'r', encoding='utf-8').read()

# 1. Fix the feeling-emoji div to show word in uppercase teal instead of emoji
old1 = '      <div class="feeling-emoji">${data.pill.emoji}</div>'
new1 = '      <div class="feeling-emoji">${data.pill.word.toUpperCase()}</div>'

if old1 in content:
    content = content.replace(old1, new1)
    print('Fixed: emoji replaced with uppercase word')
else:
    # Try alternate
    old1b = '      <div class="feeling-emoji">${data.pill.word.toUpperCase()}</div>'
    if old1b in content:
        print('Already fixed: emoji already replaced')
    else:
        print('WARNING: emoji pattern not found, searching...')
        for i, line in enumerate(content.split('\n')):
            if 'feeling-emoji' in line or 'pill.emoji' in line or 'pill.word' in line:
                print(f'{i}: {repr(line)}')

# 2. Fix the live-bar to show immediately when data has live info
# Change: display:none to show by default if live data exists
old2 = "      <div class=\"live-bar\" id=\"liveBar\">"
new2 = "      <div class=\"live-bar\" id=\"liveBar\" style=\"display:${data.live && data.live.emotion ? 'block' : 'none'}\">"

if old2 in content:
    content = content.replace(old2, new2)
    print('Fixed: live bar shows when live data exists')
else:
    print('WARNING: live-bar pattern not found')

# 3. Populate live bar from data on render
old3 = "      <div><span class=\"live-emotion\" id=\"liveEmotion\"></span> <span class=\"live-conf\" id=\"liveConf\"></span></div>"
new3 = "      <div><span class=\"live-emotion\" id=\"liveEmotion\">${data.live ? data.live.emotion : ''}</span> <span class=\"live-conf\" id=\"liveConf\">${data.live && data.live.confidence ? data.live.confidence + '% confidence' : ''}</span></div>"

if old3 in content:
    content = content.replace(old3, new3)
    print('Fixed: live bar populated from data on render')
else:
    print('WARNING: live emotion span pattern not found')

open('resonance/templates/dashboard.html', 'w', encoding='utf-8').write(content)
print('Done.')
