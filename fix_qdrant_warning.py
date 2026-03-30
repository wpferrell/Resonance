# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_qdrant_warning.py

content = open('resonance/storage.py', 'r', encoding='utf-8').read()

old = '        self._qdrant = QdrantClient(path=QDRANT_PATH)'

new = '''        self._qdrant = QdrantClient(path=QDRANT_PATH)

    def __del__(self):
        try:
            self._qdrant.close()
        except Exception:
            pass'''

if old in content:
    content = content.replace(old, new)
    open('resonance/storage.py', 'w', encoding='utf-8').write(content)
    print('Fixed: storage.py — Qdrant client closes cleanly on shutdown')
else:
    print('WARNING: pattern not found in storage.py')
