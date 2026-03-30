# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_storage_init.py

content = open('resonance/storage.py', 'r', encoding='utf-8').read()

old = '''    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._qdrant = QdrantClient(path=QDRANT_PATH)
    def __del__(self):
        try:
            self._qdrant.close()
        except Exception:
            pass
        self._ensure_collection()
        self._loop = asyncio.new_event_loop()
        self._db = None
        self._loop.run_until_complete(self._init_surreal())'''

new = '''    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._qdrant = QdrantClient(path=QDRANT_PATH)
        self._ensure_collection()
        self._loop = asyncio.new_event_loop()
        self._db = None
        self._loop.run_until_complete(self._init_surreal())

    def __del__(self):
        try:
            if hasattr(self, '_qdrant'):
                self._qdrant.close()
        except Exception:
            pass'''

if old in content:
    content = content.replace(old, new)
    open('resonance/storage.py', 'w', encoding='utf-8').write(content)
    print('Fixed: storage.py — __init__ and __del__ corrected')
else:
    print('WARNING: pattern not found. Showing __init__ area:')
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '__init__' in line or '__del__' in line or '_ensure_collection' in line or '_loop' in line:
            print(f'{i}: {line}')
