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
| 4 | `t4_dfplayer` | Audio plays by track number | Files not in `/mp3`, or not named `0001.mp3` |
| 5 | `t5_sd` | Card mounts, CSV appends | 3.3V-only module fed 5V, or CS on the wrong pin |
| 6 | `t6_model` | TFLite Micro matches `train.py` | Arena too small, or stale `model_data.h` |

Only after all six pass should you flash `braille_tutor.ino`.

## Power, before you start

Six motors at once pull ~480 mA. Add the ESP32 and DFPlayer and you are near
800 mA peak. Use a **5 V 2 A supply**, not a laptop USB port, and put a
**1000 µF capacitor across the motor rail**. Without it the motor inrush
browns out the 3V3 regulator and the ESP32 reboots mid-session — which looks
exactly like a firmware crash and is not one. If your board resets whenever
several motors fire together, this is why.

Never drive motors from the ESP32's 3V3 pin. Common ground everywhere.

## Generating the headers

Sketch 6 and the main firmware need the generated headers. From the repo root:

```bash
python3 tools/gen_engine.py
python3 tools/gen_braille_header.py
python3 tools/train.py && python3 tools/tflite_to_header.py
```

They are not copied into `t6_model/`. Its `platformio.ini` adds
`firmware/braille_tutor/` to the include path instead, so the sketch always
tests the exact headers the main firmware compiles — a copy is how this test
ends up passing against a model the firmware no longer runs.

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
