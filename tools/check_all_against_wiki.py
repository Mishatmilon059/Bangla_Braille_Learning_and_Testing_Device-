import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# The Wikipedia Bangladesh Braille Standard extracted from the 4 user images:
WIKI_BANGLADESH = {
    # Vowels (Image 1)
    "অ": [1],
    "আ": [3, 4, 5],
    "ই": [2, 4],
    "ঈ": [3, 5],
    "উ": [1, 3, 6],
    "ঊ": [1, 2, 5, 6],
    "ঋ": [1, 2, 3, 5], # 2-cell: prefix [5] + [1, 2, 3, 5]
    "এ": [1, 5],
    "ঐ": [3, 4],
    "ও": [1, 3, 5],
    "ঔ": [2, 4, 6],
    
    # Consonants 1 (Image 2)
    "ক": [1, 3],
    "খ": [1, 3, 4, 6], # Bangladesh: [1, 3, 4, 6]
    "গ": [1, 2, 4, 5],
    "ঘ": [1, 2, 6],
    "ঙ": [3, 4, 6],
    "চ": [1, 4],
    "ছ": [1, 6],
    "জ": [2, 4, 5],
    "ঝ": [1, 3, 5, 6], # Bangladesh: [1, 3, 5, 6]
    "ঞ": [2, 5],
    "ট": [2, 3, 4, 5, 6],
    "ঠ": [2, 4, 5, 6],
    "ড": [1, 2, 4, 6],
    "ঢ": [1, 2, 3, 4, 5, 6],
    "ণ": [3, 4, 5, 6],
    "ত": [2, 3, 4, 5],
    "থ": [1, 4, 5, 6],
    "দ": [1, 4, 5],
    "ধ": [2, 3, 4, 6],
    "ন": [1, 3, 4, 5],
    
    # Consonants 2 (Image 3)
    "প": [1, 2, 3, 4],
    "ফ": [2, 3, 5],     # Bangladesh & India: [2, 3, 5]
    "ব": [1, 2],
    "ভ": [1, 2, 3, 6], # Bangladesh: [1, 2, 3, 6]
    "ম": [1, 3, 4],
    "য": [1, 3, 4, 5, 6],
    "র": [1, 2, 3, 5],
    "ল": [1, 2, 3],
    "শ": [1, 4, 6],
    "ষ": [1, 2, 3, 4, 6],
    "স": [2, 3, 4],
    "হ": [1, 2, 5],
    "ড়": [1, 2, 4, 5, 6],
    "ঢ়": [1, 2, 3, 5, 6],
    "য়": [2, 6],       # Bangladesh & India: [2, 6]
    "ৎ": [2, 3, 4, 5], # Bangladesh: prefix [5] + [2, 3, 4, 5]
    
    # Modifiers (Image 4)
    "ং": [5, 6],
    "ঃ": [6],
    "ঁ": [3],
}

with open('data/braille_map.json', encoding='utf-8') as f:
    bm = json.load(f)

print(f"Comparing all {len(bm['letters'])} letters in data/braille_map.json against Wikipedia images:")
all_match = True
for item in bm['letters']:
    char = item['char']
    if char in WIKI_BANGLADESH:
        expected = WIKI_BANGLADESH[char]
        actual = item['dots']
        if expected != actual:
            print(f"MISMATCH in map for {char} ({item['name']}): expected {expected}, got {actual}")
            all_match = False
    else:
        print(f"Character {char} not in Wiki Bangladesh dict!")
        all_match = False

if all_match:
    print("ALL 50 characters in data/braille_map.json 100% MATCH Wikipedia Bangladesh standard!")
else:
    print("Found discrepancies in data/braille_map.json!")
