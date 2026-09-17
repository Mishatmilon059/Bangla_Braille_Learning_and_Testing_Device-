import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def detect_dots_in_crop(crop_img, num_cells=1):
    # crop_img is a PIL Image containing 1 or 2 braille cells
    # Convert to grayscale
    gray = np.array(crop_img.convert('L'))
    h, w = gray.shape
    
    # We want to identify the black (filled) dots and white (empty) circles.
    # Black dots have very low values (e.g. < 60).
    # White circles have dark outline and bright center.
    # Let's find local minima or connected components of dark pixels.
    results = []
    
    cell_w = w / num_cells
    for c_idx in range(num_cells):
        cx_start = int(c_idx * cell_w)
        cx_end = int((c_idx + 1) * cell_w)
        cell_gray = gray[:, cx_start:cx_end]
        
        # Standard Braille cell has 2 columns, 3 rows:
        # col 1 (dots 1, 2, 3), col 2 (dots 4, 5, 6)
        # Let's divide cell into 2x3 regions
        # or search for dark blobs
        cell_h, cw = cell_gray.shape
        
        # Let's estimate the 6 dot positions by looking at the grid
        # In a standard cell, dots are approximately at:
        # x: 30%, 70% of cw
        # y: 20%, 50%, 80% of cell_h
        # But let's find the actual circles
        dot_status = {}
        for dot, (r, c) in {1:(0,0), 2:(1,0), 3:(2,0), 4:(0,1), 5:(1,1), 6:(2,1)}.items():
            # sub-box for this dot
            y_min = int(cell_h * (r * 0.33 + 0.05))
            y_max = int(cell_h * ((r + 1) * 0.33 + 0.05))
            x_min = int(cw * (c * 0.5 + 0.05))
            x_max = int(cw * ((c + 1) * 0.5 + 0.05))
            
            sub = cell_gray[y_min:y_max, x_min:x_max]
            # Minimum pixel value in sub
            min_val = np.min(sub) if sub.size > 0 else 255
            mean_val = np.mean(sub) if sub.size > 0 else 255
            # If min_val < 50 and mean_val < 160 -> filled black circle
            is_filled = (min_val < 60) and (np.sum(sub < 80) > 15)
            dot_status[dot] = is_filled
            
        filled_dots = [d for d, filled in dot_status.items() if filled]
        results.append(filled_dots)
        
    return results

# Let's test this on our 10 letters!
os.makedirs('scratch/inspected_letters', exist_ok=True)

# 1. ঋ (Rri) from vowels.png
# x: 735 to 842
# In vowels.png:
# Row 0: header (y: 63 to 101)
# Row 1: বাংলাদেশ (y: 101 to 211)
# Wait, let's check y-lines in vowels.png!
# In vowels.png: lines at [63, 101, 211]
# Let's check headers vs content!
im1 = Image.open('scratch/wiki_crops/vowels.png')
ri_crop = im1.crop((735, 101, 842, 211))
ri_crop.save('scratch/inspected_letters/06_ri.png')
print("ঋ (Rri) crop saved, size:", ri_crop.size)

# Let's check consonants_1.png
# Horizontal lines: [61, 103, 261, 282, 323, 430]
# Table 1:
# Row 0 (Header): y: 61 to 103
# Row 1 (বাংলাদেশ): y: 103 to 182? Wait, let's find horizontal lines inside Table 1!
# Table 1 x-lines: [22, 129, 196, 290, 357, 424, 491, 558, 625, 692, 785, 852]
# Col 0 (Header): 22 to 129
# Col 1 (ক): 129 to 196
# Col 2 (খ): 196 to 290
# Col 3 (গ): 290 to 357
# Col 4 (ঘ): 357 to 424
# Col 5 (ঙ): 424 to 491
# Col 6 (চ): 491 to 558
# Col 7 (ছ): 558 to 625
# Col 8 (জ): 625 to 692
# Col 9 (ঝ): 692 to 785
# Col 10 (ঞ): 785 to 852

im2 = Image.open('scratch/wiki_crops/consonants_1.png')
kha_crop = im2.crop((196, 103, 290, 261))
kha_crop.save('scratch/inspected_letters/12_kha.png')
print("খ (Kha) crop saved, size:", kha_crop.size)

jha_crop = im2.crop((692, 103, 785, 261))
jha_crop.save('scratch/inspected_letters/19_jha.png')
print("ঝ (Jha) crop saved, size:", jha_crop.size)
