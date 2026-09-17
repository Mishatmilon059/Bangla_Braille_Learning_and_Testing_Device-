import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def find_lines(im_path):
    im = Image.open(im_path).convert('RGB')
    arr = np.array(im)
    h, w, _ = arr.shape
    
    # Grid lines are grayish borders, usually darker than background (#eaecf0 or #f8f9fa)
    # Let's find columns where there is a vertical line
    # A vertical line has consistent color across y
    gray = np.mean(arr, axis=2)
    
    # Horizontal lines: low variance or border color across many columns
    horiz_scores = []
    for y in range(h):
        row = gray[y, :]
        # check if many pixels are around 150-210 (border)
        border_count = np.sum((row >= 150) & (row <= 215))
        horiz_scores.append((y, border_count))
        
    vert_scores = []
    for x in range(w):
        col = gray[:, x]
        border_count = np.sum((col >= 150) & (col <= 215))
        vert_scores.append((x, border_count))
        
    print(f"\n--- Analysis for {os.path.basename(im_path)} ({w}x{h}) ---")
    # Top horizontal lines
    top_h = sorted([y for y, c in horiz_scores if c > w * 0.5])
    print("Horizontal lines around:", top_h)
    
    top_v = sorted([x for x, c in vert_scores if c > h * 0.4])
    print("Vertical lines around:", top_v)

find_lines('scratch/wiki_crops/vowels.png')
find_lines('scratch/wiki_crops/consonants_1.png')
find_lines('scratch/wiki_crops/consonants_2.png')
find_lines('scratch/wiki_crops/modifiers.png')
