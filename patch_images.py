import re

with open('build_pages.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Map products to images
img_map = {
    "classic-sambrani": "002.webp",
    "computer-sambrani": "003.webp",
    "loban-dhoop": "004.webp",
    "kesar-rose-sambrani": "005.webp",
    "gugal-dhoop-cones": "006.webp",
    "chandan-sambrani-powder": "007.webp",
    "marikolunthu": "111.webp",
    "jasmine": "222.webp",
    "rose": "333.webp",
    "sandal": "444.webp",
    "pineapple": "555.webp",
    "natural": "666.webp",
    "royal": "777.webp",
    "traditional": "888.webp",
}

for k, v in img_map.items():
    # Use re.escape on k and just look for it before .html": {
    # e.g. /classic-sambrani.html": {
    pattern = rf'({k}\.html":\s*{{\s*)("cat":)'
    code = re.sub(pattern, rf'\1"img": "public/{v}",\n        \2', code)

with open('build_pages.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("build_pages.py successfully patched.")
