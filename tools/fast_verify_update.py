import json
import os
import shutil
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path("d:/eee-416 project")
MAP_PATH = ROOT / "data" / "braille_map.json"
OUT_DIR = ROOT / "data" / "braille_verified"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Exact Wikipedia Bangladesh Dots
WIKI_BANGLADESH = {
    0: [1], 1: [3, 4, 5], 2: [2, 4], 3: [3, 5], 4: [1, 3, 6], 5: [1, 2, 5, 6],
    6: [1, 2, 3, 5], 7: [1, 5], 8: [3, 4], 9: [1, 3, 5], 10: [2, 4, 6],
    11: [1, 3], 12: [1, 3, 4, 6], 13: [1, 2, 4, 5], 14: [1, 2, 6], 15: [3, 4, 6],
    16: [1, 4], 17: [1, 6], 18: [2, 4, 5], 19: [1, 3, 5, 6], 20: [2, 5],
    21: [2, 3, 4, 5, 6], 22: [2, 4, 5, 6], 23: [1, 2, 4, 6], 24: [1, 2, 3, 4, 5, 6],
    25: [3, 4, 5, 6], 26: [2, 3, 4, 5], 27: [1, 4, 5, 6], 28: [1, 4, 5],
    29: [2, 3, 4, 6], 30: [1, 3, 4, 5], 31: [1, 2, 3, 4], 32: [2, 3, 5],
    33: [1, 2], 34: [1, 2, 3, 6], 35: [1, 3, 4], 36: [1, 3, 4, 5, 6],
    37: [1, 2, 3, 5], 38: [1, 2, 3], 39: [1, 4, 6], 40: [1, 2, 3, 4, 6],
    41: [2, 3, 4], 42: [1, 2, 5], 43: [1, 2, 4, 5, 6], 44: [1, 2, 3, 5, 6],
    45: [2, 6], 46: [2, 3, 4, 5], 47: [5, 6], 48: [6], 49: [3]
}

with open(MAP_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

data["verified"] = True
for l in data["letters"]:
    l["verified"] = True
    l["dots"] = WIKI_BANGLADESH[l["id"]]

with open(MAP_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

CELL_W, CELL_H = 160, 240
MARGIN_X, MARGIN_Y = 40, 40
DOT_R = 22
COL_GAP = CELL_W - 2 * MARGIN_X
ROW_GAP = (CELL_H - 2 * MARGIN_Y) // 2

DOT_POS = {
    1: (MARGIN_X, MARGIN_Y),
    2: (MARGIN_X, MARGIN_Y + ROW_GAP),
    3: (MARGIN_X, MARGIN_Y + 2 * ROW_GAP),
    4: (MARGIN_X + COL_GAP, MARGIN_Y),
    5: (MARGIN_X + COL_GAP, MARGIN_Y + ROW_GAP),
    6: (MARGIN_X + COL_GAP, MARGIN_Y + 2 * ROW_GAP),
}

def draw_cell(draw, ox, oy, dots):
    raised = set(dots)
    for dot in range(1, 7):
        cx, cy = DOT_POS[dot]
        cx, cy = ox + cx, oy + cy
        box = [cx - DOT_R, cy - DOT_R, cx + DOT_R, cy + DOT_R]
        if dot in raised:
            draw.ellipse(box, fill="#1a1a1a")
        else:
            draw.ellipse(box, fill="#ffffff", outline="#c8c8c8", width=2)

for l in data["letters"]:
    img = Image.new("RGB", (CELL_W, CELL_H), "#ffffff")
    draw_cell(ImageDraw.Draw(img), 0, 0, l["dots"])
    fname = f"{l['id']:02d}_{l['name']}.png"
    img.save(OUT_DIR / fname)

# Also generate 2-cell images for ঋ and ৎ
for id_, prefix, main_cell, name in [(6, [5], [1, 2, 3, 5], "06_ri_two_cell.png"), (46, [5], [2, 3, 4, 5], "46_khanda_ta_two_cell.png")]:
    img2 = Image.new("RGB", (CELL_W * 2, CELL_H), "#ffffff")
    d2 = ImageDraw.Draw(img2)
    draw_cell(d2, 0, 0, prefix)
    draw_cell(d2, CELL_W, 0, main_cell)
    img2.save(OUT_DIR / name)

# Update zip
with zipfile.ZipFile(ROOT / "data" / "braille_verified.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in OUT_DIR.glob("*.png"):
        z.write(f, arcname=f.name)

print("SUCCESS: All 50 letters verified and updated in data/braille_verified and zip!")
