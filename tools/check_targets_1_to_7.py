import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def print_target_detail(path, name):
    im = Image.open(path).convert('RGB')
    arr = np.array(im)
    h, w, _ = arr.shape
    gray = np.mean(arr, axis=2)
    
    print(f"\n=======================================================")
    print(f"Target: {name} (size: {w}x{h})")
    print(f"=======================================================")
    
    # Scale to ~60 cols
    scale_x = max(1, w // 60)
    scale_y = max(1, h // 35)
    
    mini_h = h // scale_y
    mini_w = w // scale_x
    
    for y in range(mini_h):
        row_str = ""
        orig_y = y * scale_y
        for x in range(mini_w):
            orig_x = x * scale_x
            patch = gray[orig_y:orig_y+scale_y, orig_x:orig_x+scale_x]
            min_val = np.min(patch)
            mean_val = np.mean(patch)
            if min_val < 60:
                row_str += "●"
            elif min_val < 180 and mean_val > 170:
                row_str += "○"
            else:
                row_str += " "
        print(row_str)

for i in range(1, 8):
    fnames = [f for f in os.listdir('scratch/inspected_letters') if f.startswith(f"target_{i}_")]
    if fnames:
        print_target_detail(os.path.join('scratch/inspected_letters', fnames[0]), fnames[0])
