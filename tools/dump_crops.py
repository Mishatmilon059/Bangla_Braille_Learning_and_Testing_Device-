import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

img_dir = r"C:\Users\Milon\.gemini\antigravity\brain\12f349ad-0e16-41c7-ab14-0be4cf1881f6\.user_uploaded"
im1 = Image.open(os.path.join(img_dir, "media_1789639442524.png")) # Vowels
im2 = Image.open(os.path.join(img_dir, "media_1789639460591.png")) # Consonants 1 (ক - ন)
im3 = Image.open(os.path.join(img_dir, "media_1789639478149.png")) # Consonants 2 (প - ৎ)
im4 = Image.open(os.path.join(img_dir, "media_1789639494289.png")) # Modifiers (্ - ঽ)

os.makedirs('scratch/wiki_crops', exist_ok=True)

# Let's save debug crops for inspecting each letter
# Image 1 (Vowels): ঋ is near the right side
im1.save('scratch/wiki_crops/vowels.png')
im2.save('scratch/wiki_crops/consonants_1.png')
im3.save('scratch/wiki_crops/consonants_2.png')
im4.save('scratch/wiki_crops/modifiers.png')

print("Saved raw images to scratch/wiki_crops/")
