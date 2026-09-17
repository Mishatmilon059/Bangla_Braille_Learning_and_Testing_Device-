import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def find_circles_in_crop(crop_img):
    # crop_img is RGB or L
    gray = np.array(crop_img.convert('L'))
    h, w = gray.shape
    
    # We want to identify the circles.
    # In wikipedia, dots are 6-dot cells. A cell can have 1 or 2 columns of dots.
    # Let's find all dark regions (black dots, value < 80) and empty circles (circle with light center > 200 and dark boundary < 150)
    
    # Let's do a simple grid search for dots:
    # Most cells are 2 columns x 3 rows.
    # If width is wide, it may be a two-cell glyph (e.g. ঋ or ৎ).
    return gray

# Let's inspect the exact layout of:
# 1. vowels.png (Image 1)
# 2. consonants_1.png (Image 2)
# 3. consonants_2.png (Image 3)
# 4. modifiers.png (Image 4)

im1 = Image.open('scratch/wiki_crops/vowels.png')
im2 = Image.open('scratch/wiki_crops/consonants_1.png')
im3 = Image.open('scratch/wiki_crops/consonants_2.png')
im4 = Image.open('scratch/wiki_crops/modifiers.png')

# Let's print out the exact visual crops for our 10 targets:
# Targets:
# 1. ঋ (ri)
# 2. খ (kha)
# 3. ঝ (jha)
# 4. ফ (pha)
# 5. ভ (bha)
# 6. য় (yya)
# 7. ৎ (khandatta)
# 8. ং (anushar)
# 9. ঃ (bisharga)
# 10. ঁ (chandrabindu)

# Save each individually with high quality
# ঋ in vowels.png:
# x: 735 to 842
# y in vowels.png:
# Row 0: header (y: 63 to 101)
# Row 1: বাংলাদেশ (y: 101 to 211) -> wait, does it have বাংলাদেশ and ভারত?
# Let's check y lines in vowels: [63, 101, 211]
# Wait! In vowels.png, let's crop y from 63 to 237 at x: 735 to 842:
im1.crop((735, 63, 842, 237)).save('scratch/inspected_letters/target_1_ri.png')

# In consonants_1.png:
# খ: x=196 to 290, y=61 to 261
im2.crop((196, 61, 290, 261)).save('scratch/inspected_letters/target_2_kha.png')
# ঝ: x=692 to 785, y=61 to 261
im2.crop((692, 61, 785, 261)).save('scratch/inspected_letters/target_3_jha.png')

# In consonants_2.png:
# Horizontal lines: [10, 51, 208, 229, 271, 428]
# Table 1: y=10 to 208 (headers y=10 to 51)
# Table 2: y=229 to 428 (headers y=229 to 271)
# Table 1 cols: মুদ্রণ, প, ফ, ব, ভ, ম, য, র, ল, ৱ
# Vertical lines in table 1:
# [16, 122, 189, 256, 323, 389, 456, 523, 590, 695, 783]
# Col 0 (Headers): 16 to 122
# Col 1 (প): 122 to 189
# Col 2 (ফ): 189 to 256
# Col 3 (ব): 256 to 323
# Col 4 (ভ): 323 to 389
im3.crop((189, 10, 256, 208)).save('scratch/inspected_letters/target_4_pha.png')
im3.crop((323, 10, 389, 208)).save('scratch/inspected_letters/target_5_bha.png')

# Table 2 cols: মুদ্রণ, শ, ষ, স, হ, ক্ষ, জ্ঞ, ড়, ঢ়, য়, ৎ
# Col 0 (Headers): 16 to 122
# Let's find vertical lines in table 2:
# x: 695 to 783 is য়, 783 to 1000 is ৎ
im3.crop((695, 229, 783, 428)).save('scratch/inspected_letters/target_6_yya.png')
im3.crop((783, 229, 930, 428)).save('scratch/inspected_letters/target_7_khandatta.png')

# Modifiers in modifiers.png:
# Vertical lines: [29, 136, 203, 270, 337, 404, 471]
# Col 0 (Headers): 29 to 136
# Col 1 (্): 136 to 203
# Col 2 (ং): 203 to 270
# Col 3 (ঃ): 270 to 337
# Col 4 (ঁ): 337 to 404
# Col 5 (ঽ): 404 to 471
im4.crop((203, 65, 270, 213)).save('scratch/inspected_letters/target_8_anushar.png')
im4.crop((270, 65, 337, 213)).save('scratch/inspected_letters/target_9_bisharga.png')
im4.crop((337, 65, 404, 213)).save('scratch/inspected_letters/target_10_chandrabindu.png')

print("All 10 target crops saved to scratch/inspected_letters/!")
