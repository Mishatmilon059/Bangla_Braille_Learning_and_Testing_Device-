import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect each crop in detail
# Let's write a function to print ASCII representations of small crops
def dump_ascii(crop_path, w=80, h=30):
    im = Image.open(crop_path).convert('L')
    im = im.resize((w, h))
    for y in range(h):
        line = ""
        for x in range(w):
            v = im.getpixel((x, y))
            if v < 80:
                line += "#"
            elif v < 160:
                line += "+"
            elif v < 220:
                line += "."
            else:
                line += " "
        print(line)

print("=== CROP RI ===")
dump_ascii('scratch/wiki_crops/crop_ri.png', 80, 25)

print("=== CROP KHA ===")
dump_ascii('scratch/wiki_crops/crop_kha.png', 60, 25)

print("=== CROP JHA ===")
dump_ascii('scratch/wiki_crops/crop_jha.png', 60, 25)

print("=== CROP PHA ===")
dump_ascii('scratch/wiki_crops/crop_pha.png', 50, 25)

print("=== CROP BHA ===")
dump_ascii('scratch/wiki_crops/crop_bha.png', 50, 25)

print("=== CROP YYA ===")
dump_ascii('scratch/wiki_crops/crop_yya.png', 60, 25)

print("=== CROP KHANDATTA ===")
dump_ascii('scratch/wiki_crops/crop_khandatta.png', 70, 25)

print("=== CROP ANUSHAR ===")
dump_ascii('scratch/wiki_crops/crop_anushar.png', 40, 25)

print("=== CROP BISHARGA ===")
dump_ascii('scratch/wiki_crops/crop_bisharga.png', 40, 25)

print("=== CROP CHANDRABINDU ===")
dump_ascii('scratch/wiki_crops/crop_chandrabindu.png', 40, 25)
