# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_storage_init2.py

lines = open('resonance/storage.py', 'r', encoding='utf-8').readlines()

# Find the line numbers
init_line = None
del_line = None
for i, line in enumerate(lines):
    if 'def __init__(self):' in line and init_line is None:
        init_line = i
    if 'def __del__(self):' in line and del_line is None:
        del_line = i

print(f'__init__ at line {init_line}: {lines[init_line].rstrip()}')
print(f'__del__ at line {del_line}: {lines[del_line].rstrip()}')

# Show lines between them
print('Lines between:')
for i in range(init_line, del_line + 10):
    print(f'{i}: {lines[i].rstrip()}')

# The fix: move _ensure_collection, _loop, _db lines from __del__ back to __init__
# Remove those lines from after __del__ and put them in __init__

# Build new file
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # When we hit __init__, add the body lines that should be there
    if 'def __init__(self):' in line:
        new_lines.append(line)
        i += 1
        # Add the DATA_DIR and _qdrant lines (they're already next)
        while i < len(lines) and 'def __del__' not in lines[i]:
            new_lines.append(lines[i])
            i += 1
        # Now add the missing init lines
        indent = '        '
        new_lines.append(f'{indent}self._ensure_collection()\n')
        new_lines.append(f'{indent}self._loop = asyncio.new_event_loop()\n')
        new_lines.append(f'{indent}self._db = None\n')
        new_lines.append(f'{indent}self._loop.run_until_complete(self._init_surreal())\n')
        new_lines.append(f'\n')
        continue
    
    # When we hit __del__, write clean version
    if 'def __del__(self):' in line:
        new_lines.append(line)
        i += 1
        # Write clean __del__ body
        indent = '        '
        new_lines.append(f'{indent}try:\n')
        new_lines.append(f'{indent}    if hasattr(self, \'_qdrant\'):\n')
        new_lines.append(f'{indent}        self._qdrant.close()\n')
        new_lines.append(f'{indent}except Exception:\n')
        new_lines.append(f'{indent}    pass\n')
        new_lines.append(f'\n')
        # Skip the old __del__ body
        while i < len(lines) and 'def _ensure_collection' not in lines[i]:
            i += 1
        continue
    
    new_lines.append(line)
    i += 1

open('resonance/storage.py', 'w', encoding='utf-8').write(''.join(new_lines))
print('\nFixed: storage.py written. Verifying...')

# Verify
content = open('resonance/storage.py', 'r', encoding='utf-8').read()
lines2 = content.split('\n')
for i, line in enumerate(lines2):
    if '__init__' in line or '__del__' in line or '_ensure_collection()' in line:
        print(f'{i}: {line}')
