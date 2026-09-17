# Bangla Braille Tutor — AI-assisted, offline on ESP32

Teaches Bangla Braille, logs learner interaction data, trains a small
multi-task model on that data, and runs it **fully offline** on an ESP32 with
push buttons, vibration motors, and audio.

Three pieces:

| Piece | What it is | Where |
|---|---|---|
| **MVP web app** | Data-collection instrument. Single page, no build step. | `web/` |
| **Training pipeline** | CSV → multi-task sklearn MLP → C float arrays | `tools/` |
| **Firmware** | ESP32 sketch, no WiFi, inference on-device | `firmware/` |

---

## The one thing to understand before changing anything

Two data files are the source of truth. Almost everything else is **generated**:

```
spec/engine_spec.json  ──gen_engine.py──────►  web/rule_engine.js
                                               firmware/braille_tutor/rule_engine.h
                                               tools/rule_engine_gen.py

data/braille_map.json  ──gen_braille_header.py──►  firmware/braille_tutor/braille_map.h
                       ──gen_braille_images.py──►  assets/braille/*.svg, *.png
                       ──gen_audio.py───────────►  web/audio/, sd_card/mp3/

dataset/real_v3.csv  ──train_and_export.py──►  firmware/braille_tutor/model_weights.h
dataset/synthetic_2k.csv                        models/metrics_final.json
                                                models/golden_vectors.json
```

This exists to kill one bug class: the web app and the ESP32 computing features
or rules slightly differently, so a model trained on web-collected data
misbehaves on hardware. `tools/test_parity.py` proves all three rule engines
agree on every vector. **Never hand-edit a generated file.** Edit the spec,
regenerate, re-run parity.

---

## Quick start

```bash
pip install scikit-learn numpy Pillow
sudo apt-get install -y espeak-ng ffmpeg

python3 tools/gen_engine.py            # 3 rule engines (JS, C, Python)
python3 tools/gen_braille_header.py    # firmware dot table
python3 tools/gen_braille_images.py    # 50 SVG + 50 PNG + contact sheet
python3 tools/gen_audio.py             # 50 letters + 10 prompts

python3 tools/import_braille_images.py --write   # read braille_img/ into the map
python3 tools/verify_braille_images.py           # QA sheet -- then look at it

python3 tools/run_all_tests.py         # everything must be green
```

Run the app — **serve the repository root**, not `web/`, because the app reads
`data/braille_map.json`:

```bash
python3 -m http.server 8000
# open http://localhost:8000/web/
```

---

## Braille verification status — 50 of 50

All 50 letters are now verified against the Bangladesh National Braille Code
(cross-checked against Wikipedia's Bengali Braille table) — `data/braille_map.json`
and the generated `firmware/braille_tutor/braille_map.h` both carry
`BRAILLE_MAP_VERIFIED 1` / `BRAILLE_VERIFIED_COUNT 50`. Every row's
`braille_map_verified` flag in logged data can be trusted.

### The ঋ / র collision, and how it's actually resolved

ঋ (ri) and র (ra) share the same 5-dot cell (`[1,2,3,5]`) — genuinely, per the
Braille standard, not a data error. They're told apart by making ঋ a
**two-cell** character: a short prefix vibration (dot 5) plays before the
answer cell, and the prompt audio itself also disambiguates them. See
`BRAILLE_PREFIX[]` in `firmware/braille_tutor/braille_map.h` and the
"Two-cell characters" section below for how the remote-mode sketches
(`t10_learning`, `t11_testing`, `t11_ml_test`) teach and test this.

### Re-verifying or re-deriving the map

If you ever need to re-check a pattern against a reference image:

```bash
python3 tools/import_braille_images.py           # dry run: shows what would change
python3 tools/import_braille_images.py --write
python3 tools/verify_braille_images.py           # then LOOK at the sheet
python3 tools/gen_braille_header.py
python3 tools/gen_braille_images.py
```

The importer **refuses to guess** a filename it does not recognise. That is
deliberate: your `uu.webp` is উ, which this project calls `u`, while your
`uuuu.webp` is ঊ, which it calls `uu`. The literal string `uu` means different
letters in the two schemes, so any fallback name matching would put one
letter's pattern on another — producing a map that passes every structural
check while being wrong. The alias table (`tools/braille_aliases.json`) is the
only lookup path.

---

## Workflow, in order

### 1. Collect real data — start this the day the app works

Calendar time is the constraint, not coding time. Sessions must be spread
across **several days per participant**, otherwise `session_number` and
`time_since_last_practice` have no variance and two of the 14 features are dead.

- Sighted volunteers doing eyes-closed recall produce realistic timing. You do
  not need visually-impaired participants at this stage.
- Target ~400 real attempts (the 40% share).
- Watch the **class balance** panel in the app while collecting. Any class stuck
  near zero is a problem you want to find on day 2, not at training time.
- Use **targeted** mode to make rare classes fire. It biases character
  selection toward genuinely stale and genuinely weak characters — it does not
  fabricate feature values.

**Supabase is already wired up** (`web/config.js` holds the project URL and
publishable key). Two things left to do once:

```bash
# 1. paste supabase/schema.sql into the Supabase SQL editor and run it
# 2. prove it works -- this was NOT runnable where the project was built,
#    because supabase.co is blocked by egress policy there
cp .env.example .env
python3 tools/test_supabase.py --write
```

`test_supabase.py` checks the things that actually break collection: that the
table exists, that the publishable key can INSERT (a project can be reachable
and readable while still rejecting writes), and that the dedupe index turns a
replayed row into a no-op — which is what the offline queue depends on when a
laptop reconnects mid-session.

Without any of this the app still runs fully offline and exports CSV per device.

**Key hygiene:** the publishable key in `web/config.js` is meant to be public —
RLS decides what it can do. The **secret** key bypasses RLS entirely and belongs
only in `.env` (gitignored). If it is ever pasted into a chat, a screenshot, or
a commit, rotate it in Supabase → Settings → API Keys. Rotation is instant.

### 2. Generate synthetic data — *after* step 1, not before

```bash
python3 tools/export_dataset.py --out dataset/real.csv
python3 tools/gen_synthetic.py --real dataset/real.csv --n 600
```

Order matters. `gen_synthetic.py` fits timing distributions to your real rows,
then simulates learners through the same state machine the web app uses. Run
before any real data exists and it falls back to priors — which are guesses,
and it says so loudly.

It simulates rather than sampling features independently, because independent
sampling produces impossible vectors (`current_streak=7` beside
`prev_mastery=0.02`) that waste model capacity on a region that cannot occur.

### 3. Train

```bash
python3 tools/train_and_export.py
```

Trains two sklearn MLPClassifiers (teaching-action head + confidence-state head)
on `dataset/real_v3.csv` + `dataset/synthetic_2k.csv`, then exports weights
directly as C float arrays into `firmware/braille_tutor/model_weights.h`.
Reports **real-only test accuracy** separately from combined, with a
majority-class baseline beside every number.

### 4. Hardware

Work through `firmware/tests/` **in order** — one peripheral per sketch. Do not
flash the main sketch first. See `firmware/tests/README.md`.

```
sd_card/mp3/  →  copy to the microSD card root (DFPlayer needs a folder named "mp3")
```

---

## What this model actually is — read before writing it up

The labels come from the rule engine. A **1,734-parameter** dual-head network
trained on them learns to **compress your if/else logic**, reaching ~99% agreement
on synthetic data and **98.6% / 91.4% real-only test accuracy** (teaching action /
confidence state) on 1,000 real collected rows.

**8 of the 14 logged features** are fed to the model:
`response_time`, `press_duration`, `retry_count`, `prev_accuracy`,
`prev_mastery`, `hint_count`, `current_streak`, `wrong_streak`.
The other 6 are logged for analysis but read by no rule, so the model has
nothing to gain from them.

Architecture: `Input(8) → Dense(32, ReLU) → Dense(16, ReLU) → [Dense(3) TA head, Dense(3) CS head]`

Implementation: sklearn `MLPClassifier` (TensorFlow is incompatible with Python 3.12
on Windows). Weights are exported as C float arrays — no TFLite, no arena,
no external library. `firmware/braille_tutor/inference.h` provides a self-contained
forward pass (~0.1 ms at 240 MHz).

Dataset: **1,000 real rows** (P01=315, P02=320, P03=364, P04=1) +
**1,242 synthetic** = 2,242 total. See `models/metrics_final.json` for per-class F1.

That is a legitimate embedded-ML result — train → export C arrays → real-time
offline inference at **6.9 KB** (1,734 × 4 bytes) — and it should be written up
that way. Describing it as autonomous adaptive learning would be false, and any
examiner who asks "where did the labels come from?" will find that out in one
question.

The genuinely interesting comparison is `t11_ml_test`: flash it and watch the
**MATCH/MISMATCH** log on Serial Monitor — the cases where the network departs
from the rule engine on real presses are the ones worth reading.

---

## Hardware

ESP32-WROOM-32 · DFPlayer Mini + 3 W speaker · **ULN2803A** · 6 coin motors ·
6 tactile dot buttons + 1 submit button · microSD module · 5 V 2 A supply ·
1000 µF cap · 6× 1 kΩ · 3× 10 kΩ · *(recommended)* DS3231 RTC

| Function | GPIO |
|---|---|
| Buttons 1–6 (dots) | 32, 33, 25, 26, 27, 14 |
| Submit | 12 *(strapping pin — must read LOW at boot; a switch to GND is safe here, see `pins.h`)* |
| Motors 1–6 → ULN2803A | 21, 13, 22, 2, 15, 4 *(verified against physical wiring — do not "correct" this back to a sequential-looking order)* |
| DFPlayer (UART2) | 16 RX, 17 TX |
| microSD (VSPI) | 18 CLK, 19 MISO, 23 MOSI, 5 CS |

`response_time` is measured from the end of the prompt audio to the debounced
**submit** press, not to the first dot press — the learner is expected to hold
the pattern on the 6 dot buttons, then press submit. `web/app.js` measures the
same way (prompt end → the submit click), so the two stay comparable.

Three things that will bite you, in order of likelihood:

1. **Use the ULN2803A, not discrete transistors.** Coin motors are inductive;
   it has flyback diodes built in (tie COM to +5 V). Driving them off a bare
   GPIO destroys pins.
2. **5 V 2 A supply + 1000 µF across the motor rail.** Six motors pull ~480 mA;
   with the ESP32 and DFPlayer you are near 800 mA peak. Motor inrush on a weak
   supply browns out the regulator and reboots the board mid-session — which
   looks exactly like a firmware crash and is not one.
3. **GPIO 2 and 15 are strapping pins** — add 10 kΩ pulldowns. GPIO 12 is
   deliberately unused; it must be LOW at boot.

**Fit:** model weights 6,936 B (1,734 floats) — **no arena, no runtime library**.
`inference.h` allocates two stack arrays (32 + 16 floats = 192 B) during the
forward pass and frees them immediately. Total: ≈ **7.1 KB of 520 KB SRAM**.
Size was never the risk on this project.

### The RTC, and why it matters

`millis()` resets on every power-up, so without an RTC the board cannot know how
long it was switched off — and `time_since_last_practice` is one of the 14
features the model consumes. Firmware handles this honestly rather than silently:
without an RTC it advances a persisted epoch by a **declared assumption** and
stamps every row `rtc_present=0`, so those rows stay auditable. A DS3231 costs
about $2 and removes the problem. Set `USE_RTC 1` in `pins.h` after wiring it.

---

## Remote / cloud-connected mode — teacher panel

`braille_tutor.ino` is deliberately WiFi-free, so the pieces below are a
**separate, parallel mode**: a teacher controls the board from a phone or
laptop anywhere with internet, over WiFi + Supabase, instead of the offline
on-device model. Nothing here replaces the offline track above — pick
whichever mode fits the session.

### The pieces

| Piece | What it does | Where |
|---|---|---|
| Teacher panel (web UI) | Pick Learn or Test mode, select letters, watch results live | `web/teacher.html` + `web/teacher.js` |
| Single-letter remote | Minimal page: pick one letter, send it | `web/remote_control.html` |
| **t10_learning** | Teach mode: audio + motor vibration teaches the pattern, retries until correct, reports every attempt | `firmware/tests/t10_learning/` |
| **t11_testing** | Assessment mode: audio only (no vibration cue), one attempt per letter, no retry, prints a batch summary to Serial when the teacher's whole selection is done | `firmware/tests/t11_testing/` |
| **t11_ml_test** | Same flow as t10_learning, but also runs the on-device ML model side-by-side with the rule engine after every attempt and prints MATCH/MISMATCH to Serial Monitor — **no data goes to Supabase** | `firmware/t11_ml_test/` |

Only flash **one** of `t10_learning` / `t11_testing` / `t11_ml_test` at a time
— whichever the teacher panel's current tab needs (শেখানো → t10_learning or
t11_ml_test, পরীক্ষা → t11_testing).

### How data moves

There is no direct connection between the browser and the ESP32 — everything
relays through two Supabase tables, polled (not pushed) by both sides:

```
[Teacher selects letters, clicks Start]
        │  INSERT
        ▼
  remote_commands   { device_id, letter_id, command: "play"|"test",
                       test_index, test_total }
        │  polled by the ESP32 every ~250 ms
        ▼
  ESP32 plays audio (+ vibration in Learn mode), waits for the
  physical dot buttons + SUBMIT -- there is no web input path
        │  INSERT
        ▼
  attempts   { char_id, entered_pattern, expected_pattern, is_correct,
               response_time, retry_count, teaching_action,
               confidence_state, source: "esp32", ... }
        │  polled by the browser every ~200 ms
        ▼
  Teacher panel shows the result live and sends the next letter.
  After the last letter in a Test run: test_sessions + student_weaknesses
  get written too, for the results screen and per-letter mastery dots.
```

`test_index`/`test_total` on `remote_commands` are how the ESP32 knows its
position in the teacher's batch and when to print the final score to Serial
— they're only set for `command: "test"` rows.

### One-time setup

```bash
# 1. paste supabase/full_setup.sql into the Supabase SQL editor and run it
#    (creates/updates remote_commands, attempts, test_sessions, student_weaknesses)
# 2. per sketch you plan to flash, open its secrets.h and fill in your real
#    WIFI_SSID / WIFI_PASS -- e.g. firmware/tests/t10_learning/secrets.h
```

**Never commit a `secrets.h` with real credentials.** Every sketch's
`secrets.h` is already gitignored (see `.gitignore`) — if you add a new
remote-mode sketch, add its `secrets.h` path there too before filling in
real values.

### Two-cell characters (ঋ, ৎ)

ঋ and ৎ can't be told apart from other letters that share their main dot
pattern by feel alone, so they're taught/tested as two cells: a short
**prefix** vibration (dot 5), then the answer cell. `data/braille_map.json`'s
`cells` field and `firmware/braille_tutor/braille_map.h`'s `BRAILLE_PREFIX[]`
are the source of truth — `0` means single-cell, matching every other letter.

---

## Tests

```bash
python3 tools/run_all_tests.py
```

| Test | Proves |
|---|---|
| `validate_braille_map.py` | 50 letters, no duplicate dot patterns |
| `test_parity.py` | JS, C and Python rule engines agree on every vector |
| `test_web_e2e.mjs` | A real browser session logs usable rows |
| `test_firmware_headers.py` | Generated headers compile and agree with the source data |
| `verify_braille_images.py` | Every stored pattern re-reads identically from its source image |

`test_web_e2e.mjs` is the one that earns its keep: it catches a session that
looks fine but logs null or NaN features — otherwise discovered weeks later
with the data already collected and the volunteers gone.

---

## Full report

`docs/PROJECT_REPORT.md` — end-to-end write-up: architecture, the 14 features
and why correctness is derivable from the streaks, measured results, hardware
design, every known limitation, and what can and cannot honestly be claimed
today. Every figure in it is checked against the source data.

---

## Layout

```
spec/engine_spec.json        ⭐ 14 features, 8 model inputs, thresholds, normalization
data/braille_map.json        ⭐ 50 letters → dot patterns + per-letter verified
dataset/real_v3.csv          1,000 real rows (P01-P04, spec_version=2)
dataset/synthetic_2k.csv     1,242 synthetic rows (fitted to real distribution)
models/metrics_final.json    test accuracy + per-class F1 for last trained model
models/golden_vectors.json   20 ESP32 boot self-test vectors
braille_img/                 reference cell images used to verify the map
data/braille_verified.zip    cropped reference images used by tools/check_*.py
tools/braille_aliases.json   filename → letter, the ONLY lookup path
assets/braille/              generated SVG + PNG + contact sheet
web/                         MVP data-collection app (rule_engine.js is GENERATED)
web/teacher.html, teacher.js remote teacher panel -- Learn/Test over Supabase
web/remote_control.html      minimal single-letter remote sender
tools/                       generators, dataset, training, parity tests
tools/gen_engine.py          ⭐ regenerates all 3 rule engines from spec
tools/train_and_export.py    ⭐ trains sklearn MLP + exports model_weights.h
tools/parity_py_js.py        Python vs JS parity check (500 vectors, 100% match)
tools/check_*.py, verify_*.py  braille pattern QA scripts (26 files)
firmware/braille_tutor/      main OFFLINE sketch (rule_engine.h, braille_map.h,
                              model_weights.h, inference.h are GENERATED/exported)
firmware/tests/              staged bring-up sketches t1..t9, plus the
                              remote-mode sketches t7_cloud_dot, t8_cloud_quiz,
                              t10_learning, t11_testing (see README.md there)
firmware/t11_ml_test/        remote learning + Serial Monitor ML vs rule-engine log
supabase/full_setup.sql      ⭐ single idempotent migration -- run this one
supabase/schema.sql          original attempts-table-only schema (superseded)
sd_card/mp3/                 audio, ready to copy to the card
```
