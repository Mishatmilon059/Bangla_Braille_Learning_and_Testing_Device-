import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def analyze_crop_dots(path, name):
    im = Image.open(path).convert('RGB')
    arr = np.array(im)
    h, w, _ = arr.shape
    gray = np.mean(arr, axis=2)
    
    print(f"\n=======================================================")
    print(f"Target: {name} (size: {w}x{h})")
    print(f"=======================================================")
    
    # Check if there are horizontal dividers in this crop
    # In table, headers are usually at the top, followed by 1 or 2 rows
    # Let's print out an ASCII map of pixels < 100 (black pixels)
    # Scale to ~40 cols
    scale_x = max(1, w // 40)
    scale_y = max(1, h // 25)
    
    mini_h = h // scale_y
    mini_w = w // scale_x
    
    grid = []
    for y in range(mini_h):
        row_str = ""
        orig_y = y * scale_y
        for x in range(mini_w):
            orig_x = x * scale_x
            patch = gray[orig_y:orig_y+scale_y, orig_x:orig_x+scale_x]
            min_val = np.min(patch)
            mean_val = np.mean(patch)
            if min_val < 60:
                row_str += "●" # filled dot or glyph
            elif min_val < 180 and mean_val > 180:
                row_str += "○" # empty circle outline
            else:
                row_str += " "
        grid.append(row_str)
    
    for row in grid:
        print(row)

for i in range(1, 11):
    fnames = [f for f in os.listdir('scratch/inspected_letters') if f.startswith(f"target_{i}_")]
    if fnames:
        analyze_crop_dots(os.path.join('scratch/inspected_letters', fnames[0]), fnames[0])
