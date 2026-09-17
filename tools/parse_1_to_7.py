import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def parse_target(img_path, title):
    im = Image.open(img_path).convert('L')
    arr = np.array(im)
    h, w = arr.shape
    print(f"\n==========================================")
    print(f"{title} ({w}x{h})")
    print(f"==========================================")
    for y in range(0, h, max(1, h // 35)):
        line = ""
        for x in range(0, w, max(1, w // 45)):
            val = arr[y, x]
            if val < 60:
                line += "#"
            elif val < 175:
                line += "o"
            elif val < 210:
                line += "."
            else:
                line += " "
        print(line)

for i in range(1, 8):
    fnames = [f for f in os.listdir('scratch/inspected_letters') if f.startswith(f"target_{i}_")]
    if fnames:
        parse_target(os.path.join('scratch/inspected_letters', fnames[0]), fnames[0])
