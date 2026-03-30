# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_loading_weights.py

content = open('resonance/extractor.py', 'r', encoding='utf-8').read()

# Suppress the "Loading weights" progress bar from transformers
old = '            self._model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_PATH))'
new = '            self._model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_PATH), local_files_only=True)'

# Also wrap model loading to suppress tqdm output
old2 = '''            self._tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
            self._model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_PATH), local_files_only=True)
            self._model.eval()'''

new2 = '''            import os
            import io
            from contextlib import redirect_stderr
            self._tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
            with redirect_stderr(io.StringIO()):
                self._model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_PATH), local_files_only=True)
            self._model.eval()'''

if old in content:
    content = content.replace(old, new)
    print('Step 1: Added local_files_only=True')

if old2 in content:
    content = content.replace(old2, new2)
    print('Step 2: Suppressed loading weights bar')
else:
    print('WARNING: step 2 pattern not found - checking...')
    for i, line in enumerate(content.split('\n')):
        if 'from_pretrained' in line or 'redirect' in line:
            print(f'{i}: {line}')

open('resonance/extractor.py', 'w', encoding='utf-8').write(content)
print('Done.')
