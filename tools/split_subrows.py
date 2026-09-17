import numpy as np
from PIL import Image

def inspect_crop(path, name):
    im = Image.open(path).convert('RGB')
    arr = np.array(im)
    h, w, _ = arr.shape
    gray = np.mean(arr, axis=2)
    
    # Check for horizontal dividers
    dividers = []
    for y in range(h):
        # check if row is a horizontal border
        if np.sum((gray[y, :] >= 150) & (gray[y, :] <= 215)) > w * 0.6:
            dividers.append(y)
    print(f"\n=== {name} ({w}x{h}) ===")
    print("Internal horizontal dividers:", dividers)
    
    # Let's save Bangladesh (top) and India (bottom) if divider exists
    if dividers:
        mid_y = dividers[len(dividers)//2]
        top = im.crop((0, 0, w, mid_y))
        bot = im.crop((0, mid_y, w, h))
        top.save(f"scratch/inspected_letters/{name}_bd.png")
        bot.save(f"scratch/inspected_letters/{name}_in.png")
        print(f"Saved {name}_bd.png (top: {top.size}) and {name}_in.png (bot: {bot.size})")
    else:
        im.save(f"scratch/inspected_letters/{name}_single.png")

inspect_crop('scratch/inspected_letters/12_kha.png', 'kha')
inspect_crop('scratch/inspected_letters/19_jha.png', 'jha')
inspect_crop('scratch/inspected_letters/06_ri.png', 'ri')
