# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_atexit.py

content = open('resonance/storage.py', 'r', encoding='utf-8').read()

# Add atexit import if not present
if 'import atexit' not in content:
    content = content.replace('import asyncio', 'import asyncio\nimport atexit')
    print('Added atexit import')

# Add atexit registration in __init__
old = '''        self._loop = asyncio.new_event_loop()
        self._db = None
        self._loop.run_until_complete(self._init_surreal())'''

new = '''        self._loop = asyncio.new_event_loop()
        self._db = None
        self._loop.run_until_complete(self._init_surreal())
        atexit.register(self._close)

    def _close(self):
        try:
            self._qdrant.close()
        except Exception:
            pass'''

if old in content:
    content = content.replace(old, new)
    print('Added atexit.register and _close method')
else:
    print('WARNING: pattern not found')

# Fix __del__ to not try to close (atexit handles it now)
old_del = '''    def __del__(self):
        try:
            if hasattr(self, '_qdrant'):
                self._qdrant.close()
        except Exception:
            pass'''

new_del = '''    def __del__(self):
        pass'''

if old_del in content:
    content = content.replace(old_del, new_del)
    print('Simplified __del__')

open('resonance/storage.py', 'w', encoding='utf-8').write(content)
print('Done.')
