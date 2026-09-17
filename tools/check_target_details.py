import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect each target crop by detecting:
# 1. Image dimensions
# 2. Text in header / row labels
# 3. Circles and dots

files = [
    ("target_1_ri.png", "ঋ (Rri)"),
    ("target_2_kha.png", "খ (Kha)"),
    ("target_3_jha.png", "ঝ (Jha)"),
    ("target_4_pha.png", "ফ (Pha)"),
    ("target_5_bha.png", "ভ (Bha)"),
    ("target_6_yya.png", "য় (Yya)"),
    ("target_7_khandatta.png", "ৎ (Khandatta)"),
    ("target_8_anushar.png", "ং (Anushar)"),
    ("target_9_bisharga.png", "ঃ (Bisharga)"),
    ("target_10_chandrabindu.png", "ঁ (Chandrabindu)"),
]

for fname, name in files:
    path = os.path.join('scratch/inspected_letters', fname)
    im = Image.open(path)
    print(f"=== {name} : {im.size} ===")
