import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def analyze_box(img, x1, y1, x2, y2, name=""):
    crop = img.crop((x1, y1, x2, y2))
    crop_path = f"scratch/wiki_crops/test_{name}.png"
    crop.save(crop_path)
    return crop_path

im1 = Image.open('scratch/wiki_crops/vowels.png')
im2 = Image.open('scratch/wiki_crops/consonants_1.png')
im3 = Image.open('scratch/wiki_crops/consonants_2.png')
im4 = Image.open('scratch/wiki_crops/modifiers.png')

print("Image 1 vowels:", im1.size)
print("Image 2 consonants 1:", im2.size)
print("Image 3 consonants 2:", im3.size)
print("Image 4 modifiers:", im4.size)
