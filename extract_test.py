import os
import re

TEMPLATE_PATH = 'template.html'

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='utf-16') as f:
            return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

html = read_file(TEMPLATE_PATH)

# Output lines matching ROUTE
for i, line in enumerate(html.split('\n')):
    if 'ROUTE' in line.upper() or 'data-route' in line.lower() or 'id="products"' in line.lower() or 'id="agarbatti"' in line.lower():
        print(f"{i+1}: {line.strip()}")
