# Bring-up sketches — run these in order

Do **not** flash `braille_tutor.ino` first. It drives six buttons, six motors,
a DFPlayer, an SD card and a neural network at once; if anything is miswired
you get one symptom and eighteen possible causes.

Each sketch here adds exactly one peripheral. Every one prints what it expects
to see, so you know whether it passed without guessing.

| # | Sketch | Proves | Typical failure |
|---|---|---|---|
| 1 | `t1_blink_serial` | Board alive, serial at 115200 | Wrong board selected, bad USB cable (many are charge-only) |
| 2 | `t2_buttons` | All 6 buttons, debounce, press timing | Button on a pin with no internal pull-up |
| 3 | `t3_motors` | ULN2803A drives each motor | COM pin not tied to +5V — motors weak or GPIO dies |
| 3b | `t3b_braille_patterns` | A typed letter buzzes the right dots | Motor channel swapped — dot 3 fires where dot 4 should |
| 4 | `t4_dfplayer` | Audio plays by track number | Files not in `/mp3`, or not named `0001.mp3` |
| 5 | `t5_sd` | Card mounts, CSV appends | 3.3V-only module fed 5V, or CS on the wrong pin |
| 6 | `t6_model` | TFLite Micro matches `train.py` | Arena too small, or stale `model_data.h` |

Only after all six pass should you flash `braille_tutor.ino`. `t3b` is optional
for bring-up but is the one place you can check a Braille cell by touch before
the whole tutor is running: type a letter number (1–50) or its name into the
Serial Monitor and the motors buzz its dots in reading order — 1 2 3 down the
left column, then 4 5 6 down the right. It prints the cell as ASCII at the same
time, so you can see what you should be feeling.

## Power, before you start

Six motors at once pull ~480 mA. Add the ESP32 and DFPlayer and you are near
800 mA peak. Use a **5 V 2 A supply**, not a laptop USB port, and put a
**1000 µF capacitor across the motor rail**. Without it the motor inrush
browns out the 3V3 regulator and the ESP32 reboots mid-session — which looks
exactly like a firmware crash and is not one. If your board resets whenever
several motors fire together, this is why.

Never drive motors from the ESP32's 3V3 pin. Common ground everywhere.

## Generating the headers

Sketches 3b and 6 and the main firmware need the generated headers, and each
Arduino sketch folder needs its own copy. From the repo root:

```bash
python3 tools/gen_engine.py
python3 tools/gen_braille_header.py
python3 tools/train.py && python3 tools/tflite_to_header.py
cp firmware/braille_tutor/{rule_engine.h,braille_map.h,model_data.h} firmware/tests/t6_model/
cp firmware/braille_tutor/braille_map.h firmware/tests/t3b_braille_patterns/
```

Re-run the copy after every `gen_braille_header.py` — the copies are snapshots,
and a stale one means `t3b` buzzes a pattern the rest of the system no longer
believes in.

## Why t6 can fail even when the model is fine

TFLite Micro's `FULLY_CONNECTED` kernel takes **one** requantization multiplier
from `filter->params.scale` and applies it to every output channel. TFLite's
converter defaults to **per-channel** weights — one scale per output unit.
Nothing rejects that combination: TFLM loads the model, runs it, and quietly
uses channel 0's scale for all channels. The softmax still sums to 1.0 and the
output still looks like a probability distribution; it is just the wrong one.

`tools/train.py` therefore disables per-channel quantization for the Dense
layers, and asserts after conversion that no weight tensor carries more than one
scale. If you ever see t6 report plausible-but-wrong classes while the desktop
model is correct, check that first.

---

## Remote / cloud-connected sketches — a separate track

Everything above builds toward `braille_tutor.ino`, which is deliberately
WiFi-free. The sketches below are a **parallel, separate mode**: the ESP32
joins WiFi and polls Supabase for commands from `web/teacher.html`, instead of
running the on-device model. See the root `README.md`'s "Remote / cloud-
connected mode" section for the full data-flow diagram and one-time Supabase
setup. Summary here:

| Sketch | Role | Flash it when... |
|---|---|---|
| `t7_cloud_dot` | Earliest bring-up: buzz one dot on command | Verifying WiFi + Supabase reachability, motors only |
| `t8_cloud_quiz` | Full quiz flow prototype | Superseded by `t11_testing`; kept for reference |
| `t9_dfplayer_test` | Pure DFPlayer diagnostic, no WiFi | Audio not playing and you need to isolate hardware from network |
| `t10_learning` | Teach mode: audio + vibration, retries until correct, reports every attempt to `attempts` | Teacher panel's শেখানো (Learn) tab |
| `t11_testing` | Assessment mode: audio only, one attempt, no retry, Serial batch summary at the end | Teacher panel's পরীক্ষা (Test) tab |
| `firmware/t11_ml_test/` *(one level up, not under `tests/`)* | Same as `t10_learning` but also runs the on-device ML model and logs its real decision, for inspecting model-vs-rule-engine agreement | Comparing the trained model against the rule engine on real presses |

Only flash **one of these at a time** — they share `device_id: "esp32_01"`
and will all respond to the same `remote_commands` rows otherwise, which
looks like the board answering with the wrong behavior. Each folder has its
own `secrets.h` (gitignored) that needs real `WIFI_SSID`/`WIFI_PASS` filled
in before it'll connect.

**Verified pin mapping** (all remote-mode sketches share this — see each
folder's `pins.h`):

```
PIN_BUTTON = { 32, 33, 25, 26, 27, 14 }   // dot 1..6
PIN_MOTOR  = { 21, 13, 22, 2, 15, 4 }     // dot 1..6 -- confirmed against
                                          // physical wiring via a button-
                                          // press-buzzes-same-dot sync test;
                                          // do not "simplify" this ordering
PIN_SUBMIT = 12                          // strapping pin, must read LOW at boot
```

If you rewire and need to re-verify this mapping, flash `t_sync_test`: hold
each dot button in turn and confirm the SAME dot's motor buzzes. `t_motor_test`
is the same idea without WiFi, for isolating a motor/ULN2803A problem from the
network stack.
