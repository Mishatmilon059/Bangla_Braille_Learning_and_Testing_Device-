# Arduino sketchbook — bench prototypes

This folder is the Arduino IDE sketchbook used while the hardware was being
built on a breadboard. Point the IDE at this directory (File > Preferences >
Sketchbook location) and the bundled `libraries/DFRobotDFPlayerMini` is picked
up automatically, so nothing needs installing.

These are **not** the shipping firmware. The deliverable is
[`firmware/braille_tutor/`](../firmware/braille_tutor/), with its staged
bring-up sketches in [`firmware/tests/`](../firmware/tests/). What lives here is
the earlier, single-file lineage that proved each peripheral by hand.

## Read this before flashing anything

The pin assignments here are the ones that were physically wired on the
breadboard. They are **different from** the canonical map in
[`firmware/braille_tutor/pins.h`](../firmware/braille_tutor/pins.h), which moved
the buttons and motors onto pins chosen for their pull-ups and strapping
behaviour. Do not mix a sketch from this folder with wiring built to `pins.h`.

| | this sketchbook | `pins.h` |
|---|---|---|
| dot buttons | 4, 5, 15, 19, 21, 22 | 32, 33, 25, 26, 27, 14 |
| motors | 13, 14, 26, 27, 32, 33 | 13, 4, 21, 22, 2, 15 |
| DFPlayer RX / TX | 25 / 23 | 16 / 17 |
| submit / enter | 18 / 23, 34 or 16 | 34 (submit) |

## The sketches, in the order they were built

| # | Sketch | Adds | Input |
|---|---|---|---|
| 1 | `p1_pin_tester` | nothing — raw pin diagnostic, no debounce | buttons |
| 2 | `p2_motor_letters` | six vibration motors | serial, 1-37 |
| 3 | `p3_audio_and_vibrate` | DFPlayer audio on top of the motors | serial, 1-50 |
| 4 | `p4_chord_typing` | 6-dot chord input, submit, enter | buttons |
| 5 | `p5_chord_audio_vibrate` | buttons + audio + vibration together | buttons |
| 6 | `p6_dual_mode` | typing mode (audio only) and tutor mode (audio + vibration) | buttons and serial |

## The one that works: `milse1`

`milse1` is the build confirmed working on the bench: speaker, all seven
buttons and all six motors. Flash this one to demo the breadboard. The `p*`
sketches above are the history that led to it.

It is `p6_dual_mode` with five differences:

| | `p6_dual_mode` | `milse1` |
|---|---|---|
| Enter button | GPIO 16, `INPUT_PULLUP` | GPIO 34, plain `INPUT` |
| DFPlayer pin macros | `PIN_DF_RX` / `PIN_DF_TX` | `PIN_DF_ESP_RX` / `PIN_DF_ESP_TX` |
| Track addressing | `playMp3Folder()` | `play()` |
| Volume | 22 | 25 |
| Settle before `begin()` | 500 ms | 1000 ms |

Three notes on it, none a reason to change working hardware:

- **`play()` rather than `playMp3Folder()`.** `play(n)` takes the nth file in
  the card's index order rather than resolving `/mp3/000n.mp3` by name. It is
  correct here because the card was written once, in order, with nothing else
  on it. Rewrite or reorder the card and the mapping can shift.
- **Enter on GPIO 34 with plain `INPUT`.** More honest than the
  `INPUT_PULLUP` it replaced, since GPIO 34 has no internal pull-up to
  enable. The pin still floats without an external 10k to 3V3, so Enter can
  self-trigger. Add the resistor if you see phantom message prints.
- **The `begin()` failure branch is unreachable.** With `isACK` false the
  library returns `... || !isACK`, so those four "Check:" hints never print.
  Harmless while the audio works; misleading the next time it does not.

## `final_working_20260907_1017`

Saved 7 September 2026, 10:17. Same hardware and pins as `milse1`, but a
different program and a different Braille table.

The program is a three-mode menu driven over serial: `L` enters Learn, which
speaks a letter and vibrates its dots; `T` enters Test, which speaks a letter
and scores the dots you press; `M` or the Enter button returns to the menu and
prints the running score. It has no typing-to-text mode, so nothing does a
reverse pattern lookup.

**Its `BRAILLE_PATTERN` table is not usable as ground truth.** Every hex value
does agree with its own dot-list comment, so there are no transcription typos,
but the table itself is not one-to-one:

- **34 distinct patterns for 50 letters.** Twelve patterns are shared by 28
  letters. Dots 1-4-5 is listed as the answer for ঈ, ঙ and দ at once; dots
  1-2-4-5 for ঋ, গ and ং; dots 1-2-4-5-6 for ও, ঢ and ড়. Six dots give 63
  distinct non-empty patterns, so 50 letters fit with room to spare. Collisions
  mean the chart was misread, not that the encoding ran out of room.
- **It contradicts `firmware/braille_tutor/braille_map.h` on 33 of 50
  letters**, including 10 of the 11 that map marks as verified against a
  supplied chart image. For আ the verified pattern is dots 3-4-5 and this table
  says dots 1-2.

Test mode still scores each question, because it compares against the pattern
at a known index rather than searching. But a collided letter teaches the
learner two contradictory answers, and rows logged from it would corrupt the
training set. `tools/validate_braille_map.py` exists for exactly this check and
says so in its own docstring. Reconcile the chart against the images in
`braille_img/` before treating this table as correct.

## Known problems, kept unfixed on purpose

Each sketch reproduces what was actually on the bench, so the flaws are
documented rather than patched. The fixes all live in the `firmware/` tree.

- **GPIO 34 has no internal pull-up.** `p5` calls
  `pinMode(enterButtonPin, INPUT_PULLUP)` on GPIO 34, which is input-only. The
  call is a no-op and the button floats. It needs an external 10k to 3V3.
  `p6` has since moved Enter to GPIO 16, which does have one. Note that
  GPIO 16/17 are wired to PSRAM on ESP32-WROVER modules and unusable there;
  `p6` assumes a WROOM.
- **GPIO 23 is triple-booked.** It is "Submit" in `p1`, "Enter" in `p4`, and the
  DFPlayer TX line in `p5`/`p6`.
- **`p2` carries a stale dictionary.** Its 37-letter table disagrees with the
  canonical 50-letter table on three characters: খ (`0x2D` vs `0x28`), ঝ (`0x35`
  vs `0x34`) and ভ (`0x27` vs `0x18`). The 50-letter table in `p3`/`p5`/`p6`
  matches `firmware/braille_tutor/braille_map.h` and is the one to trust.
- **`p3` sets an out-of-range volume.** `dfPlayer.volume(50)`; the part accepts
  0-30. `p5` uses 30 and `p6` uses 22.
- **`p3` and `p5` address audio with `play()`, `p6` with `playMp3Folder()`.**
  `play(n)` takes the nth file in the card's index order, which depends on the
  order the files were written. `playMp3Folder(n)` resolves `/mp3/000n.mp3` by
  name and is the reliable one, but it needs `mp3/` at the card root. Copy the
  contents of `sd_card/`, not the `sd_card` folder itself.
- **Keep `begin()`'s isACK argument true.** The library returns
  `... || !isACK`, so passing false makes `begin()` report success with no
  module attached, and disables the acknowledgement that would surface any
  later command failure. A dead DFPlayer then looks exactly like a working
  one.
- **ঋ and র share pattern `0x17`.** The decoders skip index 6 during the
  one-cell search, so a bare `0x17` chord resolves to র and ঋ is reachable only
  through the dot-5 two-cell prefix.

## `_archive/`

`chord_typing_dot6_prefix` is an earlier `p4` that used a **dot-6** prefix for ৎ
and a dot-5 prefix for ঋ. That was dropped in favour of a single dot-5 prefix
for both, which is what `p4`, `p5` and `p6` implement. Kept only for the
history; the IDE will still open it.
