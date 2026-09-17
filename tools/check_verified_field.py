import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/braille_map.json', encoding='utf-8') as f:
    bm = json.load(f)

unverified = [l for l in bm['letters'] if not l.get('verified')]
print(f"Top-level 'verified': {bm.get('verified')}")
print(f"Letters verified: {len(bm['letters']) - len(unverified)} / {len(bm['letters'])}")
if unverified:
    print("Unverified letters:")
    for u in unverified:
        print(f"  ID {u['id']:2d}: {u['char']} ({u['name']})")
