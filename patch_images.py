import re

with open('build_pages.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Map products to images
img_map = {
    "classic-sambrani": "002.png",
    "computer-sambrani": "003.png",
    "loban-dhoop": "004.png",
    "kesar-rose-sambrani": "005.png",
    "gugal-dhoop-cones": "006.png",
    "chandan-sambrani-powder": "007.png",
    "marikolunthu": "111.png",
    "jasmine": "222.png",
    "rose": "333.png",
    "sandal": "444.png",
    "pineapple": "555.png",
    "natural": "666.png",
    "royal": "777.png",
    "traditional": "888.png",
}

for k, v in img_map.items():
    # Use re.escape on k and just look for it before .html": {
    # e.g. /classic-sambrani.html": {
    pattern = rf'({k}\.html":\s*{{\s*)("cat":)'
    code = re.sub(pattern, rf'\1"img": "public/{v}",\n        \2', code)

with open('build_pages.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("build_pages.py successfully patched.")
