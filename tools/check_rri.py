import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def get_filled_dots_in_cell(cell_img):
    # cell_img is a single 6-dot braille cell grayscale image
    arr = np.array(cell_img)
    h, w = arr.shape
    
    # 2 columns, 3 rows
    # Col 1: dots 1, 2, 3 (left ~25-40% w)
    # Col 2: dots 4, 5, 6 (right ~60-75% w)
    # Row 1: dots 1, 4 (top ~15-30% h)
    # Row 2: dots 2, 5 (mid ~45-55% h)
    # Row 3: dots 3, 6 (bot ~70-85% h)
    
    col_x = [int(w * 0.32), int(w * 0.68)]
    row_y = [int(h * 0.22), int(h * 0.50), int(h * 0.78)]
    
    dots = []
    dot_coords = {
        1: (row_y[0], col_x[0]),
        2: (row_y[1], col_x[0]),
        3: (row_y[2], col_x[0]),
        4: (row_y[0], col_x[1]),
        5: (row_y[1], col_x[1]),
        6: (row_y[2], col_x[1]),
    }
    
    # Radius to sample
    r = max(2, min(w, h) // 12)
    for d, (cy, cx) in dot_coords.items():
        y1, y2 = max(0, cy - r), min(h, cy + r + 1)
        x1, x2 = max(0, cx - r), min(w, cx + r + 1)
        patch = arr[y1:y2, x1:x2]
        min_v = np.min(patch)
        mean_v = np.mean(patch)
        # filled dot is very dark (black), min_v < 60 and mean_v < 100
        # empty circle has white center (mean_v > 180)
        is_filled = (min_v < 80 and mean_v < 130)
        if is_filled:
            dots.append(d)
            
    return dots

# Let's test on each target!
# 1. Rri: target_1_ri.png
# Size: (107, 174). Look at target_1_ri.png:
im_ri = Image.open('scratch/inspected_letters/target_1_ri.png').convert('L')
# In vowels table:
# Header is y: 0 to ~38
# বাংলাদেশ is row 1
# ભારત is row 2
# Let's find horizontal lines in im_ri
gray = np.array(im_ri)
h, w = gray.shape
print("Target 1 (Rri) size:", w, h)
divs = [y for y in range(h) if np.sum(gray[y, :] < 200) > w * 0.7]
print("divs in Rri:", divs)

# Let's crop content:
# In vowels.png, row 1 is Bangladesh, row 2 is India.
# But wait! Look at the header of vowels.png:
# Left column of vowels.png:
# Row 0: মুদ্রণ
# Row 1: বাংলাদেশ
# Row 2: ভারত
