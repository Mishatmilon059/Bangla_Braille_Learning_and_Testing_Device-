#!/usr/bin/env python3
"""Generate examination audio cues and Bengali numbers for the Bangla Braille device.

Generated tracks:
  61: "পরীক্ষা শুরু হচ্ছে" (Test start)
  62: "পরীক্ষা শেষ"         (Test end)
  63: "ধন্যবাদ"              (Thank you)
  70..120: Numbers 0 to 50 in Bengali ("শূন্য", "এক", "দুই", ...)
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path
from gtts import gTTS

ROOT = Path(__file__).resolve().parent.parent
SD_DIR = ROOT / "sd_card" / "mp3"
WEB_DIR = ROOT / "web" / "audio"
WEBAPP_DIR = ROOT / "webapp" / "public" / "audio"

GTTS_LANG = "bn"
GTTS_SLOW = True
MP3_RATE = "44100"
MP3_BITRATE = "64k"
LEAD_SILENCE_MS = 150
TAIL_SILENCE_S = 0.15

CUES = [
    (61, "পরীক্ষা শুরু হচ্ছে"),
    (62, "পরীক্ষা শেষ"),
    (63, "ধন্যবাদ"),
]

BENGALI_NUMBERS = [
    "শূন্য", "এক", "দুই", "তিন", "চার", "পাঁচ", "ছয়", "সাত", "আট", "নয়", "দশ",
    "এগারো", "বারো", "তেরো", "চৌদ্দ", "পনেরো", "ষোলো", "সতেরো", "আঠারো", "উনিশ", "বিশ",
    "একুশ", "বাইশ", "তেইশ", "চব্বিশ", "পঁচিশ", "ছাব্বিশ", "সাতাশ", "আঠাশ", "উনত্রিশ", "ত্রিশ",
    "একত্রিশ", "বত্রিশ", "তেত্রিশ", "চৌত্রিশ", "পঁয়ত্রিশ", "ছত্রিশ", "সাইত্রিশ", "আটত্রিশ", "উনচল্লিশ", "চল্লিশ",
    "একচল্লিশ", "বিয়াল্লিশ", "তেতাল্লিশ", "চুয়াল্লিশ", "পঁয়তাল্লিশ", "ছেচল্লিশ", "সাতচল্লিশ", "আটচল্লিশ", "উনপঞ্চাশ", "পঞ্চাশ"
]

NUMBER_START_TRACK = 70


def synth(text, track, out_dirs):
    raw = ROOT / f".tmp_{track:04d}_raw.mp3"
    print(f"Generating track {track:04d} ({text})...")
    gTTS(text=text, lang=GTTS_LANG, slow=GTTS_SLOW).save(str(raw))

    first = out_dirs[0] / f"{track:04d}.mp3"
    af = f"adelay={LEAD_SILENCE_MS}:all=1,apad=pad_dur={TAIL_SILENCE_S}"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
         "-af", af, "-ac", "1", "-ar", MP3_RATE, "-b:a", MP3_BITRATE, str(first)],
        check=True,
    )
    for d in out_dirs[1:]:
        shutil.copy(first, d / f"{track:04d}.mp3")
    raw.unlink(missing_ok=True)
    time.sleep(0.5)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    dirs = [SD_DIR, WEB_DIR, WEBAPP_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    print("--- Generating Test Cues ---")
    for track, text in CUES:
        synth(text, track, dirs)

    print("--- Generating Numbers (0 to 50) ---")
    for i, text in enumerate(BENGALI_NUMBERS):
        track = NUMBER_START_TRACK + i
        synth(text, track, dirs)

    print("\nAll audio generated successfully!")


if __name__ == "__main__":
    main()
