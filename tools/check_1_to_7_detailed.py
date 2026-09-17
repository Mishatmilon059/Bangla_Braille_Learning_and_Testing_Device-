import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def analyze_individual(path, name):
    im = Image.open(path).convert('RGB')
    arr = np.array(im)
    h, w, _ = arr.shape
    gray = np.mean(arr, axis=2)
    
    print(f"\n=======================================================")
    print(f"Target: {name} (size: {w}x{h})")
    print(f"=======================================================")
    
    # Let's print out lines at 1 character per 2 pixels
    step_y = 4
    step_x = 2
    for y in range(0, h, step_y):
        line = ""
        for x in range(0, w, step_x):
            sub = gray[y:min(y+step_y, h), x:min(x+step_x, w)]
            min_v = np.min(sub)
            mean_v = np.mean(sub)
            if min_v < 60:
                line += "●"
            elif min_v < 180 and mean_v > 180:
                line += "o"
            elif min_v < 210 and mean_v > 180:
                line += "."
            else:
                line += " "
        print(line)

for i in [1, 2, 3, 4, 5, 6, 7]:
    fnames = [f for f in os.listdir('scratch/inspected_letters') if f.startswith(f"target_{i}_")]
    if fnames:
        analyze_individual(os.path.join('scratch/inspected_letters', fnames[0]), fnames[0])
