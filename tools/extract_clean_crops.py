import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect the exact structure of:
# 1. vowels.png (Image 1):
# Table 1:
# Header: y = 63 to 101 (মুদ্রণ)
# Row 1: y = 101 to 155? Let's check where the divider is!
im1 = Image.open('scratch/wiki_crops/vowels.png')
# Let's save the entire column for ঋ (x: 735 to 842, y: 0 to 237)
im1.crop((735, 0, 842, 237)).save('scratch/wiki_crops/full_col_ri.png')

# 2. consonants_1.png (Image 2):
# In top table:
# Header: y = 61 to 103 (মুদ্রণ)
# Row 1 (বাংলাদেশ): y = 103 to 182
# Row 2 (ভারত): y = 182 to 261
im2 = Image.open('scratch/wiki_crops/consonants_1.png')
# খ is x: 196 to 290
im2.crop((196, 103, 290, 182)).save('scratch/wiki_crops/kha_bangladesh.png')
im2.crop((196, 182, 290, 261)).save('scratch/wiki_crops/kha_india.png')

# ঝ is x: 692 to 785
im2.crop((692, 103, 785, 182)).save('scratch/wiki_crops/jha_bangladesh.png')
im2.crop((692, 182, 785, 261)).save('scratch/wiki_crops/jha_india.png')

# 3. consonants_2.png (Image 3):
# Top table:
# Header: y = 10 to 51 (মুদ্রণ)
# Row 1 (বাংলাদেশ): y = 51 to 130
# Row 2 (ভারত): y = 130 to 208
im3 = Image.open('scratch/wiki_crops/consonants_2.png')
# ফ is x: 189 to 256. Notice: in table, does ফ have separate rows for Bangladesh and India or one row?
# Let's crop the entire column for ফ: y: 10 to 208
im3.crop((189, 10, 256, 208)).save('scratch/wiki_crops/full_col_pha.png')
# ভ is x: 323 to 389:
im3.crop((323, 10, 389, 208)).save('scratch/wiki_crops/full_col_bha.png')

# Bottom table of consonants_2.png:
# Header: y = 229 to 271 (মুদ্রণ)
# Row 1 (বাংলাদেশ): y = 271 to 350
# Row 2 (ভারত): y = 350 to 428
# য় is x: 695 to 783:
im3.crop((695, 229, 783, 428)).save('scratch/wiki_crops/full_col_yya.png')
# ৎ is x: 783 to 930:
im3.crop((783, 229, 930, 428)).save('scratch/wiki_crops/full_col_khandatta.png')

# 4. modifiers.png (Image 4):
# Header: y = 65 to 107 (মুদ্রণ)
# Content: y = 107 to 213 (বাংলাদেশ ও ভারত)
im4 = Image.open('scratch/wiki_crops/modifiers.png')
im4.crop((203, 107, 270, 213)).save('scratch/wiki_crops/anushar.png')
im4.crop((270, 107, 337, 213)).save('scratch/wiki_crops/bisharga.png')
im4.crop((337, 107, 404, 213)).save('scratch/wiki_crops/chandrabindu.png')

print("Saved all extracted columns!")
