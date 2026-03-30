# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_flask_silent.py

from pathlib import Path

# Fix dashboard.py in project source
for filepath in [
    'resonance/dashboard.py',
]:
    content = open(filepath, 'r', encoding='utf-8').read()

    # Fix template path
    for old, new in [
        ("template_folder='templates'", "template_folder=str(Path(__file__).parent / 'templates')"),
        ("template_folder=str(__import__('pathlib').Path(__file__).parent / 'templates')", "template_folder=str(Path(__file__).parent / 'templates')"),
    ]:
        if old in content:
            content = content.replace(old, new)
            print(f'Fixed template path in {filepath}')

    # Silence ALL Flask/werkzeug/socketio logging
    old_run = '''    def _run():'''
    new_run = '''    def _run():
        import logging, os
        os.environ['WERKZEUG_RUN_MAIN'] = 'true'
        for logger_name in ['werkzeug', 'engineio', 'socketio', 'flask']:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)'''

    if '        for logger_name in' not in content:
        content = content.replace(old_run, new_run)
        print(f'Fixed: server logging silenced in {filepath}')

    open(filepath, 'w', encoding='utf-8').write(content)

# Add MANIFEST.in so templates get included in PyPI package
open('MANIFEST.in', 'w').write('recursive-include resonance/templates *\n')
print('Fixed: MANIFEST.in created')

# Fix pyproject.toml to include templates
toml = open('pyproject.toml', 'r', encoding='utf-8').read()
if 'package-data' not in toml:
    toml = toml.rstrip() + '\n\n[tool.setuptools.package-data]\nresonance = ["templates/*"]\n'
    open('pyproject.toml', 'w', encoding='utf-8').write(toml)
    print('Fixed: pyproject.toml includes templates')
else:
    print('pyproject.toml already has package-data')

print('Done.')
