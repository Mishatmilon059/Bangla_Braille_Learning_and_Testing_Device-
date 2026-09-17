from PIL import Image
import numpy as np

im = Image.open('data/braille_verified/00_a.png')
print("Mode:", im.mode, "Size:", im.size)
arr = np.array(im)
# Dot 1 is at (40, 40)
# Let's find unique colors
unique_colors = np.unique(arr.reshape(-1, 3), axis=0)
print(f"Number of unique colors: {len(unique_colors)}")
for c in unique_colors[:10]:
    print("Color:", c)
