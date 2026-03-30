# fix_dashboard_eventlet.py
# Run from C:\Users\Shadow\Documents\Resonance with .venv active

PROJECT = 'resonance/dashboard.py'
INSTALLED = r'C:\Users\Shadow\resonance\Lib\site-packages\resonance\dashboard.py'

NEW_RUN = '''    def _run():
        import eventlet
        eventlet.monkey_patch()
        _socketio.run(_app, port=port, host='127.0.0.1')
'''

for filepath in [PROJECT, INSTALLED]:
    try:
        content = open(filepath, 'r', encoding='utf-8').read()
        
        # Find and replace the entire _run function body
        import re
        # Replace everything between def _run(): and _server_thread
        pattern = r'    def _run\(\):.*?(?=    _server_thread)'
        replacement = NEW_RUN + '\n'
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Also fix async_mode
        new_content = new_content.replace("async_mode='threading'", "async_mode='eventlet'")
        new_content = new_content.replace("async_mode=\"threading\"", "async_mode='eventlet'")
        
        open(filepath, 'w', encoding='utf-8').write(new_content)
        print(f'Fixed: {filepath}')
    except Exception as e:
        print(f'Error on {filepath}: {e}')

print('Done.')
