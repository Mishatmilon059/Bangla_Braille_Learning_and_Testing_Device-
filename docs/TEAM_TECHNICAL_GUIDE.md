# Team Technical Guide — Bangla Braille Learning & Testing Device

**Purpose of this document.** This is a complete, file-by-file walkthrough of everything in
[github.com/Mishatmilon059/Bangla_Braille_Learning_and_Testing_Device-](https://github.com/Mishatmilon059/Bangla_Braille_Learning_and_Testing_Device-),
written so any of the four of us can answer a detailed question about *any* part of the
project — including parts we didn't personally write — without having to go re-read the
code under exam pressure. Every claim below was checked against the actual file in the
repo (path and, where useful, line numbers are cited) as of the commit that added this
document. It is deliberately more cautious than the README in a few places — see
**Section 0** — because the README was written in "publication" voice for the GitHub
front page, and a professor's question deserves the exact truth, not the marketing
version.

**How to use this under viva pressure.** Each major section ends with a "Viva-Ready Q&A"
block — short, direct answers to the questions a reviewer is most likely to ask about
that part of the system. If you only have time to read one thing per section, read those.

---

## Table of Contents

- [0. Read This First — Critical Findings](#0-read-this-first--critical-findings)
- [1. Project at a Glance](#1-project-at-a-glance)
- [2. Repository Map](#2-repository-map)
- [3. The Spec Engine — Single Source of Truth](#3-the-spec-engine--single-source-of-truth)
- [4. Automated Test Suite](#4-automated-test-suite)
- [5. Braille Ground Truth — Data, Sources, and Verification](#5-braille-ground-truth--data-sources-and-verification)
- [6. The Web App — Data Collection Client](#6-the-web-app--data-collection-client)
- [7. Dataset Construction](#7-dataset-construction)
- [8. Supabase Backend — The Bridge Between Web and ESP32](#8-supabase-backend--the-bridge-between-web-and-esp32)
- [9. Firmware — Main Offline Sketch](#9-firmware--main-offline-sketch-firmwarebraille_tutor)
- [10. Firmware — ML vs Rule-Engine Comparison](#10-firmwaret11_ml_test--ml-vs-rule-engine-comparison)
- [11. Firmware — Bring-up and Remote-Mode Sketches](#11-firmwaretests--bring-up-and-remote-mode-sketches)
- [12. ML Training Pipeline](#12-ml-training-pipeline)
- [13. The `models/` Folder](#13-the-models-folder)
- [14. Audio Generation and SD Card](#14-audio-generation-and-sd-card)
- [15. Enclosure — 3D/Physical Design](#15-enclosure--3dphysical-design)
- [16. `Arduino/` — Early Prototyping](#16-arduino--early-prototyping-superseded-by-firmware)
- [17. Root Project Files](#17-root-project-files)
- [18. Master Q&A Index](#18-master-qa-index)

---

## 0. Read This First — Critical Findings

Five things surfaced while building this document that are **not** obvious from the
README, and that a careful professor is more likely to catch than to miss. Know these
cold before anyone asks a follow-up question.

### 0.1 — The main offline sketch does not run the model everyone talks about ⚠️ HIGH SEVERITY

Everywhere in this project — the README, `docs/PROJECT_REPORT.md`, the presentation
deck, this document's own Sections 9 and 12 — "the model" means the 1,734-parameter
dual-head network trained on 1,000 real + 1,242 synthetic rows (98.56%/91.37% real-only
accuracy), exported as pure C float arrays in `firmware/braille_tutor/model_weights.h`
and run by `firmware/braille_tutor/inference.h`.

**`firmware/braille_tutor/braille_tutor.ino` — the actual offline sketch meant to be
flashed onto the device — does not `#include` either of those files.** Its real includes
are:

```c
#include "model_data.h"                 // NOT model_weights.h
#include <TensorFlowLite_ESP32.h>
#include "tensorflow/lite/micro/micro_interpreter.h"
```

`model_data.h`'s own header comment says, verbatim:

```
// !! This model was trained on SYNTHETIC DATA ONLY. Its accuracy numbers
// !! are circular and say nothing about real learners. Pipeline test only.
```

So as the repository stands right now, flashing `braille_tutor.ino` deploys an **older,
synthetic-only TFLite model** — not the real-data model. The correct, current pure-C
model (`inference.h` + `model_weights.h`) exists, is verified, and *is* actually wired
into `firmware/t11_ml_test/t11_ml_test.ino` — it's just not yet wired into the sketch
that's supposed to be the real deliverable. This is almost certainly a "we built the new
path, tested it in the comparison sketch, and never went back to swap the main sketch
over" gap — a good thing to either fix before a hardware demo, or to be ready to explain
honestly if asked "what model is actually running on your device right now?"

### 0.2 — `tools/train_and_export.py` is cited everywhere but does not exist in the repo ⚠️ HIGH SEVERITY

The README's reproduction guide, `CONTRIBUTING.md`, and `firmware/tests/README.md` all
instruct a reader to run `python tools/train_and_export.py` to retrain the model. **That
file is not in the working tree and was not found anywhere in git history.** Only its
*output* survives — `firmware/braille_tutor/model_weights.h` opens with `// GENERATED by
tools/train_and_export.py -- DO NOT EDIT`. The only training script physically present,
`tools/train.py`, is a different, superseded TensorFlow/Keras pipeline that produces the
legacy `model.tflite` / `model_data.h`, not `model_weights.h` (see Section 12).

If asked to reproduce training from scratch, the honest answer is: the exact script that
produced the currently-deployed weights is missing from the repo; only the artifact and
its architecture (documented in Section 12) survive.

### 0.3 — The consonant Braille patterns trace to Wikipedia, not "World Braille Usage," despite what the README says

`README.md` states the whole 50-character map was verified against *World Braille Usage,
3rd Edition*. That's accurate for the **11 vowels** (verified from `braille_img/*.webp`
reference photos). For the **39 consonants**, `data/braille_map.json`'s own per-letter
`source` field says `"Wikipedia:Bengali_Braille"`, and the script that actually wrote
their current values (`tools/fast_verify_update.py`) used a hand-transcribed Wikipedia
table. There is at least one letter, ফ (*pha*), where `Bangla_Braille_39_Consonants_PNG/.../README.txt`
explicitly documents that World Braille Usage disagrees with Wikipedia (dots 124 vs 235)
— and the shipped map uses the Wikipedia value. See Section 5 for the full detail. This
doesn't mean the map is wrong; the Bangladesh National Braille Code identity is still
correct and self-consistent. It means: if asked "did you verify against World Braille
Usage," the precise answer is "the vowels, yes directly; the consonants were cross-checked
against Wikipedia's Bengali Braille table, with one documented case where our source
differs from World Braille Usage and we followed Wikipedia."

### 0.4 — The IEEE journal citation in the README is a placeholder, not a real publication

`README.md`'s citation block and `CITATION.cff` present this work as
`journal={IEEE Transactions on Human-Machine Systems}` with `doi={10.1109/THMS.2026.XXXXXXX}`
— a literal `XXXXXXX` placeholder. **This project has not been submitted to or accepted by
that journal.** This is standard aspirational template text some citation generators
produce, but if a professor asks "so this is published in IEEE Transactions?", the answer
is no — this is unpublished student coursework with a citation file formatted the way a
future publication *would* look, not a claim that it already happened. Never present the
DOI or journal name as real in front of an examiner.

### 0.5 — Hardware assembly status, precisely

The electronics prototype has real, on-record bench confirmation: `Arduino/README.md`
states the `Arduino/milse1/` sketch is "the build confirmed working on the bench: speaker,
all seven buttons and all six motors." That's genuine evidence of a working breadboard
build — **but it was built and tested using the early `Arduino/` prototype sketches and
their own pin assignments, which differ from the canonical `firmware/braille_tutor/pins.h`
map** used by the actual deliverable firmware. No file in the repo shows the *final*
firmware (`braille_tutor.ino`, with its canonical pin map, SD card, and RTC) running on
assembled hardware end-to-end. The 3D-printed/laser-cut enclosure (Section 15) is
verified only computationally (watertight mesh, volume checks) — nothing in the repo
shows it physically printed or fitted to the electronics. Precise honest framing: *"the
electronics have been bench-tested working with an early prototype sketch; the final
firmware and enclosure have not yet been verified together on physical hardware."*

---

## 1. Project at a Glance

| | |
|---|---|
| **Project** | Bangla Braille Learning and Testing Device |
| **Course** | EEE 416 — Microprocessor and Embedded Systems Laboratory, BUET EEE, Group 08, Section A2 |
| **Team** | Santu Nag (2106055) · Md. Adib Hasan Audhi (2106056) · Mishat Hasan Milon (2106059) · Khalid Mehebub (2106065) |
| **Microcontroller** | ESP32-WROOM-32, 240 MHz dual-core |
| **Braille standard** | Bangladesh National Braille Code, 50/50 characters currently marked verified (11 vowels + 39 consonants incl. 3 modifier marks) — see §0.3 for the precise verification-source caveat |
| **Model (correct, current)** | Two independent MLPs, `Input(8)→Dense(32,ReLU)→Dense(16,ReLU)→Dense(3,softmax)`, 1,734 params combined, 6,936 bytes, pure C float arrays, no runtime library |
| **Model (actually flashed today)** | ⚠️ See §0.1 — `braille_tutor.ino` currently links an older TFLite model trained on synthetic data only |
| **Real-only test accuracy** | Teaching action 98.56% · Confidence state 91.37% (majority baselines 46.59%/42.43%) |
| **Dataset** | 1,000 real rows (participants P01–P04) + 1,242 synthetic = 2,242 total |
| **Data collection** | Web app (`web/`), synced to Supabase, exported via `tools/export_dataset.py` |
| **Backend** | Supabase (Postgres + REST + RLS), 4 tables, plain HTTPS polling both directions — no websockets |
| **Hardware status** | Firmware written; electronics bench-tested on an early prototype sketch; enclosure design-verified only, not confirmed printed; see §0.5 |
| **Deployment** | Web app live at Vercel; ESP32 firmware not yet confirmed running end-to-end on assembled hardware |

---

## 2. Repository Map

```
.
├── spec/engine_spec.json          ⭐ single source of truth — see §3
├── data/                          Braille ground truth + verification images — see §5
├── Bangla_Braille_39_Consonants_PNG/   Raw consonant reference cards — see §5
├── braille_img/                   Raw vowel reference images — see §5
├── assets/braille/                Generated SVG/PNG cells — see §5
├── dataset/                       Real + synthetic training CSVs — see §7
├── web/                           Student practice app + teacher panel — see §6
├── supabase/, data/supabase_migrations/   Backend schema — see §8
├── firmware/
│   ├── braille_tutor/             Main offline sketch — see §9 (and §0.1!)
│   ├── t11_ml_test/                ML-vs-rule-engine comparison sketch — see §10
│   └── tests/                     16 bring-up + remote-mode sketches — see §11
├── tools/                         ~50 Python/Node scripts — generators, training, QA
├── models/                        Trained model artifacts + metrics — see §13
├── sd_card/mp3/, web/audio/       60 audio tracks — see §14
├── enclosure/                     OpenSCAD 3D case design — see §15
├── Arduino/                       Early prototyping sketches — see §16
├── docs/                          Reports, diagrams, presentation decks, this file
└── (root) LICENSE, CITATION.cff, README.md, ...   — see §17
```

Full per-file detail is in the sections below — this map is only a jump-off point.

---

## 3. The Spec Engine — Single Source of Truth

### `spec/engine_spec.json`

This file is the project's single source of truth for the 14 logged features, the rule
engine, and feature normalization. It is never executed directly — it is **transpiled**
by `tools/gen_engine.py` into three independently-running rule engines (JavaScript for
the web app, a C header for the ESP32 firmware, a Python module for synthetic-data
generation and training), so the web app and the physical hardware can never disagree
about what "REPEAT" or "GUESSING" means.

**The 14 features** (`spec/engine_spec.json:32-45`), 8 of which feed the neural network
(`model_input: true`):

| # | name | model_input | notes |
|---|---|---|---|
| 0 | char_id | no | index into `data/braille_map.json`, logged only |
| 1 | response_time | **yes** | ms, clamp 0–15000 |
| 2 | press_duration | **yes** | ms, clamp 0–2000 |
| 3 | retry_count | **yes** | count, 0–10 |
| 4 | prev_accuracy | **yes** | ratio, 0–1 |
| 5 | prev_mastery | **yes** | ratio, 0–1 |
| 6 | hint_count | **yes** | count, 0–10 |
| 7 | session_number | no | logged only |
| 8 | difficulty_level | no | dead rule input, logged only |
| 9 | time_since_last_practice | no | logged only, clamp 7 days |
| 10 | prev_confidence | no | enum 0/1/2, logged only |
| 11 | current_streak | **yes** | count, 0–20 |
| 12 | wrong_streak | **yes** | count, 0–20 |
| 13 | prev_mistakes | no | logged only |

Per `_model_input_note` in the spec, going from an earlier 4-feature model to this 8-feature
one raised confidence accuracy from 64.7% to 91.4% on the 1,000 real rows. There is
deliberately **no `is_correct` feature**: `current_streak`/`wrong_streak` are updated
*after* scoring, so exactly one is non-zero, making correctness derivable and forcing the
web app and firmware to sample features at identical moments (the `_feature_timing_contract`
in the spec).

**Teaching-action rules** (first match wins):

| rule id | condition(s) | result |
|---|---|---|
| ta_repeat_on_first_wrong | `wrong_streak >= 1 AND retry_count == 0` | REPEAT |
| ta_hint_while_stuck | `wrong_streak >= 1` | HINT |
| ta_default | (none) | NORMAL_PRACTICE |

**Confidence-state rules**:

| rule id | condition(s) | result |
|---|---|---|
| cs_guessing | `retry_count >= 2 OR response_time >= 6000` | GUESSING |
| cs_confident | `response_time <= 2500 AND retry_count == 0 AND wrong_streak == 0 AND press_duration <= 400` | CONFIDENT |
| cs_default | (none) | HESITANT |

**Normalization** is min-max with clamping, applied only to the 8 model-input features.
Ranges are **fixed in the spec, not derived from the live dataset** — specifically so
that retraining on a growing dataset can never shift what the ESP32 computes for a given
raw value out from under model weights that have already been flashed.

**Mastery update**: exponential moving average, `alpha_correct=0.25`, `alpha_wrong=0.35`,
`initial=0.0` — correct: `m + 0.25*(1-m)`, wrong: `m - 0.35*m`.

### `tools/gen_engine.py` — the transpiler

Reads `spec/engine_spec.json` and writes three files: `web/rule_engine.js`,
`firmware/braille_tutor/rule_engine.h`, `tools/rule_engine_gen.py`. It works by **string
templating**, not AST generation or a real compiler: `gen_js`/`gen_h`/`gen_py` each build
one shared, language-agnostic rule chain and render it with a per-language accessor
(`f.name` in JS, `f->name` in C, `f['name']` in Python).

The same rule (`ta_repeat_on_first_wrong`), three outputs:

```js
// web/rule_engine.js
if (f.wrong_streak >= 1.0 && f.retry_count == 0.0) return TEACHING_ACTION.REPEAT;
```
```c
// firmware/braille_tutor/rule_engine.h
if (f->wrong_streak >= 1.0 && f->retry_count == 0.0) return TA_REPEAT;
```
```python
# tools/rule_engine_gen.py
if f['wrong_streak'] >= 1.0 and f['retry_count'] == 0.0: return TeachingAction.REPEAT
```

| Generated file | Language | Regenerate with |
|---|---|---|
| `web/rule_engine.js` | ES module | `python tools/gen_engine.py` |
| `firmware/braille_tutor/rule_engine.h` | C (uses `double`, deliberately, to match Python/JS arithmetic exactly) | `python tools/gen_engine.py` |
| `tools/rule_engine_gen.py` | Python (`IntEnum`s) | `python tools/gen_engine.py` |

---

## 4. Automated Test Suite

| Script | What it checks | How to run it | Pass criteria |
|---|---|---|---|
| `validate_braille_map.py` | `data/braille_map.json`: counts, id contiguity, dot validity, duplicate patterns, audio filenames | `python tools/validate_braille_map.py` | `OK - all checks passed` |
| `test_parity.py` | JS vs C vs Python: both labels + all 8 normalized model-input values, across N sampled vectors | `python tools/test_parity.py [N]` | `OK - JS, C and Python rule engines agree on every vector` |
| `test_firmware_headers.py` | Generated headers compile as C++17 **and** their content agrees with the source JSON/spec | `python tools/test_firmware_headers.py` | 21 checks, 0 failures |
| `test_web_e2e.mjs` | Real Playwright browser session against `web/` | `node tools/test_web_e2e.mjs` | 25–28 checks (see below), 0 failures |
| `test_supabase.py` | Live Supabase backend: reachability, schema, RLS, dedupe, key hygiene | `python tools/test_supabase.py [--write]` | 0 failures |
| `run_all_tests.py` | Master runner — invokes all of the above except `test_supabase.py` (needs live network) | `python tools/run_all_tests.py [--skip-web]` | all invoked suites PASS |

**`test_parity.py`'s vector count — the exact truth.** The bare script's own default is
**2,000** (`test_parity.py:115`). `run_all_tests.py` explicitly calls it with `3000`, which
is what `docs/PROJECT_REPORT.md` describes ("pushes 3,000 feature vectors") — correct for
the master-suite run specifically. The README's `python tools/test_parity.py 1000` is
just an illustrative example argument, not a claim about any default. All three numbers
are true simultaneously; they describe different invocations, not a contradiction.

The comparison covers `teaching_action`, `confidence_state`, and every one of the 8
normalized model-input values, tolerance `1e-6`, compiling a C harness on the fly and
running the JS/Python engines alongside it. Roughly a quarter of sampled vectors are
placed deliberately on or beside a decision threshold ("thresholds are where drift
hides" — comment in the script), another 10% deliberately out of range to exercise
clamping.

`test_web_e2e.mjs` drives a headless Chromium session, simulates a real 12-attempt
practice session with human-like randomized timing, then asserts on the resulting rows:
no JS errors, all 14 logged features present and finite, streak-exclusivity, correctness
derivability, plausible timing ranges, correct provenance stamps, a valid CSV export, and
an offline-resilience branch when the backend is unreachable — 25 unconditional checks +
up to 3 conditional ones = up to 28 total, matching `docs/PROJECT_REPORT.md`'s "28 checks."

`test_firmware_headers.py` compiles `rule_engine.h` + `braille_map.h` + `model_data.h`
together as C++17, runs the compiled probe, and cross-checks its printed output against
`spec/engine_spec.json` and `data/braille_map.json` bit-for-bit — 21 `check()` calls
total.

`test_supabase.py` runs primarily with the **publishable/anon key** (the same one the
browser uses) to prove reachability, table existence, and that RLS actually lets `anon`
insert+select; `--write` additionally needs the **secret key**, only to delete its own
test row afterward (there is no delete policy granted to `anon`).

### Viva-ready Q&A

- **Q: Why is there no `is_correct` feature?** Because `current_streak`/`wrong_streak` are
  mutually exclusive after scoring, so correctness is already implied.
- **Q: What proves the web app and firmware never disagree on a rule?** `test_parity.py`
  compiles/runs all three generated engines over the same vectors and diffs both labels
  plus every normalized feature to `1e-6`.
- **Q: Does `test_parity.py` really test 3,000 vectors?** Only via `run_all_tests.py`,
  which passes `3000` explicitly; the bare script's own default is 2,000.
- **Q: Why isn't `test_supabase.py` part of the standard CI run?** It needs live network
  access to `supabase.co`, which the build environment's own egress policy blocked — it's
  deliberately run by hand, separately.

---

## 5. Braille Ground Truth — Data, Sources, and Verification

### `data/braille_map.json` structure

The canonical 50-character map. Each letter entry has: `id` (0–49), `char` (Bangla
glyph), `name` (canonical id used everywhere), `roman`, `category` (vowel/consonant),
`dots` (the answer cell's raised dot numbers), `cells` (only for the two two-cell
characters — `[prefix_cell, answer_cell]`), `audio` (DFPlayer track filename), `verified`
(bool), and `source` (provenance string). Reading the file directly confirms all 50
entries carry `"verified": true` and the top-level `"verified_count": 50`.

### Where the reference images actually came from

- **`braille_img/*.webp`** — 11 vowel reference photos. Filenames do **not** match vowel
  names literally — `tools/braille_aliases.json` is the authoritative lookup, because the
  supplier's `uu.webp` is উ (called `"u"` here) while `uuuu.webp` is ঊ (called `"uu"`
  here). A naive filename match would silently swap two valid-looking but wrong patterns.
- **`Bangla_Braille_39_Consonants_PNG/Bangla_Braille_39_PNG/*.png`** — 39 consonant
  reference cards. Their own `README.txt` genuinely does cite *World Braille Usage, 3rd
  Edition* (specific pages, 9–10) — that part of the top-level README's claim is
  accurate for this source material. It also documents one explicit conflict: ফ (*pha*)
  is dots 235 per Wikipedia but dots 124 per World Braille Usage.
- **`data/braille_verified/*.png`** — these are **not** crops of any photograph. They are
  synthetically drawn (the same dot-circle renderer `gen_braille_images.py` uses) directly
  from a hardcoded dictionary in `tools/fast_verify_update.py`, visualizing "what the map
  currently says" — a self-consistency render, not independent photographic evidence.

**The actual provenance, reconciled.** `data/braille_map.json`'s own `_notes` say only the
11 vowels were verified from `braille_img/`; the 39 consonants were verified against
**Wikipedia's Bengali Braille table**, and each consonant's `source` field says exactly
that. The script that set all 50 letters' current values, `tools/fast_verify_update.py`,
used a hardcoded Wikipedia-derived dictionary — and for ফ specifically, it set dots
`[2,3,5]`, the Wikipedia value, on the very letter the PNG package's own README flags as
disagreeing with World Braille Usage. See §0.3 for how to phrase this precisely if asked.

### The verification algorithm (`tools/braille_image_reader.py`)

Used for the 11 vowel images:

1. Composite the source image onto white (it carries alpha).
2. Threshold to an ink mask, confirm the ink bounding box looks like one 2×3 cell.
3. Find 3 row-bands and 2 column-bands by **projection profile** (rows/columns containing
   any ink), take each band's midpoint — not a naive uniform-sixths split, which the
   script's own docstring says shrinks the confidence margin from ~120 grey levels to
   ~7 because circles don't sit at exact sixths.
4. Sample a small disc at each of the 6 band intersections: a **raised** dot reads as a
   solid dark disc (dark center), an **unraised** dot as a hollow ring (light center).
   Center-sampling rather than whole-slot ink coverage is the key trick.

### The import/QA tool family

`tools/import_braille_images.py` is dry-run by default (`--write` to apply), refuses to
resolve any filename absent from `braille_aliases.json`, and blocks on a hard collision
between two already-verified letters while tolerating a soft collision against an
unverified placeholder. `tools/verify_braille_images.py` renders a contact sheet
(`assets/braille/_verification_sheet.png`) for a human to eyeball. Roughly 26 smaller
scripts round out the pipeline:

| Tool group | Scripts | Purpose |
|---|---|---|
| Grid/crop-finding | `crop_letters.py`, `crop_exact.py`, `extract_all_targets.py`, `extract_clean_crops.py`, `find_grid.py`, `split_subrows.py`, `dump_crops.py`, `analyze_wiki_table.py` | Locate/crop individual letter cells out of pasted Wikipedia table screenshots during manual transcription |
| Dot-reading on crops | `check_1_to_3.py`, `check_4_to_7.py`, `check_1_to_7_detailed.py`, `check_targets_1_to_7.py`, `check_target_details.py`, `check_rri.py`, `parse_1_to_7.py`, `analyze_all_10.py`, `analyze_cells.py`, `visualize_dots.py`, `dump_ascii.py`, `check_images.py` | Ad hoc scripts reading dot patterns off specific crops while manually building the Wikipedia dictionary |
| Wikipedia cross-check | `check_all_against_wiki.py`, `verify_wiki.py` | Compare `braille_map.json` against the hardcoded Wikipedia dict for spot-checked letters |
| Field/flag auditing | `audit_verified.py`, `check_verified_dots.py`, `check_verified_field.py` | Diff `data/braille_verified/*.png` against `braille_map.json`, or just report flag counts |
| Misc | `inspect_style.py`, `fast_verify_update.py`, `svgkit.py` | `fast_verify_update.py` is the actual bulk overwrite script; the other two are minor helpers |

### Generated assets

`tools/gen_braille_header.py` reads `data/braille_map.json` and writes
`firmware/braille_tutor/braille_map.h`: parallel arrays `BRAILLE_VERIFIED[]`,
`BRAILLE_PATTERN[]` (6-bit dot mask), `BRAILLE_PREFIX[]` (non-zero only for the two
two-cell characters), `BRAILLE_NAME[]`, `BRAILLE_ROMAN[]`, plus a `braille_track(id)`
helper mapping id → mp3 filename. `tools/gen_braille_images.py` writes, per letter, an
SVG and PNG, plus a contact sheet and `assets/braille/index.json` (a flat enumerable list
of `{id, char, name, dots, svg, png}`).

### The ঋ/র and ৎ/ত two-cell disambiguation

ঋ's answer cell `[1,2,3,5]` is bit-for-bit identical to র's single cell; ৎ's answer cell
`[2,3,4,5]` collides with ত's. This is not a data bug — it's how the Bangladesh Braille
standard itself encodes these characters. The firmware plays the letter's audio, and if
`BRAILLE_PREFIX[id]` is non-zero, vibrates that prefix pattern (dot 5) for 350 ms, pauses
600 ms, then opens the answer window and scores **only** against `BRAILLE_PATTERN[id]`
(the answer cell). Audio + timing context resolve what the dot pattern alone cannot.

### Viva-ready Q&A

- **Q: How many characters are verified, and how do you know?** All 50 — confirmed by
  reading `data/braille_map.json` directly (`"verified_count": 50`, every letter
  `"verified": true`), not by trusting a summary claim.
- **Q: What were the two ground-truth sources?** 11 vowels from photographed reference
  cells (automated dot-reading algorithm); 39 consonants from a manually transcribed
  Wikipedia table.
- **Q: Does the project really verify against World Braille Usage 3rd Edition?** The
  vowel reference package and the consonant PNG package's own README both cite it, but
  the consonant *values actually shipped* trace to Wikipedia per `braille_map.json`'s own
  provenance fields — with one documented disagreement (ফ) where the two sources differ
  and Wikipedia's value was kept.
- **Q: How does the algorithm tell a raised dot from a flat one?** Projection-profile band
  detection finds the 6 dot centers, then a small disc is sampled at each center — solid
  dark = raised, hollow light = unraised.
- **Q: How is ঋ told apart from র on the device, given they share a dot pattern?** A
  350 ms prefix vibration on dot 5, a 600 ms pause, then the shared answer cell — matching
  the real Braille standard's own encoding, not an engineering workaround.

---

## 6. The Web App — Data Collection Client

### Page structure (`web/index.html`)

Four regions: a **profile overlay** (name + participant ID, localStorage-persisted, no
login system), a **setup panel** (mode: normal/targeted/review, character set, attempts
per session), a **practice panel** (prompt display, 6-dot visual cell, 6-button keypad,
hint/submit/clear/stop), and **stats panels** (per-character mastery table, class-balance
table — both collapsible and hidden by default).

### `web/app.js` — core client logic

- **`boot()`** — gates on the profile existing; loads `data/braille_map.json` (with a
  hardcoded fallback if the fetch fails); constructs the cell/keypad/logger; probes
  Supabase connectivity; wires events.
- **`pickLetter()`** — selection algorithm per mode:

  | Mode | Algorithm |
  |---|---|
  | (any, after REPEAT/HINT) | Re-show the same letter |
  | `review` | Uniform random among seen chars with mastery < 0.5 |
  | `targeted` | Score every char: `weakness*2 + staleness*2 + wrongPressure*3 + random*0.5`; pick uniformly among the top 5 |
  | `normal` | Inverse-mastery-weighted random draw: `weight = 0.15 + (1 - mastery)` |

- **`submit()`** — the critical function. Reads the entered dot mask, computes
  correctness, samples `prev_accuracy`/`prev_mastery`/`prev_mistakes`/`prev_confidence`/
  `time_since_last_practice` **before** updating learner state, measures `response_time`
  as `now - promptEnd` where `promptEnd` is stamped only when the prompt audio's `ended`
  event fires (**not** on first key press — matching the firmware exactly), then updates
  learner state and reads `current_streak`/`wrong_streak` **after** the update. Calls the
  generated `evaluateTeachingAction()`/`evaluateConfidence()` to label the row, then logs
  it with all 14 fields + labels + provenance to `AttemptLogger`.
- There is no separate `is_correct` model feature — it's stored for audit purposes only;
  correctness for the model is carried by the mutually-exclusive streak fields.

### `web/storage.js` — persistence and offline queueing

`LearnerState` tracks per-character mastery/streaks/history in localStorage.
`AttemptLogger.log()` **always writes to localStorage first**, then queues and calls
`flush()`. `flush()` POSTs up to 100 rows at once with `Prefer:
resolution=ignore-duplicates`; on success or HTTP 409 (the DB's dedupe index rejecting a
replay) the sent rows are removed from the queue; on network failure it schedules a retry
in 30s and also listens for the browser's `online` event — rows are queued and retried,
never silently dropped.

### `web/config.js` — Supabase client config and key security model

Holds `SUPABASE_URL` and `SUPABASE_ANON_KEY` (the **publishable** key). Safe to ship to
every browser because Postgres Row Level Security restricts what that key can do — insert
and select only, no update or delete (see §8). The secret/`service_role` key must never
appear here; it lives only in the gitignored `.env`.

### Generated vs hand-written files in `web/`

| File | Generated? | Source |
|---|---|---|
| `web/rule_engine.js` | **Yes** | `tools/gen_engine.py` + `spec/engine_spec.json` |
| everything else in `web/` | No | hand-written |

### Teacher panel (`web/teacher.html`, `web/teacher.js`, `web/remote_control.html`)

Two tabs: শেখানো/Learn and পরীক্ষা/Test. Polls the `attempts` table every **200 ms**
(`setInterval(pollAttempts, 200)`), and posts to `remote_commands` when the teacher picks
a letter. See §8 for the full bidirectional flow. `remote_control.html` is a standalone
single-letter trigger page with its own inline Supabase call.

### Viva-ready Q&A

- **Q: Why does the response-time clock start at prompt-audio-end, not first key press?**
  To match the ESP32 exactly, so browser-collected and device-collected rows stay on the
  same timing scale.
- **Q: What happens if the network drops mid-session?** Nothing is lost — rows are
  written to localStorage immediately, queued, and retried with backoff; a 409 (already
  delivered) is treated as success, not an error.
- **Q: Is it safe that the Supabase key is committed to the repo?** Yes — it's the
  publishable key, restricted by RLS to insert+select only on `attempts`.

---

## 7. Dataset Construction

### CSV file relationships

| File | Rows | Role | Used by the final model? |
|---|---|---|---|
| `dataset/real.csv` | 1,000 | Full merged real-participant export (P01–P04) | **Yes** |
| `dataset/real_v3.csv` | 1,000 | Byte-identical to `real.csv` | Duplicate |
| `dataset/real_v2.csv` | 923 | Earlier partial export (P01–P03 only, missing P04 and earlier dates) | No — superseded |
| `dataset/synthetic.csv` | 1,200 | 13 simulated learners | No — this is the CLI default, not what was actually used |
| `dataset/synthetic_2k.csv` | 1,242 | Calibrated to real distributions | **Yes** |
| `dataset/synthetic_targeted.csv` | 1,836 | Rare-class-targeted samples | Used in an earlier, superseded experiment only |

Confirmed by cross-referencing `models/metrics_final.json`'s `dataset: {real: 1000,
synthetic: 1242, total: 2242}` — an exact match to `real.csv` (1,000) + `synthetic_2k.csv`
(1,242), and to the README's "2,242 Trials" badge.

### `tools/export_dataset.py`

Pulls all rows from Supabase's `attempts` table via paginated REST `GET` (1,000 rows at a
time). Resolves credentials from env → `.env` → `web/config.js`, and works fine with just
the publishable/anon key since RLS already permits `select`. Runs pre-training sanity
checks: class population ≥30/bucket, streak-mutual-exclusion invariant,
`current_streak>0 == is_correct` invariant, unverified-map row counts, multi-day spread.

### `tools/gen_synthetic.py` — simulation, not independent sampling

Runs virtual learners through the **same state machine** the web app uses, rather than
sampling each of the 14 features independently — independent sampling can produce
physically impossible combinations (e.g. `current_streak=7` beside `prev_mastery=0.02`).
Fits log-normal response-time/press-duration parameters from real rows when at least 8
samples per bucket exist; otherwise falls back to hardcoded, explicitly-labeled-as-guesses
priors. This is why real data collection must happen **before** synthetic generation.

### Viva-ready Q&A

- **Q: Which dataset files are actually "the" training data right now?** `real.csv`
  (1,000 rows) + `synthetic_2k.csv` (1,242 rows) — confirmed by matching
  `metrics_final.json`'s exact row counts, even though `train.py`'s own CLI defaults
  point at different files.
- **Q: Why simulate learners instead of sampling features independently for synthetic
  data?** Independent sampling produces impossible feature combinations that waste model
  capacity on a region of input space that can never actually occur.

---

## 8. Supabase Backend — The Bridge Between Web and ESP32

**This is the most likely "explain the whole system" question a reviewer will ask — know
this section cold.**

### The four tables

| Table | Written by | Read by | Purpose |
|---|---|---|---|
| `attempts` | Web app (student practice), ESP32 (remote-mode sketches) | Teacher panel, `tools/export_dataset.py` | The main data-collection table — one row per practice attempt, 14 features + labels + provenance |
| `remote_commands` | Teacher panel | ESP32 (remote-mode sketches) | "Play letter N" / "run test index M of N" commands from teacher to device |
| `student_weaknesses` | Teacher panel logic | Teacher panel | Per-student, per-character wrong/correct tally, built up from test results |
| `test_sessions` | Teacher panel | Teacher panel | One full result record per completed test batch |

All four tables have **Row Level Security enabled**, with a policy granting the `anon`
role (which is what the publishable key maps to) insert + select — and for
`student_weaknesses`/`test_sessions`, full read-write since the teacher panel itself
needs to update tallies. **`attempts` has no update/delete policy at all — it is
append-only by design.** A unique index on `(session_id, attempt_index)` (excluding
synthetic rows) makes a replayed POST a safe no-op instead of a duplicate.

Migration files, in the order they were written: `supabase/schema.sql` (original,
`attempts` + a simpler `remote_commands`) → `data/supabase_migrations/001_teacher_tables.sql`
(added the 3 teacher-panel tables as an incremental migration) → `supabase/full_setup.sql`
(the current, idempotent, run-this-one file combining everything plus 4 monitoring
views). **Always apply `supabase/full_setup.sql`** — it's safe to re-run even if the
older files were already applied.

### The two independent polling loops — this is the actual "flow"

There is **no websocket, no Supabase Realtime subscription, no push notification
anywhere in this system.** Both directions work by one side writing a row and the other
side asking "anything new?" on a fixed timer, over plain HTTPS REST calls to Supabase's
auto-generated API. This is deliberate: an ESP32 can hold a REST `WiFiClientSecure`
connection open and poll cheaply; a websocket/Realtime channel would be meaningfully more
firmware complexity for no benefit at this data rate.

```
DIRECTION 1 — Student practices on the web app, teacher watches live
═══════════════════════════════════════════════════════════════════

  [Student, web/index.html]
         │  submit() scores the attempt, builds a 14-feature row
         ▼
  AttemptLogger.log()  →  localStorage (always, first)
         │  flush()
         ▼
  POST https://<project>.supabase.co/rest/v1/attempts
         (Authorization: Bearer <anon key>, apikey: <anon key>)
         ▼
  ┌─────────────────────────────┐
  │   Supabase  attempts  table  │   RLS: anon may INSERT + SELECT
  └───────────────┬─────────────┘
                   │  polled every 200 ms
                   ▼
  [Teacher, web/teacher.js → pollAttempts()]
         GET .../rest/v1/attempts?...&order=id.desc&limit=1
         renders the live result on the teacher dashboard


DIRECTION 2 — Teacher sends a command, ESP32 executes it, reports back
════════════════════════════════════════════════════════════════════

  [Teacher, web/teacher.js]
         │  picks a letter / starts a test batch
         ▼
  POST .../rest/v1/remote_commands
         { device_id, letter_id, command: "play" | "test",
           test_index, test_total }
         ▼
  ┌───────────────────────────────┐
  │  Supabase  remote_commands     │   RLS: anon may INSERT + SELECT
  └───────────────┬────────────────┘
                   │  polled every 250 ms
                   ▼
  [ESP32, firmware/tests/t10_learning.ino or t11_testing.ino or
          firmware/t11_ml_test/t11_ml_test.ino]
         GET .../rest/v1/remote_commands
             ?device_id=eq.esp32_01&id=gt.<last_seen_id>&order=id.asc
         (ESP32 remembers the last-handled row id in RAM only —
          no ack column, no update/delete needed on this table either)
         │
         ▼
  Plays the letter's audio (+ vibration cue in Learn mode),
  waits for the 6 dot buttons + submit, scores the attempt
  locally against BRAILLE_PATTERN[letter_id]
         │
         ▼
  POST .../rest/v1/attempts   (device reports its own result)
         { source: "esp32", teaching_action, confidence_state, ... }
         ▼
  ┌─────────────────────────────┐
  │   Supabase  attempts  table  │
  └───────────────┬─────────────┘
                   │  polled every 200 ms (same loop as Direction 1)
                   ▼
  [Teacher, web/teacher.js]  sees the ESP32's result live,
       sends the next command when ready
```

### Why polling, not push — and what could go wrong

- **No persistent connection to babysit.** A `WiFiClientSecure` is reused across polls on
  the ESP32 side (`firmware/t11_ml_test/t11_ml_test.ino`, `https_client()`) specifically
  to avoid paying a fresh TLS handshake (0.5–3 s) every 250 ms — but if that connection
  ever drops, the very next poll just opens a new one; there's no session state to
  recover, which is the main robustness benefit of polling over a persistent
  websocket/Realtime channel for this use case.
- **`device_id` is how multiple boards would be told apart** (`"esp32_01"` is the only
  one configured) — if two ESP32s ran the same firmware simultaneously, they'd both
  execute every command meant for `esp32_01`. The project's own docs explicitly warn:
  flash only **one** remote-mode sketch on **one** device at a time.
- **Polling interval sets the worst-case latency**, not the typical case: up to 250 ms
  before the ESP32 notices a new command, up to 200 ms before the teacher panel notices a
  new result — both fast enough to feel "live" to a human, and both cheap enough that
  Supabase's free tier handles it without issue at this scale.
- **Security model**: every call from both the web app and the ESP32 uses the same
  publishable/anon key. That key can only insert and select — it cannot update or delete
  anything, and it cannot bypass RLS. The tradeoff, stated plainly in `supabase/schema.sql`'s
  own comment: anyone holding this key (and it does ship inside the client, it is not
  secret) can read every row in these tables — acceptable here because rows contain only
  anonymous participant codes and timing numbers, never names.

### Viva-ready Q&A

- **Q: How does the ESP32 know a teacher picked a new letter?** It polls
  `GET /rest/v1/remote_commands?device_id=eq.esp32_01&id=gt.<last_seen>` every 250 ms and
  remembers the last id it handled in RAM.
- **Q: How does the teacher's screen update when the ESP32 answers?** The teacher panel
  polls `GET /rest/v1/attempts` every 200 ms and re-renders whenever a new row appears.
- **Q: Is there a live/websocket connection between the browser and the ESP32?** No —
  they never talk to each other directly. Everything relays through two Supabase tables,
  and both sides only ever poll, never subscribe.
- **Q: What stops a duplicate row if a POST is retried after a timeout?** A unique index
  on `(session_id, attempt_index)` on `attempts` — a retried POST gets HTTP 409, which
  both the web client and firmware treat as "already delivered," not an error.
- **Q: What would happen if two ESP32 boards were flashed with the same remote-mode
  sketch at once?** Both would execute every command targeting `device_id: "esp32_01"`,
  since neither the schema nor the firmware disambiguates further — this is why the
  project's docs insist on flashing only one remote-mode sketch on one board at a time.
- **Q: Why doesn't the offline `braille_tutor.ino` touch Supabase at all?** By design —
  it's meant to run with zero network dependency in classrooms without internet. WiFi and
  Bluetooth are explicitly disabled in its `setup()`. Only the separate remote-mode
  sketches (`t10_learning`, `t11_testing`, `t11_ml_test`) use WiFi/Supabase at all.

---

## 9. Firmware — Main Offline Sketch (`firmware/braille_tutor/`)

> ⚠️ Read §0.1 before this section — the model this sketch actually links is not the one
> described in §12/§13.

### Complete pin table (`pins.h`)

| Function | GPIO | Notes |
|---|---|---|
| Dot button 1–6 | 32, 33, 25, 26, 27, 14 | `INPUT_PULLUP`, active LOW |
| Submit button | 12 | Boot-strapping pin — must read LOW at boot; a plain switch to GND can only pull it LOW or leave it at its own default LOW, never force it HIGH, so it's safe |
| Motor (dot) 1–6 | 21, 13, 22, 2, 15, 4 | Via ULN2803A, active HIGH; **GPIO 2 and 15 need 10 kΩ pulldowns** (also strapping pins, sampled at boot) |
| DFPlayer RX / TX | 16 / 17 | UART2; 1 kΩ series resistor on TX (3.3 V logic into a 5 V-fed module) |
| microSD (VSPI) | CLK 18, MISO 19, MOSI 23, CS 5 | |
| RTC (optional DS3231) | SDA/SCL declared but unwired | `USE_RTC 0` — see below |

GPIO 12 is deliberately never GPIO 0 (the board's own BOOT button) — reusing GPIO 0 risks
accidentally forcing flash mode at reset.

**Power**: 6 motors (~480 mA peak) + ESP32 (~80 mA, WiFi off) + DFPlayer (~200 mA) ≈
800 mA peak → needs a 5 V/2 A supply and a 1000 µF capacitor across the motor rail, or
motor inrush browns out the regulator and reboots the board mid-session — which looks
exactly like a firmware crash and is not one.

### `hardware.h` — peripheral abstractions

- `buttons_begin()` / `buttons_poll()` — per-pin 20 ms debounce, builds the pressed-dot
  mask and press order.
- `buttons_mean_press_duration()` — feeds the `press_duration` feature.
- `submit_begin()` / `submit_poll()` — separate debounced state machine for the submit
  button.
- `motors_show_pattern()` / `motors_show_sequential()` / `motors_buzz_all()` — different
  vibration feedback styles (all-at-once for a hint, one-at-a-time for teaching, all-six
  for a correct answer).
- `audio_play_blocking()` — **blocking** on purpose, so the response-time clock starts
  exactly when the clip finishes, matching the web app's `ended` event timing.
- `sd_begin()` / `sd_append()` — mounts SD, appends one CSV row per attempt, closing the
  file each time so a power loss costs at most one row.

### `braille_tutor.ino` — control flow

**setup()**: Serial at 115200 → WiFi and Bluetooth explicitly turned off
(`WiFi.mode(WIFI_OFF); btStop();` — confirms this sketch really is fully offline) →
buttons/motors/SD initialized → learner state loaded from `/state.bin` → clock
initialized (RTC or assumed-epoch fallback) → audio initialized → **model loaded and
self-tested against compiled-in golden vectors; any mismatch disables the model and
falls back to the rule engine** → boot audio plays.

**loop()**: picks the next letter (repeats after REPEAT/HINT, otherwise inverse-mastery
weighted, mirroring the web app's `pickLetter()`) → runs up to 4 attempts per prompt
while the decision keeps being REPEAT/HINT → saves state after every prompt (not just at
session end) → ends after 20 attempts.

**One attempt (`run_attempt()`)**: play letter audio (blocking) → if two-cell, buzz the
prefix and pause → start the response-time clock at prompt-end → poll buttons/submit for
up to 15 s → read pre-attempt history **before** scoring → score (model or rule-engine
fallback) → play feedback audio/motors → log the row to SD.

### `inference.h` — the correct, current forward pass (linked by `t11_ml_test`, not yet by this sketch)

```c
static inline void ml_infer(const Features *f, int *out_ta, int *out_cs) {
    float norm[ML_FEATURE_COUNT];
    normalize_features(f, norm);
    float h0[ML_HIDDEN1], h1[ML_HIDDEN2], logits[ML_OUTPUT];
    _ml_dense_relu(ML_TA_W0, ML_TA_B0, norm, ML_FEATURE_COUNT, h0, ML_HIDDEN1);
    _ml_dense_relu(ML_TA_W1, ML_TA_B1, h0,   ML_HIDDEN1,       h1, ML_HIDDEN2);
    _ml_dense     (ML_TA_W2, ML_TA_B2, h1,   ML_HIDDEN2, logits, ML_OUTPUT);
    *out_ta = _ml_argmax(logits, ML_OUTPUT);
    // ... identical 3-layer pass again with ML_CS_* weights for confidence
}
```

Two independent 3-layer MLPs sharing one normalized 8-feature input. `model_weights.h`
carries 12 arrays (`ML_TA_*`/`ML_CS_*` × W0/B0/W1/B1/W2/B2); counting elements gives
8·32+32 + 32·16+16 + 16·3+3 = **867 per head × 2 = 1,734**, matching every other citation
of this number in the project. No library, no arena, no quantization — pure `float` C,
~917 multiply-adds total, ~0.1 ms claimed at 240 MHz.

### `rule_engine.h` / `braille_map.h` (both generated — see §3 and §5)

### `learner_state.h`

Per-character on-device state persisted to `/state.bin` (magic `"BRL1"`). Tracks
seen/correct/mistakes/streak/wrong_streak/mastery/last_practice/last_confidence for all
50 characters. `apply_outcome()` updates it after scoring — the same ordering contract as
the web app (`app.js`'s `submit()`): read history first, then update.

### `platformio.ini`

`board = esp32dev`, `framework = arduino`. `lib_deps` explicitly includes
`tanakamasayuki/TensorFlowLite_ESP32 @ ^1.0.0` and `dfrobot/DFRobotDFPlayerMini @ ^1.0.6`
— confirming the TFLite dependency in §0.1 is real and currently required for this sketch
to build as written.

---

## 10. `firmware/t11_ml_test/` — ML vs Rule-Engine Comparison

This folder's `pins.h`, `braille_map.h`, `rule_engine.h`, `inference.h`, `model_weights.h`
are content-identical to `braille_tutor/`'s copies. `t11_ml_test.ino` is built on the
`t10_learning` flow (WiFi + Supabase, retry-until-correct teaching) and adds a local ML
pass after every attempt:

- **`log_ml_comparison()`** — builds a `Features` struct from in-RAM per-character state,
  runs **both** `evaluate_teaching_action()`/`evaluate_confidence()` (rule engine) and
  `ml_infer()` (the correct pure-C network) on the same vector, and prints a side-by-side
  `MATCH`/`MISMATCH` block to Serial Monitor.
- **`report_attempt()`** — POSTs to Supabase's `attempts` table using the **ML model's**
  decision as the authoritative `teaching_action`/`confidence_state`, not the rule
  engine's — matching the *intended* design of `braille_tutor.ino` (prefer the model when
  available), even though that sketch's currently-linked model is the older TFLite one
  (§0.1).
- Requires WiFi and a `secrets.h` (gitignored) — it is **not** an offline sketch.

**This is the one file in the whole repo where the correct, real-data-trained model is
actually running.** If a professor asks to see the good model in action, this is the
sketch to point to.

---

## 11. `firmware/tests/` — Bring-up and Remote-Mode Sketches

### Recommended bring-up order

1 → 2 → 3 → 3b → 4 → 5 → 6, **one peripheral at a time** — flashing the full
`braille_tutor.ino` directly wires six buttons, six motors, a DFPlayer, an SD card, and a
neural network simultaneously, so a single wiring mistake produces one symptom and
eighteen possible causes. Only after 1–6 pass should the main sketch be flashed. The
remote/cloud sketches (t7–t11, `t11_ml_test`) are an explicitly separate, parallel track
— WiFi is deliberately absent from the main offline tutor.

### Sketch-by-sketch

| Sketch | Tests | Key pins/peripherals |
|---|---|---|
| `t1_blink_serial` | Board alive, Serial at 115200 | UART only |
| `t2_buttons` | All 6 dot buttons, debounce, timing | `32,33,25,26,27,14`, `INPUT_PULLUP` |
| `t3_motors` | ULN2803A fires each motor in sequence, then together | `21,13,22,2,15,4` |
| `t3b_braille_patterns` | Types a letter id/name in Serial, feels the real pattern from `braille_map.h` | Same motor pins as t3 |
| `t4_dfplayer` | Audio playback by track number | RX 16 / TX 17 |
| `t5_sd` | SD mount, CSV append + read-back | VSPI 18/19/23/5 |
| `t6_model` | *Legacy, superseded* — TFLite inference vs desktop golden vectors | needs `model_data.h` |
| `t7_cloud_dot` | Earliest WiFi+Supabase bring-up — polls `remote_commands`, buzzes one dot/letter | Motors + WiFi |
| `t7_model_live` | TFLite model scoring live vs rule engine (predecessor to `t11_ml_test`) | DFPlayer, `model_data.h` |
| `t8_cloud_quiz` | Full quiz prototype; superseded by `t11_testing` | Full board + WiFi |
| `t9_dfplayer_test` | Pure audio diagnostic, no motors/buttons | RX 16 / TX 17 |
| `t9b_dfplayer_diagnostic` | Step-by-step DFPlayer fault diagnosis, decodes library error codes | Same UART pins |
| `t10_learning` | Remote Learn mode (see below) | Full board + WiFi |
| `t11_testing` | Remote Test mode (see below) | Full board minus vibration cues + WiFi |
| `t_motor_test` | Isolates GPIO-vs-ULN2803A motor faults | Motor pins |
| `t_sync_test` | Confirms button N buzzes motor N (physical wiring sanity check) | Both pin arrays |

### `t10_learning` vs `t11_testing`

Both share the canonical pin map, poll `remote_commands` every 250 ms over a reused TLS
connection, and POST scored rows to `attempts`.

- **`t10_learning` (শেখানো/Learn)**: plays audio, vibrates the full dot pattern as a
  teaching cue, **retries indefinitely** on a wrong answer, reports every attempt
  including retries.
- **`t11_testing` (পরীক্ষা/Test)**: audio only, **no vibration cue at all** — the student
  must recall the pattern from memory — exactly **one** attempt, no retry, and prints a
  full pass/fail Serial summary after the last item in the teacher's batch.
- **Neither uses the ML model.** Both compute placeholder zero values for the unused
  logged fields and derive the label with a simple inline `correct ? ... : ...`
  expression — only `t11_ml_test` (§10) actually calls `ml_infer()`.

### Viva-ready Q&A

- **Q: What happens if the ML model and rule engine disagree?** `braille_tutor.ino` never
  runs both at once — it uses the model if it passed its boot self-test, otherwise the
  rule engine, never comparing them live. `t11_ml_test.ino` is the only sketch that runs
  both and reports MATCH/MISMATCH.
- **Q: How do you know the ESP32 is running the model that was actually trained?** A
  boot-time self-test replays 20 golden vectors (known inputs + expected outputs from the
  training run) through the model; any mismatch disables it and falls back to the rule
  engine automatically.
- **Q: Why C float arrays instead of TFLite, for the correct model?** No interpreter, no
  arena sizing, no quantization step — `ml_infer()` is a direct double-loop matrix
  multiply over plain float arrays, smaller and simpler to audit than linking
  `TensorFlowLite_ESP32`.
- **Q: Why does Test mode give zero vibration cues but Learn mode does?** By design —
  Learn mode teaches the pattern, Test mode assesses recall from memory; vibrating the
  answer during a test would give it away.
- **Q: How does the firmware survive a power loss mid-session?** `/state.bin` is
  rewritten after every completed prompt, and the SD log is opened/appended/closed per
  row — a crash costs at most the current prompt, not the whole session.

---

## 12. ML Training Pipeline

### `tools/train_and_export.py` — cited everywhere, missing from the repo

See §0.2. The README, `CONTRIBUTING.md`, and `firmware/tests/README.md` all cite this
script by name; it does not exist in the working tree or anywhere in git history. Only
its output (`model_weights.h`, `models/metrics_final.json`, `models/golden_vectors.json`)
survives.

### `tools/train.py` — the script that *is* present, a different, legacy pipeline

Uses `tensorflow.keras`, not sklearn — builds **one** `tf.keras.Model` with two output
heads sharing a `Dense(32,relu)→Dense(16,relu)` trunk, trains with weighted
sparse-categorical-crossentropy per head, then quantizes to **int8 TFLite**
(`models/model.tflite`) and hands off to `tools/tflite_to_header.py`, which emits
`firmware/braille_tutor/model_data.h` — **not** `model_weights.h`.
`firmware/tests/README.md` states plainly: *"The project no longer uses TFLite ...
t6_model — legacy TFLite test — superseded."* `model.tflite`, `model.keras`, and
`model_data.h` are therefore artifacts of an earlier, abandoned approach — the one
currently (and incorrectly) still linked by `braille_tutor.ino` (§0.1).

### What's actually deployed correctly: `model_weights.h`

Architecture: `Input(8) → Dense(32,ReLU) → Dense(16,ReLU) → Dense(3,softmax)`, trained
**twice** as two fully independent `sklearn.neural_network.MLPClassifier` instances — one
per head — because neither sklearn nor Keras 3 cleanly supports per-output class
weighting on a single multi-output model, so training one classifier per head is the
straightforward way to balance each head's class distribution independently.

- **8 input features**: response_time, press_duration, retry_count, prev_accuracy,
  prev_mastery, hint_count, current_streak, wrong_streak (confirmed against
  `models/golden_vectors.json`).
- **Dataset**: 1,000 real + 1,242 synthetic = 2,242 (§7).
- **Split** (`models/metrics_final.json`): train 1,569 / val 336 / test 337 (139 real rows
  in test).
- **Export**: each `MLPClassifier.coefs_[i]`/`.intercepts_[i]` flattened into a `static
  const float` C array, row-major, matching `inference.h`'s dense-layer loop exactly.

### Parameter count — verified by direct count, not assumption

867 params/head (8·32+32 + 32·16+16 + 16·3+3) × 2 heads = **1,734**, counted directly from
the 12 array declarations in `model_weights.h`.

### `models/golden_vectors.json`

20 vectors, each with `features_raw`, `features_norm`, `expect_teaching`,
`expect_confidence` — replayed on boot by any sketch that includes `model_weights.h` to
self-test the forward pass against what training computed.

---

## 13. The `models/` Folder

| File | Status | Key numbers |
|---|---|---|
| `metrics_final.json` | **Authoritative, current** | 8 features; 1,000 real + 1,242 synthetic = 2,242 rows; split 1,569/336/337; teaching combined 99.41% / real-only **98.56%** / majority baseline 46.59%; confidence combined 94.07% / real-only **91.37%** / majority baseline 42.43%. Per-class F1 — TA: REPEAT 0.994, HINT 0.989, NORMAL_PRACTICE 0.997; CS: CONFIDENT 0.938, HESITANT 0.928, GUESSING 0.960 |
| `metrics.json` | Historical — do not cite | Only 4 features, ~790 params, 743 real + 1,200 synthetic |
| `metrics_2k.json` | Historical — do not cite | 743 real + 1,464 synthetic; teaching real-only 96.08% |
| `metrics_balanced.json` | Historical — do not cite | 743 real + 3,036 synthetic; teaching 100%/100% (suspiciously perfect, likely overfit on over-synthesized data) |
| `golden_vectors.json` | Current | 20 self-test vectors, see §12 |
| `model.tflite` / `model.keras` | **Legacy, not the correct model** | Output of the abandoned Keras/TFLite pipeline (§12); currently still what `braille_tutor.ino` actually links (§0.1) |

**Rule for presentations: only ever quote numbers from `metrics_final.json`.**

---

## 14. Audio Generation and SD Card

### `tools/gen_audio.py`

Two selectable TTS engines: gTTS (needs internet) or espeak-ng (fully offline).
`web/audio/manifest.json` confirms the audio actually shipped was generated with
`"voice": "espeak-ng bn"` and `"human_recorded": false` — the offline fallback, not the
default. Synthesizes 50 letter clips (tracks 1–50, `id+1`) + 10 Bangla system prompts
(tracks 51–60: correct/wrong/try-again/hint/well-done/next-letter/review/harder/
session-start/session-end). Processed through `ffmpeg` to mono 44.1 kHz 64 kbps MP3,
written simultaneously to `web/audio/` and `sd_card/mp3/`.

### File layout

| Location | Files | Used by |
|---|---|---|
| `sd_card/mp3/` | 60 files, `0001.mp3`–`0060.mp3` | DFPlayer Mini — requires a folder literally named `mp3` at the SD card root, addressed by track number (`playMp3Folder(n)`), not filename |
| `web/audio/` | Same 60 files + `manifest.json` | Browser, in place of the SD card |

**Honesty note**: all shipped audio is synthetic (espeak-ng machine voice). Real
recordings can be dropped in later using the exact same track numbering, with zero code
changes.

---

## 15. Enclosure — 3D/Physical Design

### Tooling

`enclosure/braille_tutor_case.scad` and `top_panel_layout.scad` are **OpenSCAD** files —
open-source, script-based parametric CAD, where geometry is written as code and compiled
to a mesh, rather than modeled by hand in a GUI tool like Fusion 360 or SolidWorks. **If
asked "what CAD tool did you use," the accurate answer is OpenSCAD.**

The `.scad`/`.svg`/`.stl` files are themselves generated, not hand-drawn:
`tools/gen_top_panel.py` holds the component/pitch constants (button 12×12 mm, motor
Ø10 mm, speaker Ø40 mm, 30 mm grid pitch) and emits the 2D layout + cutout SVG;
`tools/gen_top_panel_3d.py` imports those same constants and builds the 3D mesh by hand
(conforming-Delaunay triangulation, no external mesh library), verified watertight
(0 non-manifold edges) and volume-checked. `enclosure/README.md` states explicitly that
every generated file traces back to one place and should never be hand-edited.

`enclosure/3d_preview.html` is flagged in `enclosure/README.md` itself as **superseded** —
an older mockup with stale (round, not square) button holes; `top_panel_3d.html` is the
current Three.js viewer and embeds the same verified mesh as `top_panel.stl`.

### Fabrication status — honest assessment

**The enclosure is a digital design, computationally verified but not confirmed
physically printed anywhere in the repo.** `enclosure/README.md`'s fabrication section
(print settings, screw sizes) reads as forward-looking instructions, not a build log. See
§0.5 for how this relates to the separately-confirmed breadboard electronics build.

---

## 16. `Arduino/` — Early Prototyping (superseded by `firmware/`)

`Arduino/README.md` states plainly: these are **not** the shipping firmware — the
deliverable is `firmware/braille_tutor/`. Pin assignments here differ from the canonical
`pins.h` map.

| Item | What it is |
|---|---|
| `p1_pin_tester` → `p6_dual_mode` | Six incremental prototyping sketches: raw button test → +motors → +audio → +chord input → +audio&vibrate together → dual mode |
| `milse1` | **The confirmed-working bench build** — speaker, all 7 buttons, all 6 motors, per `Arduino/README.md` |
| `_archive/chord_typing_dot6_prefix` | An abandoned earlier two-cell-encoding variant, kept for history |
| `final_working_20260907_1017` | A dated snapshot with its own Braille lookup table — **flagged unreliable**, disagreeing with `braille_map.h` on 33 of 50 letters; do not use this table as a reference |
| `libraries/DFRobotDFPlayerMini/` | Vendored third-party Arduino library, not project code |

---

## 17. Root Project Files

| File | Purpose |
|---|---|
| `LICENSE` | MIT — permissive reuse/modification/redistribution with attribution, no warranty |
| `CITATION.cff` | Citation metadata. **See §0.4** — the associated IEEE journal citation is a placeholder, not a real publication |
| `CONTRIBUTING.md` | No-PII rule (use `P01`/`P02` codes), the spec→generator diagram, setup steps, PR guidelines — also repeats the missing `train_and_export.py` instruction |
| `requirements.txt` | `numpy`, `scipy`, `scikit-learn>=1.3.0`, `Pillow`, `requests`, `python-pptx` — **no `tensorflow`**, meaning `tools/train.py`'s legacy path needs TF installed separately to even run |
| `package.json` (root) | `scripts.dev` = local static server, `scripts.test` = `run_all_tests.py`; no npm dependencies |
| `web/package.json` | Just `{"type":"module"}` |
| `vercel.json` | One rewrite rule serving `web/`'s contents at the deployed root URL |
| `.env.example` | Template for `SUPABASE_URL`, `SUPABASE_ANON_KEY` (safe, client-side), `SUPABASE_SERVICE_KEY` (secret, bypasses RLS — never commit) |
| `USER_MANUAL.md` | Bengali-language guide for participants using the web app |
| `index.html` (root) | Redirect page sending repo-root visitors into `web/` |

---

## 18. Master Q&A Index

Every section above ends with its own detailed Q&A block. The highest-value ones to
review before a viva, in order of how likely they are to come up:

1. **"What model is actually running on your device right now?"** → §0.1, §9, §10
2. **"Walk me through how data flows between the app and the ESP32."** → §8 (with the
   diagram)
3. **"How did you verify your Braille patterns are correct?"** → §0.3, §5
4. **"What's your model's accuracy, and where does that number come from?"** → §12, §13
5. **"Can I see your training script run?"** → §0.2, §12
6. **"What CAD tool did you use for the enclosure, and is it built?"** → §15, §0.5
7. **"Is this published research?"** → §0.4
8. **"What happens if the network/power drops mid-session?"** → §6, §9 (both have this
   answered independently, for the web app and the firmware)
9. **"Why did you choose two separate networks instead of one multi-output model?"** →
   §12
10. **"What's your test coverage, and how do you know the three rule engines agree?"** →
    §4

---

*This document was built by reading every file in the repository directly — not by
summarizing the README — specifically so it could catch and correct places where the
README's marketing language had drifted from what the code actually does. If you update
the code, the honest thing to do is re-check whether the corresponding section here (and
the README) still matches, especially §0.1 and §0.2 if the training script or the main
sketch's model wiring ever gets fixed.*
