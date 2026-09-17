import json
import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

with open('data/braille_map.json', encoding='utf-8') as f:
    bm = json.load(f)

def read_dots(path):
    im = Image.open(path).convert('L')
    dots = []
    positions = {
        1: (40, 40),
        2: (40, 120),
        3: (40, 200),
        4: (120, 40),
        5: (120, 120),
        6: (120, 200),
    }
    for d, (x, y) in positions.items():
        if im.getpixel((x, y)) < 100:
            dots.append(d)
    return dots

print(f"{'ID':2s} {'Char':4s} {'Name':14s} {'Map Dots':16s} {'Verified PNG Dots':20s} {'Match?':6s}")
print("-" * 75)

discrepancies = []
for item in bm['letters']:
    fname = f"{item['id']:02d}_{item['name']}.png"
    p = os.path.join('data', 'braille_verified', fname)
    if os.path.exists(p):
        png_dots = read_dots(p)
        map_dots = item['dots']
        match = (png_dots == map_dots)
        if not match:
            discrepancies.append((item['id'], item['char'], item['name'], map_dots, png_dots))
        print(f"{item['id']:2d} {item['char']:4s} {item['name']:14s} {str(map_dots):16s} {str(png_dots):20s} {'OK' if match else 'MISMATCH'}")
    else:
        print(f"{item['id']:2d} {item['char']:4s} {item['name']:14s} {str(item['dots']):16s} {'MISSING':20s} NO")

print("\n--- Discrepancies between braille_map.json and data/braille_verified/*.png ---")
for d in discrepancies:
    print(f"ID {d[0]:2d}: {d[1]} ({d[2]}) -> Map has {d[3]}, but PNG has {d[4]}")
