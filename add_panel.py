# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python add_panel.py

import shutil

# 1. Replace dashboard.py
shutil.copy('dashboard_new.py', 'resonance/dashboard.py')
print('Replaced: resonance/dashboard.py')

# 2. Replace dashboard.html
shutil.copy('dashboard_new.html', 'resonance/templates/dashboard.html')
print('Replaced: resonance/templates/dashboard.html')

# 3. Add start_panel() to __init__.py
content = open('resonance/__init__.py', 'r', encoding='utf-8').read()

# Add start_panel method after process method
old = '''    def correct(self, detected: str, corrected: str, result: EmotionResult):'''

new = '''    def start_panel(self, port: int = 7731, open_browser: bool = True) -> str:
        """
        Start the Resonance panel in your browser.
        Returns the URL. Panel updates live with every process() call.

        Usage:
            r = Resonance(user_id="you")
            r.start_panel()  # opens http://localhost:7731
        """
        from .dashboard import start
        url = start(port=port, open_browser=open_browser)
        print(f"[Resonance] Panel running at {url}")
        return url

    def correct(self, detected: str, corrected: str, result: EmotionResult):'''

if old in content:
    content = content.replace(old, new)
    print('Added: start_panel() method')
else:
    print('WARNING: could not find insertion point for start_panel()')

# 4. Update process() to push live updates to panel
old2 = '''        result = self.extractor.extract(message, modality=modality)
        self.storage.save(result, self.user_id, session_id="default")
        return self.injector'''

new2 = '''        result = self.extractor.extract(message, modality=modality)
        self.storage.save(result, self.user_id, session_id="default")
        try:
            from .dashboard import push_update
            push_update(result)
        except Exception:
            pass
        return self.injector'''

if old2 in content:
    content = content.replace(old2, new2)
    print('Updated: process() pushes live updates to panel')
else:
    print('WARNING: could not update process() method')

open('resonance/__init__.py', 'w', encoding='utf-8').write(content)

# 5. Add flask and flask-socketio to pyproject.toml
toml = open('pyproject.toml', 'r', encoding='utf-8').read()
if 'flask' not in toml.lower():
    toml = toml.replace(
        '"sentencepiece>=0.1.99"',
        '"sentencepiece>=0.1.99",\n    "flask>=3.0.0",\n    "flask-socketio>=5.3.0"'
    )
    open('pyproject.toml', 'w', encoding='utf-8').write(toml)
    print('Updated: pyproject.toml with flask and flask-socketio')
else:
    print('flask already in pyproject.toml')

print('Done.')
