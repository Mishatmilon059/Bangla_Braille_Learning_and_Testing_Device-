import json
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open('data/braille_map.json', encoding='utf-8') as f:
    bm = json.load(f)

targets = ['ঋ', 'খ', 'ঝ', 'ফ', 'ভ', 'ঁ', 'ঃ', 'ং', 'ৎ', 'য়']
for item in bm['letters']:
    if item['char'] in targets or item['name'] in ['ri', 'kha', 'jha', 'pha', 'bha', 'chandrabindu', 'bisharga', 'anushar', 'khanda_ta', 'yya']:
        print(f"ID {item['id']:2d}: {item['char']} ({item['name']:14s}) -> dots: {item.get('dots')}, cells: {item.get('cells')}")
