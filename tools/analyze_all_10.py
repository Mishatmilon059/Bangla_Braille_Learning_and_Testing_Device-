import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def analyze_dots_ascii(img_path, title):
    im = Image.open(img_path).convert('L')
    arr = np.array(im)
    h, w = arr.shape
    print(f"\n==========================================")
    print(f"{title} ({w}x{h})")
    print(f"==========================================")
    for y in range(0, h, max(1, h // 30)):
        line = ""
        for x in range(0, w, max(1, w // 45)):
            val = arr[y, x]
            if val < 60:
                line += "#"
            elif val < 175:
                line += "o"
            elif val < 210:
                line += "."
            else:
                line += " "
        print(line)

analyze_dots_ascii('scratch/inspected_letters/target_1_ri.png', '1. ঋ (Rri)')
analyze_dots_ascii('scratch/inspected_letters/target_2_kha.png', '2. খ (Kha)')
analyze_dots_ascii('scratch/inspected_letters/target_3_jha.png', '3. ঝ (Jha)')
analyze_dots_ascii('scratch/inspected_letters/target_4_pha.png', '4. ফ (Pha)')
analyze_dots_ascii('scratch/inspected_letters/target_5_bha.png', '5. ভ (Bha)')
analyze_dots_ascii('scratch/inspected_letters/target_6_yya.png', '6. য় (Yya)')
analyze_dots_ascii('scratch/inspected_letters/target_7_khandatta.png', '7. ৎ (Khandatta)')
analyze_dots_ascii('scratch/inspected_letters/target_8_anushar.png', '8. ং (Anushar)')
analyze_dots_ascii('scratch/inspected_letters/target_9_bisharga.png', '9. ঃ (Bisharga)')
analyze_dots_ascii('scratch/inspected_letters/target_10_chandrabindu.png', '10. ঁ (Chandrabindu)')
