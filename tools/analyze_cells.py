import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def analyze_cell(img_path, title):
    im = Image.open(img_path).convert('L')
    arr = np.array(im)
    h, w = arr.shape
    print(f"\n==========================================")
    print(f"{title} ({w}x{h})")
    print(f"==========================================")
    
    # Print high resolution ASCII
    # Determine height to print
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

crops = [
    ('scratch/wiki_crops/full_col_ri.png', '1. ঋ (Rri) - Full Column'),
    ('scratch/wiki_crops/kha_bangladesh.png', '2. খ (Kha) - Bangladesh'),
    ('scratch/wiki_crops/kha_india.png', '2b. খ (Kha) - India'),
    ('scratch/wiki_crops/jha_bangladesh.png', '3. ঝ (Jha) - Bangladesh'),
    ('scratch/wiki_crops/jha_india.png', '3b. ঝ (Jha) - India'),
    ('scratch/wiki_crops/full_col_pha.png', '4. ফ (Pha) - Full Column'),
    ('scratch/wiki_crops/full_col_bha.png', '5. ভ (Bha) - Full Column'),
    ('scratch/wiki_crops/full_col_yya.png', '6. য় (Yya) - Full Column'),
    ('scratch/wiki_crops/full_col_khandatta.png', '7. ৎ (Khandatta) - Full Column'),
    ('scratch/wiki_crops/anushar.png', '8. ং (Anushar)'),
    ('scratch/wiki_crops/bisharga.png', '9. ঃ (Bisharga)'),
    ('scratch/wiki_crops/chandrabindu.png', '10. ঁ (Chandrabindu)'),
]

for p, t in crops:
    analyze_cell(p, t)
