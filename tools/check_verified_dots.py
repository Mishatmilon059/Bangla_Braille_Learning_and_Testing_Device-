import json
import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

# Check dot positions in 160x240 image
# DOT_POS = {
#     1: (40, 40),
#     2: (40, 120),
#     3: (40, 200),
#     4: (120, 40),
#     5: (120, 120),
#     6: (120, 200),
# }

def read_dots_from_img(path):
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
        # sample pixel at (x, y)
        val = im.getpixel((x, y))
        if val < 100: # dark = raised
            dots.append(d)
    return dots

targets = [
    ('06_ri.png', 'ঋ', 'Rri'),
    ('12_kha.png', 'খ', 'Kha'),
    ('19_jha.png', 'ঝ', 'Jha'),
    ('32_pha.png', 'ফ', 'Pha'),
    ('34_bha.png', 'ভ', 'Bha'),
    ('45_yya.png', 'য়', 'Yya'),
    ('46_khanda_ta.png', 'ৎ', 'Khandatta'),
    ('47_anushar.png', 'ং', 'Anushar'),
    ('48_bisharga.png', 'ঃ', 'Bissharga'),
    ('49_chandrabindu.png', 'ঁ', 'Chandrabindu'),
]

print("Existing data/braille_verified images dots:")
for fname, ch, eng in targets:
    p = os.path.join('data', 'braille_verified', fname)
    if os.path.exists(p):
        dots = read_dots_from_img(p)
        print(f"{fname:20s} {ch} ({eng:12s}): dots {dots}")
