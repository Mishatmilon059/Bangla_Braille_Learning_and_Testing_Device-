import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect the 4 images
img_dir = r"C:\Users\Milon\.gemini\antigravity\brain\12f349ad-0e16-41c7-ab14-0be4cf1881f6\.user_uploaded"
images = [
    os.path.join(img_dir, "media_1789639442524.png"), # Vowels
    os.path.join(img_dir, "media_1789639460591.png"), # Consonants 1
    os.path.join(img_dir, "media_1789639478149.png"), # Consonants 2
    os.path.join(img_dir, "media_1789639494289.png"), # Modifiers
]

for idx, p in enumerate(images, 1):
    im = Image.open(p)
    print(f"Image {idx}: {im.size}, mode {im.mode}")
