import re
import os

for f in os.listdir('static/pages'):
    if f.endswith('.html'):
        path = os.path.join('static/pages', f)
        with open(path, 'r', encoding='utf-8') as fp:
            c = fp.read()
        # Fix relative paths to /static/
        c = re.sub(r'(href|src)=["\'](?!(?:https?://|/|#))([^"\']*)["\']', r'\1="/static/\2"', c)
        with open(path, 'w', encoding='utf-8') as fp:
            fp.write(c)
        print(f'Fixed {f}')