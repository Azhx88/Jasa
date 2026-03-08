import re

# 1. Update build_pages.py
with open('build_pages.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace products/dhoop/ with just the filename, and inject "type": "dhoop",
code = re.sub(r'"products/dhoop/([^"]+)":\s*\{\n\s*"img"', r'"\1": {\n        "type": "dhoop",\n        "img"', code)

# Replace products/agarbatti/ with just the filename, and inject "type": "agarbatti",
code = re.sub(r'"products/agarbatti/([^"]+)":\s*\{\n\s*"img"', r'"\1": {\n        "type": "agarbatti",\n        "img"', code)

# Fix the checks in create_product_page
code = code.replace("is_dhoop = 'dhoop' in file_path", "is_dhoop = spec.get('type') == 'dhoop'")
code = code.replace("'dhoop' if 'dhoop' in file_path else 'agarbatti'", "spec.get('type')")

with open('build_pages.py', 'w', encoding='utf-8') as f:
    f.write(code)

# 2. Update template.html
with open('template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Update all anchor tags pointing to the old structure
html = html.replace('href="products/dhoop/', 'href="')
html = html.replace('href="products/agarbatti/', 'href="')

with open('template.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Flattening refactor complete.')
