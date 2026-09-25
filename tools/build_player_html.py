#!/usr/bin/env python3
"""Build audio_player.html artifact with base64 embedded MP3s."""

import base64
import json
from pathlib import Path

ARTIFACT_DIR = Path(r"C:\Users\Milon\.gemini\antigravity\brain\d6d171f6-bf3a-4d6c-8013-66ce1dea38e2")
SD_MP3_DIR = Path(r"d:\eee-416 project\sd_card\mp3")

tracks = [
    (61, "পরীক্ষা শুরু হচ্ছে", "0061.mp3", "cue"),
    (62, "পরীক্ষা শেষ", "0062.mp3", "cue"),
    (51, "সঠিক", "0051.mp3", "cue"),
    (52, "ভুল", "0052.mp3", "cue"),
    (63, "ধন্যবাদ", "0063.mp3", "cue"),
    (70, "০ (শূন্য)", "0070.mp3", "num"),
    (71, "১ (এক)", "0071.mp3", "num"),
    (72, "২ (দুই)", "0072.mp3", "num"),
    (73, "৩ (তিন)", "0073.mp3", "num"),
    (74, "৪ (চার)", "0074.mp3", "num"),
    (75, "৫ (পাঁচ)", "0075.mp3", "num"),
    (76, "৬ (ছয়)", "0076.mp3", "num"),
    (77, "৭ (সাত)", "0077.mp3", "num"),
    (78, "৮ (আট)", "0078.mp3", "num"),
    (79, "৯ (নয়)", "0079.mp3", "num"),
    (80, "১০ (দশ)", "0080.mp3", "num"),
]

audio_dict = {}
for track, label, filename, cat in tracks:
    p = SD_MP3_DIR / filename
    if p.exists():
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        audio_dict[str(track)] = {
            "track": track,
            "label": label,
            "cat": cat,
            "file": filename,
            "uri": f"data:audio/mp3;base64,{b64}",
        }

html_content = f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="utf-8">
  <title>বাংলা ব্রেইল ডিভাইস - অডিও প্লেয়ার</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    @keyframes pulse-ring {{
      0% {{ transform: scale(0.95); opacity: 0.8; }}
      50% {{ transform: scale(1.05); opacity: 1; }}
      100% {{ transform: scale(0.95); opacity: 0.8; }}
    }}
    .playing {{
      animation: pulse-ring 1s infinite;
      border-color: #22c55e !important;
      background-color: rgba(34, 197, 94, 0.15) !important;
    }}
  </style>
</head>
<body class="bg-transparent text-[var(--foreground)] antialiased p-4 font-sans">
  <div class="max-w-2xl mx-auto bg-[var(--card)] text-[var(--foreground)] border border-[var(--border)] rounded-2xl p-6 shadow-lg">

    <!-- Header -->
    <div class="flex items-center justify-between border-b border-[var(--border)] pb-4 mb-5">
      <div>
        <h2 class="text-xl font-bold flex items-center gap-2">
          <span>🔊</span> বাংলা ব্রেইল পরীক্ষার অডিও প্লেয়ার
        </h2>
        <p class="text-xs text-[var(--muted-foreground)] mt-1">
          DFPlayer Mini ও ওয়েব অ্যাপের জন্য প্রস্তুতকৃত ভয়েস প্রম্পট
        </p>
      </div>
      <div id="status-pill" class="text-xs font-semibold px-3 py-1 rounded-full bg-[var(--background)] border border-[var(--border)] text-[var(--muted-foreground)]">
        অপেক্ষমান
      </div>
    </div>

    <!-- Interactive Simulation Banner -->
    <div class="bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-blue-500/10 border border-emerald-500/30 rounded-xl p-4 mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
          পরীক্ষা শেষ সিকোয়েন্স ডেমো
        </span>
        <span id="seq-step" class="text-xs font-medium text-[var(--muted-foreground)]"></span>
      </div>
      <p class="text-xs text-[var(--muted-foreground)] mb-3">
        ১০টি বর্ণ পরীক্ষা শেষ হলে ESP32 স্পিকারে স্বয়ংক্রিয়ভাবে যেভাবে ফলাফল ঘোষণা করবে:
      </p>
      <div class="flex flex-wrap gap-2">
        <button id="btn-run-seq" onclick="playSequence([62, 51, 72, 52, 71, 63])" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-2">
          <span>▶</span> পুরো ফলাফল ঘোষণা শুনুন (সঠিক ২, ভুল ১)
        </button>
        <button id="btn-test-start-demo" onclick="playTrack(61)" class="px-3 py-2 bg-[var(--background)] border border-[var(--border)] hover:bg-[var(--border)] text-xs font-medium rounded-lg transition">
          ▶ পরীক্ষা শুরু ঘোষণা
        </button>
      </div>
    </div>

    <!-- Section: Cues -->
    <div class="mb-6">
      <h3 class="text-sm font-bold uppercase tracking-wider text-[var(--muted-foreground)] mb-3 flex items-center gap-2">
        <span>📢</span> পরীক্ষার মূল ঘোষণা (Cues)
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        <button onclick="playTrack(61)" id="btn-track-61" class="track-btn p-3 bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 rounded-xl text-left transition flex items-center justify-between group">
          <div>
            <div class="text-xs font-mono text-[var(--muted-foreground)]">Track 61</div>
            <div class="text-sm font-semibold">পরীক্ষা শুরু হচ্ছে</div>
          </div>
          <span class="text-base group-hover:scale-110 transition">🔊</span>
        </button>

        <button onclick="playTrack(62)" id="btn-track-62" class="track-btn p-3 bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 rounded-xl text-left transition flex items-center justify-between group">
          <div>
            <div class="text-xs font-mono text-[var(--muted-foreground)]">Track 62</div>
            <div class="text-sm font-semibold">পরীক্ষা শেষ</div>
          </div>
          <span class="text-base group-hover:scale-110 transition">🔊</span>
        </button>

        <button onclick="playTrack(51)" id="btn-track-51" class="track-btn p-3 bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 rounded-xl text-left transition flex items-center justify-between group">
          <div>
            <div class="text-xs font-mono text-[var(--muted-foreground)]">Track 51</div>
            <div class="text-sm font-semibold text-emerald-600 dark:text-emerald-400">সঠিক</div>
          </div>
          <span class="text-base group-hover:scale-110 transition">✓</span>
        </button>

        <button onclick="playTrack(52)" id="btn-track-52" class="track-btn p-3 bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 rounded-xl text-left transition flex items-center justify-between group">
          <div>
            <div class="text-xs font-mono text-[var(--muted-foreground)]">Track 52</div>
            <div class="text-sm font-semibold text-rose-600 dark:text-rose-400">ভুল</div>
          </div>
          <span class="text-base group-hover:scale-110 transition">✕</span>
        </button>

        <button onclick="playTrack(63)" id="btn-track-63" class="track-btn p-3 bg-[var(--background)] border border-[var(--border)] hover:border-emerald-500 rounded-xl text-left transition flex items-center justify-between group sm:col-span-2">
          <div>
            <div class="text-xs font-mono text-[var(--muted-foreground)]">Track 63</div>
            <div class="text-sm font-semibold">ধন্যবাদ</div>
          </div>
          <span class="text-base group-hover:scale-110 transition">🙏</span>
        </button>
      </div>
    </div>

    <!-- Section: Numbers -->
    <div>
      <h3 class="text-sm font-bold uppercase tracking-wider text-[var(--muted-foreground)] mb-3 flex items-center gap-2">
        <span>🔢</span> ফলাফল ঘোষণার সংখ্যা (০ থেকে ১০)
      </h3>
      <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
        <button onclick="playTrack(70)" id="btn-track-70" class="track-btn p-2.5 bg-[var(--background)] border border-[var(--border)] hover:border-blue-500 rounded-xl text-center transition">
          <div class="text-xs font-bold">০</div>
          <div class="text-[11px] text-[var(--muted-foreground)]">শূন্য</div>
        </button>
        <button onclick="playTrack(71)" id="btn-track-71" class="track-btn p-2.5 bg-[var(--background)] border border-[var(--border)] hover:border-blue-500 rounded-xl text-center transition">
          <div class="text-xs font-bold">১</div>
          <div class="text-[11px] text-[var(--muted-foreground)]">এক</div>
        </button>
        <button onclick="playTrack(72)" id="btn-track-72" class="track-btn p-2.5 bg-[var(--background)] border border-[var(--border)] hover:border-blue-500 rounded-xl text-center transition">
          <div class="text-xs font-bold">২</div>
          <div class="text-[11px] text-[var(--muted-foreground)]">দুই</div>
        </button>
        <button onclick="playTrack(73)" id="btn-track-73" class="track-btn p-2.5 bg-[var(--background)] border border-[var(--border)] hover:border-blue-500 rounded-xl text-center transition">
          <div class="text-xs font-bold">৩</div>
          <div class="text-[11px] text-[var(--muted-foreground)]">তিন</div>
        </button>
        <button onclick="playTrack(74)" id="btn-track-74" class="track-btn p-2.5 bg-[var(--background)] border border-[var(--border)] hover:border-blue-500 rounded-xl text-center transition">
          <div class="text-xs font-bold">৪</div>
          <div class="text-[11px] text-[var(--muted-foreground)]">চার</div>
        </button>
        <button onclick="playTrack(75)" id="btn-track-75" class="track-btn p-2.5 bg-[var(--background)] border border-[var(--border)] hover:border-blue-500 rounded-xl text-center transition">
          <div class="text-xs font-bold">৫</div>
          <div class="text-[11px] text-[var(--muted-foreground)]">পাঁচ</div>
        </button>
        <button onclick="playTrack(76)" id="btn-track-76" class="track-btn p-2.5 bg-[var(--background)] border border-[var(--border)] hover:border-blue-500 rounded-xl text-center transition">
          <div class="text-xs font-bold">৬</div>
          <div class="text-[11px] text-[var(--muted-foreground)]">ছয়</div>
        </button>
        <button onclick="playTrack(77)" id="btn-track-77" class="track-btn p-2.5 bg-[var(--background)] border border-[var(--border)] hover:border-blue-500 rounded-xl text-center transition">
          <div class="text-xs font-bold">৭</div>
          <div class="text-[11px] text-[var(--muted-foreground)]">সাত</div>
        </button>
        <button onclick="playTrack(78)" id="btn-track-78" class="track-btn p-2.5 bg-[var(--background)] border border-[var(--border)] hover:border-blue-500 rounded-xl text-center transition">
          <div class="text-xs font-bold">৮</div>
          <div class="text-[11px] text-[var(--muted-foreground)]">আট</div>
        </button>
        <button onclick="playTrack(79)" id="btn-track-79" class="track-btn p-2.5 bg-[var(--background)] border border-[var(--border)] hover:border-blue-500 rounded-xl text-center transition">
          <div class="text-xs font-bold">৯</div>
          <div class="text-[11px] text-[var(--muted-foreground)]">নয়</div>
        </button>
        <button onclick="playTrack(80)" id="btn-track-80" class="track-btn p-2.5 bg-[var(--background)] border border-[var(--border)] hover:border-blue-500 rounded-xl text-center transition">
          <div class="text-xs font-bold">১০</div>
          <div class="text-[11px] text-[var(--muted-foreground)]">দশ</div>
        </button>
      </div>
    </div>

  </div>

  <script>
    const AUDIOS = {json.dumps(audio_dict)};
    let currentAudio = null;

    function playTrack(trackId) {{
      return new Promise((resolve) => {{
        if (currentAudio) {{
          currentAudio.pause();
          currentAudio.currentTime = 0;
        }}
        document.querySelectorAll('.track-btn').forEach(b => b.classList.remove('playing'));

        const data = AUDIOS[String(trackId)];
        if (!data) {{ resolve(); return; }}

        const btn = document.getElementById('btn-track-' + trackId);
        if (btn) btn.classList.add('playing');

        const pill = document.getElementById('status-pill');
        pill.textContent = 'বাজছে: ' + data.label;
        pill.className = 'text-xs font-semibold px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/40';

        currentAudio = new Audio(data.uri);
        currentAudio.onended = () => {{
          if (btn) btn.classList.remove('playing');
          pill.textContent = 'শেষ হয়েছে';
          pill.className = 'text-xs font-semibold px-3 py-1 rounded-full bg-[var(--background)] border border-[var(--border)] text-[var(--muted-foreground)]';
          resolve();
        }};
        currentAudio.onerror = () => {{
          if (btn) btn.classList.remove('playing');
          resolve();
        }};
        currentAudio.play().catch(resolve);
      }});
    }}

    async function playSequence(tracks) {{
      const seqBtn = document.getElementById('btn-run-seq');
      seqBtn.disabled = true;
      seqBtn.classList.add('opacity-50');

      for (let i = 0; i < tracks.length; i++) {{
        const t = tracks[i];
        const data = AUDIOS[String(t)];
        document.getElementById('seq-step').textContent = `পদক্ষেপ ${{i + 1}}/${{tracks.length}}: ${{data?.label || ''}}`;
        await playTrack(t);
        await new Promise(r => setTimeout(r, 250));
      }}

      document.getElementById('seq-step').textContent = 'সিকোয়েন্স সমাপ্ত!';
      seqBtn.disabled = false;
      seqBtn.classList.remove('opacity-50');
    }}
  </script>
</body>
</html>
"""

target = ARTIFACT_DIR / "audio_player.html"
target.write_text(html_content, encoding="utf-8")
print(f"Written audio_player.html to {target}")
