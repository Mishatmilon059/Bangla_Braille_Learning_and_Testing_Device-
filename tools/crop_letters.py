import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect Image 1: Vowels
# Size: (1024, 237)
# Let's crop across width for columns
im1 = Image.open('scratch/wiki_crops/vowels.png')
w1, h1 = im1.size
# Columns: মুদ্রণ, অ, আ, ই, ঈ, উ, ঊ, এ, ঐ, ও, ঔ, ঋ, ঌ
# ঋ is the second to last column
# Let's crop x from 700 to 950, y from 0 to h1
crop_ri = im1.crop((700, 0, 950, h1))
crop_ri.save('scratch/wiki_crops/crop_ri.png')

# Image 2: Consonants 1
# Size: (928, 449)
# Top table: মুদ্রণ, ক, খ, গ, ঘ, ঙ, চ, ছ, জ, ঝ, ঞ
# Bottom table: মুদ্রণ, ট, ঠ, ড, ঢ, ণ, ত, থ, দ, ধ, ন
im2 = Image.open('scratch/wiki_crops/consonants_1.png')
# খ is column 2 in top table (approx x=150 to 300, y=0 to 250)
crop_kha = im2.crop((150, 0, 320, 260))
crop_kha.save('scratch/wiki_crops/crop_kha.png')

# ঝ is column 9 in top table (approx x=700 to 860, y=0 to 260)
crop_jha = im2.crop((700, 0, 860, 260))
crop_jha.save('scratch/wiki_crops/crop_jha.png')

# Image 3: Consonants 2
# Size: (1024, 441)
# Top table: মুদ্রণ, প, ফ, ব, ভ, ম, য, র, ল, ৱ
# Bottom table: মুদ্রণ, শ, ষ, স, হ, ক্ষ, জ্ঞ, ড়, ঢ়, য়, ৎ
im3 = Image.open('scratch/wiki_crops/consonants_2.png')
# ফ is column 2 (approx x=150 to 280, y=0 to 220)
crop_pha = im3.crop((150, 0, 280, 220))
crop_pha.save('scratch/wiki_crops/crop_pha.png')

# ভ is column 4 (approx x=320 to 440, y=0 to 220)
crop_bha = im3.crop((300, 0, 430, 220))
crop_bha.save('scratch/wiki_crops/crop_bha.png')

# য় is column 9 in bottom table (approx x=700 to 860, y=200 to 441)
crop_yya = im3.crop((700, 200, 850, 441))
crop_yya.save('scratch/wiki_crops/crop_yya.png')

# ৎ is column 10 in bottom table (approx x=820 to 1024, y=200 to 441)
crop_khandatta = im3.crop((820, 200, 1024, 441))
crop_khandatta.save('scratch/wiki_crops/crop_khandatta.png')

# Image 4: Modifiers
# Size: (509, 233)
# Columns: মুদ্রণ, ্, ং, ঃ, ঁ, ঽ
im4 = Image.open('scratch/wiki_crops/modifiers.png')
# Let's save each modifier column
crop_anushar = im4.crop((180, 0, 280, 233))
crop_anushar.save('scratch/wiki_crops/crop_anushar.png')

crop_bisharga = im4.crop((270, 0, 360, 233))
crop_bisharga.save('scratch/wiki_crops/crop_bisharga.png')

crop_chandrabindu = im4.crop((350, 0, 440, 233))
crop_chandrabindu.save('scratch/wiki_crops/crop_chandrabindu.png')

print("Cropped all candidate regions.")
