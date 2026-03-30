# Run this from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_process.py

content = open('resonance/__init__.py', 'r', encoding='utf-8').read()

# Find and replace the process method
old_lines = [
    '        result = self.extractor.extract(message, modality=modality)',
    '        self.storage.save(result, self.user_id, session_id="default")',
    '        import asyncio; profile = asyncio.run(self.profile_engine.build_profile())',
    '        return self.injector.prepare(result, profile)'
]

new_lines = [
    '        result = self.extractor.extract(message, modality=modality)',
    '        self.storage.save(result, self.user_id, session_id="default")',
    '        return self.injector'
]

old = '\n'.join(old_lines)
new = '\n'.join(new_lines)

if old in content:
    content = content.replace(old, new)
    open('resonance/__init__.py', 'w', encoding='utf-8').write(content)
    print('Done. Process method fixed.')
else:
    print('Pattern not found. Current process method:')
    for i, line in enumerate(content.split('\n')):
        if 'def process' in line or 'extractor.extract' in line or 'storage' in line or 'profile_engine' in line or 'injector' in line:
            print(f'{i}: {line}')
