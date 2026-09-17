import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def analyze_crop_file(p, t):
    im = Image.open(p).convert('L')
    arr = np.array(im)
    h, w = arr.shape
    print(f"\n==========================================")
    print(f"{t} ({w}x{h})")
    print(f"==========================================")
    step_y = max(1, h // 25)
    step_x = max(1, w // 40)
    for y in range(0, h, step_y):
        line = ""
        for x in range(0, w, step_x):
            patch = arr[y:min(y+step_y, h), x:min(x+step_x, w)]
            min_v = np.min(patch)
            mean_v = np.mean(patch)
            if min_v < 60:
                line += "●"
            elif min_v < 180 and mean_v > 170:
                line += "○"
            elif min_v < 210:
                line += "."
            else:
                line += " "
        print(line)

analyze_crop_file('scratch/wiki_crops/full_col_ri.png', '1. ঋ (Rri)')
analyze_crop_file('scratch/wiki_crops/kha_bangladesh.png', '2. খ (Kha) - Bangladesh')
analyze_crop_file('scratch/wiki_crops/kha_india.png', '2b. খ (Kha) - India')
analyze_crop_file('scratch/wiki_crops/jha_bangladesh.png', '3. ঝ (Jha) - Bangladesh')
analyze_crop_file('scratch/wiki_crops/jha_india.png', '3b. ঝ (Jha) - India')
