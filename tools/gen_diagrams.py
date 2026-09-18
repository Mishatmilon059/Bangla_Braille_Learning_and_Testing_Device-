#!/usr/bin/env python3
"""Generate the presentation diagrams as SVG (editable) + PNG (drop-in).

    python3 tools/gen_diagrams.py

Output: docs/diagrams/NN_name.svg and .png, all on a pure white background.

Figures are numbered in presentation order and follow the real pipeline:
simulation -> database -> CSV -> TinyML training -> ESP32 deployment ->
classroom use -> teacher analytics.

Two rendering rules learned the hard way, both visible as empty boxes if broken:
  * Bangla text MUST carry font-family "Noto Sans Bengali" (FONT_BN). Arial has
    no Bengali glyphs and silently renders every character as tofu.
  * No emoji anywhere. The rasteriser has no emoji font, so they become boxes
    too. Icons are drawn as shapes or plain ASCII instead.

Status badges ("BUILT" / "PLANNED") are deliberate. Three of these stages do not
exist yet, and a deck that shows them identically to the finished ones would
misrepresent the project to anyone reading it.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from svgkit import (APP, BAD, DATA, FONT_BN, H, HW, INK, LINE, MODEL, MUTED,
                    OK, SIM, TINT, W, WARN, WHITE, Svg)

# Both overridable so this one script can regenerate either the original
# docs/diagrams (metrics.json, kept for comparison) or a fresh set from the
# current, authoritative metrics_final.json -- see tools/gen_diagrams_v2.py.
OUT = Path(os.environ.get("GEN_DIAGRAMS_OUT", str(ROOT / "docs" / "diagrams")))
METRICS_PATH = Path(os.environ.get("GEN_DIAGRAMS_METRICS", str(ROOT / "models" / "metrics.json")))
INCLUDE_EXTRA = os.environ.get("GEN_DIAGRAMS_EXTRA") == "1"


def _count_params_from_header(header_path):
    """Ground truth for parameter count: count the floats actually compiled
    into firmware/braille_tutor/model_weights.h, rather than trusting any
    document (two of which disagreed on this number)."""
    text = header_path.read_text(encoding="utf-8")
    total = 0
    for m in re.finditer(r"static const float ML_\w+\[\]\s*=\s*\{([^}]*)\}", text):
        total += len(re.findall(r"-?[\d.]+f", m.group(1)))
    return total


def _load_metrics(path):
    """Adapts either metrics.json (old schema: 4 features/790 params) or
    metrics_final.json (current schema: 8 features/1,734 params) into one
    shape the diagram builders can read without caring which file it was."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "trainable_params_approx" in raw:
        # Old schema (models/metrics.json) -- kept working for comparison runs.
        # This file predates TFLite export too (see its own "note" field), so
        # bytes is the same raw-float32 estimate used for the current model.
        params = raw["trainable_params_approx"]
        ta = raw.get("test_accuracy", {})
        return {
            "params": params,
            "bytes": params * 4,
            "teach_acc": ta.get("teaching_real_only", ta.get("teaching_combined", 0)),
            "conf_acc": ta.get("confidence_real_only", ta.get("confidence_combined", 0)),
            "features": raw.get("features", []),
            "n_features_model": len(raw.get("features", [])),
            "real": raw.get("rows", {}).get("real", 0),
            "synthetic": raw.get("rows", {}).get("synthetic", 0),
            "total": raw.get("rows", {}).get("total", 0),
        }
    # Current schema (models/metrics_final.json).
    params = _count_params_from_header(ROOT / "firmware" / "braille_tutor" / "model_weights.h")
    return {
        "params": params,
        "bytes": params * 4,           # raw float32 C arrays -- no TFLite, no quantization
        "teach_acc": raw["test_accuracy"]["teaching_real_only"],
        "conf_acc": raw["test_accuracy"]["confidence_real_only"],
        "teach_combined": raw["test_accuracy"]["teaching_combined"],
        "conf_combined": raw["test_accuracy"]["confidence_combined"],
        "features": raw["features"],
        "n_features_model": raw["feature_count"],
        "real": raw["dataset"]["real"],
        "synthetic": raw["dataset"]["synthetic"],
        "total": raw["dataset"]["total"],
    }


# Real measured figures, read from the repo so the slides cannot drift from it.
M = _load_metrics(METRICS_PATH)
BMAP = json.loads((ROOT / "data" / "braille_map.json").read_text(encoding="utf-8"))
N_VERIFIED = sum(1 for l in BMAP["letters"] if l.get("verified"))
N_TOTAL_LETTERS = len(BMAP["letters"])
PARAMS = M["params"]
TFLITE_B = M["bytes"]                  # kept as bytes-on-device, name kept for callers below
TEACH_ACC = M["teach_acc"]
CONF_ACC = M["conf_acc"]
N_FEATURES_MODEL = M["n_features_model"]
DATA_REAL, DATA_SYNTH, DATA_TOTAL = M["real"], M["synthetic"], M["total"]

TA_CLASSES = ["REPEAT", "HINT", "NORMAL_PRACTICE"]
CS_CLASSES = ["CONFIDENT", "HESITANT", "GUESSING"]

BUILT, PLANNED = "BUILT", "PLANNED"

# Vertical rhythm: every diagram fills this band so no slide has a dead half.
TOP, BOTTOM = 150, 800


# ===========================================================================
def d01_overview():
    s = Svg(title="System overview")
    s.header("AI-Assisted Bangla Braille Tutor",
             "Complete pipeline: simulation to data to TinyML to offline hardware to analytics")

    stages = [
        ("1", "SIMULATION", SIM, BUILT,
         ["Web app teaches Braille", "and records every", "attempt a learner makes"]),
        ("2", "DATABASE", DATA, BUILT,
         ["Supabase stores 14", "features and 2 labels", "for every attempt"]),
        ("3", "TinyML MODEL", MODEL, BUILT,
         [f"{PARAMS:,} parameters", f"{TFLITE_B:,} bytes as", "plain C float arrays"]),
        ("4", "ESP32 DEVICE", HW, PLANNED,
         ["Runs fully offline.", "Speaker, 6 buttons", "and 6 vibration motors"]),
        ("5", "MOBILE APP", APP, PLANNED,
         ["Teacher sees progress,", "learning curves and", "AI suggestions"]),
    ]

    bw, bh, gap = 265, 300, 20
    x0, y = 60, TOP + 30
    for i, (num, name, color, status, body) in enumerate(stages):
        x = x0 + i * (bw + gap)
        s.rect(x, y, bw, bh, fill=TINT[color], stroke=color, sw=2.5)
        s.circle(x + 36, y + 46, 22, fill=color, stroke=color)
        s.text(x + 36, y + 54, num, 21, "bold", WHITE, "middle")
        s.text(x + 68, y + 54, name, 17.5, "bold", INK)
        s.lines(x + 20, y + 108, body, 14.5, 24, INK)
        s.badge(x + bw - 16, y + bh - 42, status)

        if i < len(stages) - 1:
            s.arrow(x + bw + 3, y + bh / 2, x + bw + gap - 4, y + bh / 2, color=LINE, sw=3)

    # what travels along each hop
    flows = ["real learner attempts", "CSV export", "trained weights → C header", "session logs (SD card)"]
    for i, f in enumerate(flows):
        x = x0 + (i + 1) * (bw + gap) - gap / 2
        s.text(x, y + bh + 34, f, 12.5, "normal", MUTED, "middle")

    # feedback loop back to training
    ly = y + bh + 92
    s.path(f"M {x0 + 4 * (bw + gap) + bw / 2} {y + bh + 50} L {x0 + 4 * (bw + gap) + bw / 2} {ly} "
           f"L {x0 + 2 * (bw + gap) + bw / 2} {ly} L {x0 + 2 * (bw + gap) + bw / 2} {y + bh + 8}",
           stroke=MUTED, sw=2.5, dash="7 6")
    s.text(x0 + 3 * (bw + gap), ly - 12,
           "continuous learning — retrain on new data, redeploy", 14, "bold", MUTED, "middle")

    s.legend(60, BOTTOM - 10, [("Built and tested", OK), ("Planned / not built yet", WARN)])
    s.footnote("All figures are measured from the current build, not estimates.")
    return s, "01_system_overview"


# ===========================================================================
def d02_simulation():
    s = Svg(title="Phase 1 — simulation and data collection")
    s.header("Phase 1 — Simulation captures real learner behaviour",
             "The web app is a measuring instrument first and a tutor second",
             BUILT, OK)

    s.rect(60, TOP, 500, BOTTOM - TOP, fill=WHITE, stroke=LINE, sw=2, dash="7 6")
    s.text(80, TOP + 32, "IN THE BROWSER", 14, "bold", MUTED)

    steps = [
        ("Audio prompt", "the app speaks a Bangla letter", SIM),
        ("Learner responds", "presses 6 keys = 6 Braille dots", SIM),
        ("System scores it", "entered pattern vs expected", SIM),
        ("Rule engine decides", "teaching action + confidence", MODEL),
    ]
    for i, (t, sub, c) in enumerate(steps):
        y = TOP + 60 + i * 145
        s.rect(90, y, 440, 105, fill=TINT[c], stroke=c, sw=2)
        s.circle(126, y + 52, 21, fill=c, stroke=c)
        s.text(126, y + 60, str(i + 1), 19, "bold", WHITE, "middle")
        s.text(162, y + 44, t, 18, "bold", INK)
        s.text(162, y + 72, sub, 14, "normal", MUTED)
        if i < 3:
            s.arrow(310, y + 107, 310, y + 143, color=LINE, sw=2.5)

    # recorded fields
    s.rect(600, TOP, 480, 340, fill=TINT[DATA], stroke=DATA, sw=2.5)
    s.text(624, TOP + 38, "RECORDED PER ATTEMPT", 15, "bold", DATA)
    rec = ["response time", "press duration", "retry count", "hint count",
           "prev accuracy", "prev mastery", "current streak", "wrong streak",
           "time since practice", "session number", "difficulty level", "prev mistakes",
           "character id", "prev confidence"]
    for i, r in enumerate(rec):
        s.text(624 + (i % 2) * 228, TOP + 78 + (i // 2) * 30, "•  " + r, 14, "normal", INK)
    s.rect(624, TOP + 285, 432, 38, fill=WHITE, stroke=DATA, sw=1.5, r=8)
    s.text(840, TOP + 310, "14 features  +  2 labels  =  1 row", 15.5, "bold", DATA, "middle")

    # braille cell
    s.rect(600, TOP + 370, 480, BOTTOM - TOP - 370, fill=WHITE, stroke=LINE, sw=2)
    s.text(624, TOP + 404, "VIRTUAL BRAILLE CELL", 14, "bold", MUTED)
    s.braille_cell(680, TOP + 450, [1, 3, 6], dot_r=16, gap_x=52, gap_y=48, labels=True)
    s.lines(790, TOP + 452, [
        "The 6 dots on screen map", "one-to-one onto the 6",
        "vibration motors on the", "hardware build.",
    ], 15, 25, INK)

    s.rect(1120, TOP, 420, BOTTOM - TOP, fill=TINT[OK], stroke=OK, sw=2.5)
    s.text(1144, TOP + 38, "WHY SIMULATE FIRST", 15, "bold", OK)
    s.lines(1144, TOP + 78, [
        "No hardware is needed to",
        "start collecting real",
        "learner behaviour.",
        "",
        "Volunteers practise with",
        "eyes closed, so the timing",
        "and hesitation recorded",
        "are genuine.",
        "",
        "The same rule engine that",
        "runs here is generated",
        "into the ESP32 firmware,",
        "so the two can never",
        "drift apart.",
        "",
        "Collection can begin weeks",
        "before any component",
        "arrives.",
    ], 15, 26, INK)

    s.footnote("Every row is written to local storage first, then synced — a dropped connection never loses data or interrupts a session.")
    return s, "02_phase1_simulation"


# ===========================================================================
def d03_features():
    s = Svg(title="Features and labels")
    s.header("What the model sees, and what it predicts",
             "14 numeric inputs, two simultaneous outputs", BUILT, OK)

    groups = [
        ("SAMPLED BEFORE THE ATTEMPT", ["character id", "prev accuracy", "prev mastery",
                                        "prev mistakes", "prev confidence", "session number",
                                        "difficulty level", "time since last practice"], DATA),
        ("MEASURED DURING", ["response time", "press duration",
                             "retry count", "hint count"], SIM),
        ("READ AFTER SCORING", ["current streak", "wrong streak"], OK),
    ]
    x = 60
    for name, items, color in groups:
        w = 320 if len(items) > 4 else 250
        s.rect(x, TOP, w, 330, fill=TINT[color], stroke=color, sw=2.5)
        s.text(x + 18, TOP + 36, name, 14, "bold", color)
        for i, it in enumerate(items):
            s.text(x + 18, TOP + 76 + i * 30, "•  " + it, 15, "normal", INK)
        x += w + 26

    # key insight band
    s.rect(60, TOP + 360, 916, 290, fill=TINT[WARN], stroke=WARN, sw=2.5)
    s.text(84, TOP + 398, "KEY DESIGN POINT", 16, "bold", WARN)
    s.text(84, TOP + 428, "There is deliberately no \"is correct\" input.", 17, "bold", INK)
    s.lines(84, TOP + 464, [
        "The two streaks are read AFTER the answer is scored, so correctness is",
        "already implied by them:",
    ], 15, 24, INK)
    s.rect(84, TOP + 508, 420, 40, fill=WHITE, stroke=OK, sw=2, r=8)
    s.text(294, TOP + 534, "current streak > 0   →   answer was RIGHT", 14.5, "bold", OK, "middle")
    s.rect(520, TOP + 508, 420, 40, fill=WHITE, stroke=BAD, sw=2, r=8)
    s.text(730, TOP + 534, "wrong streak > 0   →   answer was WRONG", 14.5, "bold", BAD, "middle")
    s.lines(84, TOP + 578, [
        "Exactly one is ever non-zero. This lets the network reproduce every rule the",
        "engine applies — had the streaks been read before scoring, the engine would",
        "branch on information the model cannot see, and accuracy would cap out for",
        "reasons that look like a training bug but are not.",
    ], 14.5, 21, INK)

    # outputs
    s.rect(1006, TOP, 534, 175, fill=TINT[MODEL], stroke=MODEL, sw=2.5)
    s.text(1030, TOP + 36, "OUTPUT 1 — TEACHING ACTION", 15, "bold", MODEL)
    s.text(1030, TOP + 60, "3 classes", 13.5, "normal", MUTED)
    for i, a in enumerate(["Repeat", "Hint", "Normal Practice"]):
        cx = 1030 + i * 172
        s.rect(cx, TOP + 78, 158, 48, fill=WHITE, stroke=MODEL, sw=1.5, r=10)
        s.text(cx + 79, TOP + 109, a, 14.5, "bold", INK, "middle")
    s.text(1030, TOP + 156, "Down from 6 — the other 3 were retired in spec v2",
           12.5, "normal", MUTED)

    s.rect(1006, TOP + 205, 534, 175, fill=TINT[APP], stroke=APP, sw=2.5)
    s.text(1030, TOP + 241, "OUTPUT 2 — CONFIDENCE STATE", 15, "bold", APP)
    s.text(1030, TOP + 265, "3 classes", 13.5, "normal", MUTED)
    for i, c in enumerate(CS_CLASSES):
        cx = 1030 + i * 172
        s.rect(cx, TOP + 283, 158, 48, fill=WHITE, stroke=APP, sw=1.5, r=10)
        s.text(cx + 79, TOP + 314, c.title(), 15, "bold", INK, "middle")
    s.text(1030, TOP + 361, "Inferred from speed, retries and hesitation.", 14, "normal", MUTED)

    s.rect(1006, TOP + 410, 534, 240, fill=WHITE, stroke=LINE, sw=2)
    s.lines(1030, TOP + 448, [
        "Two independent networks, not a",
        "shared trunk: TA and CS are each",
        f"their own Input({N_FEATURES_MODEL})→32→16→3",
        "MLP, trained separately in scikit-learn.",
        "",
        f"{PARAMS:,} parameters combined ({PARAMS//2:,} each)",
        "is still small enough that running both",
        "costs under a millisecond together.",
    ], 14.5, 23, MUTED)

    s.footnote("Feature scaling uses fixed ranges from the spec, never dataset statistics — so retraining can never desynchronise the device from the model.")
    return s, "03_features_and_labels"


# ===========================================================================
def d04_data_pipeline():
    s = Svg(title="Data pipeline")
    s.header("From learner sessions to a training set",
             "Real data first — synthetic data is fitted to it, never invented before it",
             BUILT, OK)

    s.card(60, TOP, 340, 230, "1.  Learner sessions", [
        "4 volunteers (P01–P04)",
        "Short sessions, spread",
        "across several days",
        "",
        f"Collected: {DATA_REAL:,} real rows",
    ], SIM)
    s.arrow(405, TOP + 115, 455, TOP + 115, color=LINE, sw=3)

    s.card(460, TOP, 340, 230, "2.  Supabase database", [
        "One flat 'attempts' table",
        "Append-only, deduplicated",
        "Live class-balance views",
        "",
        "Both laptops write to it",
    ], DATA)
    s.arrow(805, TOP + 115, 855, TOP + 115, color=LINE, sw=3)

    s.card(860, TOP, 340, 230, "3.  CSV export", [
        "Merges every source",
        "Audits the result",
        "Flags starved classes",
        "",
        "→ dataset/real.csv",
    ], DATA)

    s.card(460, TOP + 275, 740, 215, "4.  Synthetic generation — fitted to the real data", [
        "Timing distributions are measured from the real rows, then virtual learners",
        "are simulated through the SAME state machine the web app uses.",
        "",
        "Every generated row is internally consistent because it came from a simulated",
        "session — not from sampling 14 numbers independently, which would produce",
        "impossible combinations the model would waste capacity learning.",
    ], MODEL)
    s.elbow(1030, TOP + 233, 830, TOP + 273, color=MODEL, sw=2.5, via_y=TOP + 254)

    # actual mix achieved
    real_pct = round(100 * DATA_REAL / DATA_TOTAL)
    synth_pct = 100 - real_pct
    s.rect(60, TOP + 275, 340, 215, fill=WHITE, stroke=LINE, sw=2)
    s.text(84, TOP + 311, "ACTUAL MIX — COLLECTION COMPLETE", 14, "bold", MUTED)
    s.rect(84, TOP + 335, 120, 54, fill=TINT[SIM], stroke=SIM, sw=2, r=8)
    s.text(144, TOP + 369, f"{real_pct}% real", 17, "bold", SIM, "middle")
    s.rect(216, TOP + 335, 160, 54, fill=TINT[MODEL], stroke=MODEL, sw=2, r=8)
    s.text(296, TOP + 369, f"{synth_pct}% synthetic", 17, "bold", MODEL, "middle")
    s.lines(84, TOP + 418, [
        f"{DATA_REAL:,} real + {DATA_SYNTH:,} synthetic",
        f"= {DATA_TOTAL:,} rows. Synthetic tops up",
        "actions that need deliberately",
        "induced mistakes to occur at all.",
    ], 14, 22, MUTED)

    s.rect(1230, TOP, 310, 490, fill=TINT[WARN], stroke=WARN, sw=2.5)
    s.text(1254, TOP + 36, "ORDER MATTERS", 15, "bold", WARN)
    s.lines(1254, TOP + 76, [
        "Generating synthetic data",
        "BEFORE collecting real data",
        "produces rows fitted to",
        "nothing — a distribution",
        "that exists nowhere.",
        "",
        "The generator refuses to",
        "pretend. With no real file",
        "it falls back to documented",
        "priors and says so loudly",
        "in its output.",
        "",
        "Every synthetic row is",
        "flagged, and training always",
        "reports real-only accuracy",
        "separately from combined.",
    ], 14.5, 25, INK)

    s.rect(60, TOP + 520, 1480, 130, fill=WHITE, stroke=INK, sw=2.5)
    s.text(84, TOP + 556, "FILLING THE RARE CLASSES HONESTLY", 16, "bold", INK)
    s.lines(84, TOP + 588, [
        "REPEAT and HINT only fire after a wrong answer, so a simulated population that mostly answers correctly under-produces both —",
        "synthetic sessions include deliberately struggling virtual learners to reach them, a scenario that genuinely triggers those actions.",
    ], 14.5, 23, MUTED)

    s.footnote("No label is ever edited after the fact. Rare classes are produced by scenarios that legitimately cause them.")
    return s, "04_data_pipeline"


# ===========================================================================
def d05_model():
    s = Svg(title="TinyML model architecture")
    s.header("TinyML model architecture",
             f"Two independent networks — {PARAMS:,} trainable parameters combined", BUILT, OK)

    per_net = PARAMS // 2
    p_in = N_FEATURES_MODEL * 32 + 32
    p_h1 = 32 * 16 + 16
    p_out = 16 * 3 + 3

    def dots_col(x, y, n, color, spacing=16):
        for i in range(n):
            s.circle(x, y + i * spacing, 6, fill=color, stroke=color)
        for i in range(3):
            s.circle(x, y + n * spacing + 7 + i * 8, 2.2, fill=color, stroke=color)

    LH = 240
    y0 = TOP + 30

    def net_col(col_x, label, color, tag):
        s.text(col_x, y0 - 12, label, 14.5, "bold", color)
        s.chip(col_x + 555, y0 - 30, f"{per_net} params", color, 11, 8, 20)

        def layer(x, w, title, sub, nodes, params=None):
            s.rect(x, y0, w, LH, fill=TINT[color], stroke=color, sw=2.5)
            s.text(x + w / 2, y0 + 30, title, 14.5, "bold", INK, "middle")
            s.text(x + w / 2, y0 + 50, sub, 11.5, "normal", MUTED, "middle")
            dots_col(x + w / 2, y0 + 78, nodes, color)
            if params:
                s.text(x + w / 2, y0 + LH - 14, params, 12, "bold", color, "middle")

        layer(col_x, 120, "IN", f"{N_FEATURES_MODEL} feat.", 5)
        s.arrow(col_x + 120 + 4, y0 + LH / 2, col_x + 160, y0 + LH / 2, color=LINE, sw=2.5)
        layer(col_x + 164, 175, "DENSE 32", "ReLU", 5, f"{p_in}p")
        s.arrow(col_x + 164 + 175 + 4, y0 + LH / 2, col_x + 347, y0 + LH / 2, color=LINE, sw=2.5)
        layer(col_x + 351, 160, "DENSE 16", "ReLU", 5, f"{p_h1}p")
        s.arrow(col_x + 351 + 160 + 4, y0 + LH / 2, col_x + 519, y0 + LH / 2, color=LINE, sw=2.5)
        layer(col_x + 523, 160, "DENSE 3", f"softmax · {tag}", 3, f"{p_out}p")

    net_col(60, "TEACHING-ACTION NETWORK (TA)", MODEL, "teaching")
    net_col(830, "CONFIDENCE-STATE NETWORK (CS)", APP, "confidence")

    s.text(60, y0 + LH + 34,
           "Same shape, trained independently — inputs are shared, weights are not. Both run on every attempt; neither depends on the other's output.",
           14.5, "normal", MUTED)

    # measured numbers, as a single horizontal strip
    my = y0 + LH + 66
    s.rect(60, my, 1480, 110, fill=WHITE, stroke=LINE, sw=2)
    stats = [
        ("Parameters (both nets)", f"{PARAMS:,}"),
        ("Exported as", "C float32 arrays"),
        ("On-device weight size", f"{TFLITE_B:,} B"),
        ("Teaching acc. (real)", f"{TEACH_ACC*100:.1f}%"),
        ("Confidence acc. (real)", f"{CONF_ACC*100:.1f}%"),
        ("Boot self-test", "20 / 20 match"),
        ("Inference time", "~0.1 ms, both"),
        ("Training time", "< 30 s, CPU"),
    ]
    for i, (k, v) in enumerate(stats):
        cx = 84 + (i % 4) * 365
        cy = my + 34 + (i // 4) * 52
        s.text(cx, cy, k, 12.5, "normal", MUTED)
        s.text(cx, cy + 22, v, 16, "bold", MODEL)

    # honesty band
    by = my + 130
    s.rect(60, by, 1480, 145, fill=TINT[WARN], stroke=WARN, sw=2.5)
    s.text(84, by + 36, "WHAT THIS MODEL ACTUALLY DOES — state this plainly in the report", 16.5, "bold", WARN)
    s.lines(84, by + 70, [
        f"The training labels are produced by a hand-written rule engine, so the networks learn to REPRODUCE that engine — measured at {TEACH_ACC*100:.1f}% / {CONF_ACC*100:.1f}% real-only agreement.",
        f"That is a real embedded-ML result: an adaptive teaching policy compressed into {PARAMS:,} parameters ({TFLITE_B/1024:.1f} KB) that run offline on a $4 microcontroller, no runtime library.",
        "It is not autonomous discovery of teaching strategy and must not be described that way. The interesting evidence is where the model disagrees with the engine.",
    ], 15, 26, INK)

    s.footnote("sklearn MLPClassifier, not TensorFlow (incompatible with Python 3.12 on Windows) — weights are exported directly as C arrays, no TFLite, no arena.")
    return s, "05_model_architecture"


# ===========================================================================
def d06_esp32_fit():
    s = Svg(title="ESP32 fit — memory, latency, offline")
    s.header("Does it fit on the ESP32?",
             "Memory, latency and offline operation — measured, not estimated", BUILT, OK)

    # memory -- no TFLite runtime, no tensor arena: inference.h allocates two
    # stack arrays (32 + 16 floats = 192 B) per forward pass and frees them
    # immediately, so the only persistent cost is the exported weights.
    SRAM_B = 520 * 1024
    STACK_B = 192
    used_b = TFLITE_B + STACK_B
    free_kb = (SRAM_B - used_b) / 1024
    pct = used_b / SRAM_B * 100

    s.rect(60, TOP, 940, 270, fill=WHITE, stroke=LINE, sw=2)
    s.text(84, TOP + 38, "SRAM USAGE — 520 KB available", 16, "bold", MUTED)
    bar_x, bar_y, bar_w, bar_h = 84, TOP + 66, 892, 62
    s.rect(bar_x, bar_y, bar_w, bar_h, fill="#F3F5F8", stroke=LINE, sw=2, r=8)
    used_w = bar_w * used_b / SRAM_B
    s.rect(bar_x, bar_y, max(used_w, 4), bar_h, fill=MODEL, stroke=MODEL, sw=0, r=8)
    s.text(bar_x + bar_w - 18, bar_y + 38, f"free  ·  {free_kb:.1f} KB", 16, "bold", MUTED, "end")
    s.legend(84, TOP + 162, [(f"Weights {TFLITE_B:,} B", MODEL), (f"Forward-pass stack {STACK_B} B", HW),
                             (f"Free {free_kb:.1f} KB", MUTED)])
    s.text(84, TOP + 218, "TOTAL USED", 14, "bold", MUTED)
    s.text(300, TOP + 224, f"{used_b/1024:.1f} KB   =   {pct:.1f}% of SRAM", 26, "bold", MODEL)

    # why offline
    s.rect(60, TOP + 300, 940, 350, fill=TINT[OK], stroke=OK, sw=2.5)
    s.text(84, TOP + 338, "WHY OFFLINE INFERENCE IS THE WHOLE POINT", 16.5, "bold", OK)
    reasons = [
        ("No internet needed", "Works in any classroom or village school, with no connectivity at all."),
        ("No recurring cost", "No server, no API bill, no subscription for the school to maintain."),
        ("Instant response", "Sub-millisecond decision — no round trip to a remote service."),
        ("Data stays local", "Learner records are written to an SD card, never uploaded."),
        ("Runs on batteries", "With the radio switched off, power is dominated by the motors."),
    ]
    for i, (t, d) in enumerate(reasons):
        y = TOP + 380 + i * 52
        s.circle(102, y - 5, 7, fill=OK, stroke=OK)
        s.text(124, y, t, 15, "bold", INK)
        s.text(330, y, d, 14.5, "normal", MUTED)

    # stat cards
    stats = [
        ("LATENCY", "~0.1 ms", "both networks",
         ["Two small dense nets, no", "runtime library. The audio", "prompt takes ~10,000x longer."], MODEL),
        ("FLASH", "~30 KB", "weights + firmware",
         ["The ESP32 has 4 MB.", "Ample room for the model,", "audio index and logs."], HW),
        ("NETWORK", "NONE", "fully offline",
         ["WiFi and Bluetooth are", "switched off in firmware.", "No cloud, no data leaves."], OK),
    ]
    for i, (label, big, sub, body, color) in enumerate(stats):
        y = TOP + i * 172
        s.rect(1030, y, 510, 156, fill=TINT[color], stroke=color, sw=2.5)
        s.text(1054, y + 36, label, 14, "bold", color)
        s.text(1054, y + 86, big, 40, "bold", INK)
        s.text(1054, y + 116, sub, 14, "normal", MUTED)
        s.lines(1256, y + 58, body, 13.5, 22, INK)

    s.footnote("20 golden test vectors from training are replayed on the device at boot — if the ESP32 disagrees with the desktop, it refuses to trust the model.")
    return s, "06_esp32_fit"


# ===========================================================================
def d07_deploy():
    s = Svg(title="Training to deployment")
    s.header("From CSV to a microcontroller",
             "Four automated steps — no hand-copied numbers anywhere", BUILT, OK)

    steps = [
        ("CSV dataset", [f"{DATA_REAL:,} real + {DATA_SYNTH:,} synth", "rows, audited"], DATA, "export_dataset.py"),
        ("sklearn MLP", [f"{PARAMS:,} parameters", "two heads trained on CPU"], MODEL, "train_and_export.py"),
        ("C float export", [f"{TFLITE_B:,} bytes", "direct, no TFLite"], MODEL, "same script"),
        ("ESP32 flash", ["model_weights.h", "compiled in, runs offline"], HW, "Arduino IDE"),
    ]
    gap = 30
    bw = (1480 - (len(steps) - 1) * gap) / len(steps)
    for i, (title, body, color, tool) in enumerate(steps):
        x = 60 + i * (bw + gap)
        s.rect(x, TOP + 20, bw, 210, fill=TINT[color], stroke=color, sw=2.5)
        s.circle(x + bw / 2, TOP + 62, 22, fill=color, stroke=color)
        s.text(x + bw / 2, TOP + 70, str(i + 1), 20, "bold", WHITE, "middle")
        s.text(x + bw / 2, TOP + 122, title, 18, "bold", INK, "middle")
        for j, ln in enumerate(body):
            s.text(x + bw / 2, TOP + 152 + j * 22, ln, 14, "normal", MUTED, "middle")
        s.text(x + bw / 2, TOP + 212, tool, 12.5, "bold", color, "middle")
        if i < len(steps) - 1:
            s.arrow(x + bw + 4, TOP + 125, x + bw + gap - 5, TOP + 125, color=LINE, sw=3)

    # safety net
    s.rect(60, TOP + 275, 740, 375, fill=TINT[OK], stroke=OK, sw=2.5)
    s.text(84, TOP + 313, "HOW WE KNOW THE DEVICE RUNS THE RIGHT MODEL", 16.5, "bold", OK)
    s.lines(84, TOP + 350, [
        "During training, 20 test cases (\"golden vectors\") are saved together",
        "with the answers the desktop computed for them. Those cases are",
        "compiled into the firmware itself.",
        "",
        "At every boot the ESP32 runs all 20 and compares the results.",
    ], 15.5, 27, INK)
    s.rect(84, TOP + 500, 330, 50, fill=WHITE, stroke=OK, sw=2, r=8)
    s.text(249, TOP + 531, "match  →  use the model", 15.5, "bold", OK, "middle")
    s.rect(438, TOP + 500, 338, 50, fill=WHITE, stroke=BAD, sw=2, r=8)
    s.text(607, TOP + 531, "mismatch  →  fall back to rules", 15.5, "bold", BAD, "middle")
    s.lines(84, TOP + 585, [
        "Without this check a stale or corrupted model would run silently, and every",
        "session recorded afterwards would be measuring an unknown function.",
    ], 14, 23, MUTED)

    # generated not copied
    s.rect(830, TOP + 275, 710, 375, fill=TINT[WARN], stroke=WARN, sw=2.5)
    s.text(854, TOP + 313, "ONE SOURCE OF TRUTH — NOTHING HAND-COPIED", 16.5, "bold", WARN)
    s.lines(854, TOP + 350, [
        "The teaching rules, the 14 feature definitions and the scaling",
        "ranges are written ONCE, then code-generated into three languages:",
    ], 15, 25, INK)
    for i, (lang, where) in enumerate([("JavaScript", "the web app"),
                                       ("C", "the ESP32 firmware"),
                                       ("Python", "training + synthetic data")]):
        y = TOP + 410 + i * 56
        s.rect(854, y, 250, 42, fill=WHITE, stroke=WARN, sw=1.5, r=21)
        s.text(979, y + 28, lang, 15, "bold", INK, "middle")
        s.text(1130, y + 28, "→   " + where, 15, "normal", MUTED)
    s.rect(854, TOP + 585, 660, 44, fill=WHITE, stroke=WARN, sw=2, r=8)
    s.text(1184, TOP + 613, "test_parity.py pushes 2,000 vectors through all three and proves they agree",
           14.5, "bold", WARN, "middle")

    s.footnote("This removes the failure where the browser and the device compute features slightly differently — invisible until integration, expensive to find then.")
    return s, "07_training_to_deployment"


# ===========================================================================
def d08_hardware():
    s = Svg(title="Hardware architecture")
    s.header("Hardware architecture",
             "Firmware complete; breadboard subset (buttons + speaker) wired — full motor/DFPlayer assembly pending",
             PLANNED, WARN)

    # MCU
    s.rect(600, TOP + 140, 400, 270, fill=TINT[HW], stroke=HW, sw=3)
    s.text(800, TOP + 190, "ESP32-WROOM-32", 23, "bold", INK, "middle")
    s.text(800, TOP + 218, "240 MHz dual core", 14.5, "normal", MUTED, "middle")
    s.text(800, TOP + 242, "520 KB SRAM  ·  4 MB flash", 14.5, "normal", MUTED, "middle")
    s.rect(650, TOP + 264, 300, 50, fill=WHITE, stroke=MODEL, sw=2, r=8)
    s.text(800, TOP + 295, f"Direct C inference  ·  {TFLITE_B:,} B", 14.5, "bold", MODEL, "middle")
    s.rect(650, TOP + 326, 300, 50, fill=WHITE, stroke=OK, sw=2, r=8)
    s.text(800, TOP + 357, "WiFi OFF  ·  Bluetooth OFF", 14.5, "bold", OK, "middle")

    periph = [
        (90, TOP, "DFPlayer Mini + speaker", "AUDIO OUT",
         ["Speaks the Bangla letter", "60 audio clips on microSD", "UART2  ·  GPIO 16, 17"]),
        (90, TOP + 285, "6 push buttons", "INPUT",
         ["One per Braille dot", "Perkins keyboard layout", "GPIO 32, 33, 25, 26, 27, 14"]),
        (1110, TOP, "6 coin vibration motors", "TACTILE OUT",
         ["Driven by a ULN2803A", "Built-in flyback diodes", "GPIO 13, 4, 21, 22, 2, 15"]),
        (1110, TOP + 285, "microSD card", "STORAGE",
         ["Logs every attempt as CSV", "Same columns as the web app", "SPI  ·  GPIO 18, 19, 23, 5"]),
    ]
    for x, y, title, tag, body in periph:
        s.rect(x, y, 400, 265, fill=WHITE, stroke=LINE, sw=2)
        s.text(x + 20, y + 40, title, 17.5, "bold", INK)
        s.chip(x + 20, y + 58, tag, HW, 12, 10, 24)
        s.lines(x + 20, y + 130, body, 14, 26, MUTED)

    s.arrow(495, TOP + 130, 595, TOP + 220, color=HW, sw=2.5)
    s.arrow(495, TOP + 410, 595, TOP + 330, color=HW, sw=2.5)
    s.arrow(1005, TOP + 220, 1105, TOP + 130, color=HW, sw=2.5)
    s.arrow(1005, TOP + 330, 1105, TOP + 410, color=HW, sw=2.5)

    s.rect(60, TOP + 580, 720, 165, fill=TINT[BAD], stroke=BAD, sw=2.5)
    s.text(84, TOP + 618, "POWER — the most common way this build fails", 16.5, "bold", BAD)
    s.lines(84, TOP + 652, [
        "6 motors ≈ 480 mA  +  ESP32 ≈ 80 mA  +  audio ≈ 200 mA   →   about 800 mA peak.",
        "",
        "Use a 5 V 2 A supply and a 1000 µF capacitor on the motor rail. A weak supply",
        "browns out the regulator and reboots the board — which looks exactly like a",
        "firmware crash, and is not one.",
    ], 14.5, 22, INK)

    s.rect(820, TOP + 580, 720, 165, fill=TINT[WARN], stroke=WARN, sw=2.5)
    s.text(844, TOP + 618, "USE A ULN2803A, NOT BARE TRANSISTORS", 16.5, "bold", WARN)
    s.lines(844, TOP + 652, [
        "Coin motors are inductive. Driving them from a GPIO pin, or from a transistor",
        "with no flyback path, destroys the pin.",
        "",
        "The ULN2803A packs 8 channels with the flyback diodes already inside.",
        "One chip, and tie its COM pin to +5 V.",
    ], 14.5, 22, INK)

    return s, "08_hardware_architecture"


# ===========================================================================
def d09_interaction():
    s = Svg(title="Real classroom interaction loop")
    s.header("How a student actually uses the device",
             "One practice cycle, from spoken prompt to adaptive response", PLANNED, WARN)

    boxes = [
        ("Speaker says a letter", ["The device speaks a", "Bangla letter aloud."], HW),
        ("Student feels the cell", ["Reads the raised Braille", "reference by touch."], HW),
        ("Student presses buttons", ["Enters the dot pattern", "they believe is correct."], SIM),
        ("Device scores it", ["Compares the entered", "pattern to the expected."], MODEL),
    ]
    bw = 320
    for i, (title, body, color) in enumerate(boxes):
        x = 60 + i * (bw + 28)
        s.rect(x, TOP, bw, 175, fill=TINT[color], stroke=color, sw=2.5)
        s.circle(x + 36, TOP + 44, 20, fill=color, stroke=color)
        s.text(x + 36, TOP + 51, str(i + 1), 18, "bold", WHITE, "middle")
        s.text(x + 68, TOP + 51, title, 16, "bold", INK)
        s.lines(x + 22, TOP + 96, body, 14.5, 24, MUTED)
        if i < 3:
            s.arrow(x + bw + 3, TOP + 87, x + bw + 24, TOP + 87, color=LINE, sw=3)

    # physical reference cell
    s.rect(1452, TOP, 88, 175, fill=WHITE, stroke=LINE, sw=2)
    s.text(1496, TOP + 28, "REFERENCE", 11, "bold", MUTED, "middle")
    s.braille_cell(1478, TOP + 62, [1, 3], dot_r=10, gap_x=36, gap_y=34)
    s.text(1496, TOP + 165, "raised cell", 11, "normal", MUTED, "middle")

    s.text(60, TOP + 232, "THE MODEL DECIDES WHAT HAPPENS NEXT", 18, "bold", INK)
    s.text(60, TOP + 258, "14 features go in, a teaching action comes out — in under a millisecond, with no internet connection.",
           15, "normal", MUTED)

    # correct
    s.rect(60, TOP + 285, 720, 365, fill=TINT[OK], stroke=OK, sw=2.5)
    s.text(84, TOP + 323, "IF THE ANSWER IS CORRECT", 16.5, "bold", OK)
    corr = [
        ("Audio", "সঠিক", "— \"correct\" is spoken"),
        ("Motors", None, "all six buzz briefly as a reward"),
        ("Model", None, "mastery rises, correct streak increases"),
        ("Next", None, "a harder letter, or move on to word practice"),
    ]
    for i, (k, bn, v) in enumerate(corr):
        y = TOP + 360 + i * 68
        s.rect(84, y, 122, 40, fill=WHITE, stroke=OK, sw=1.5, r=20)
        s.text(145, y + 27, k, 14, "bold", OK, "middle")
        if bn:
            s.text(226, y + 27, bn, 17, "bold", INK, font=FONT_BN)
            s.text(300, y + 27, v, 15, "normal", INK)
        else:
            s.text(226, y + 27, v, 15, "normal", INK)

    # wrong
    s.rect(820, TOP + 285, 720, 365, fill=TINT[BAD], stroke=BAD, sw=2.5)
    s.text(844, TOP + 323, "IF THE ANSWER IS WRONG", 16.5, "bold", BAD)
    wrong = [
        ("Audio", "ভুল", "— then the letter is spoken again"),
        ("Motors", None, "the CORRECT dots buzz one at a time"),
        ("Model", None, "mastery falls, wrong streak increases"),
        ("Next", None, "the engine picks: repeat, or a hint"),
    ]
    for i, (k, bn, v) in enumerate(wrong):
        y = TOP + 360 + i * 68
        s.rect(844, y, 122, 40, fill=WHITE, stroke=BAD, sw=1.5, r=20)
        s.text(905, y + 27, k, 14, "bold", BAD, "middle")
        if bn:
            s.text(986, y + 27, bn, 17, "bold", INK, font=FONT_BN)
            s.text(1040, y + 27, v, 15, "normal", INK)
        else:
            s.text(986, y + 27, v, 15, "normal", INK)

    s.footnote("Feeling the correct pattern immediately after a mistake is the core teaching mechanism — the motors let a learner check their own answer by touch.")
    return s, "09_classroom_interaction"


# ===========================================================================
def d10_actions():
    s = Svg(title="Teaching actions and their origin")
    s.header("The three teaching actions, and where they come from",
             "Ordered rules, first match wins — written explicitly, then learned by the network", BUILT, OK)

    actions = [
        ("1", "REPEAT",
         ["First wrong attempt on this", "prompt — just try again,", "no help yet."],
         ["wrong_streak >= 1  AND", "retry_count == 0"], BAD),
        ("2", "HINT",
         ["Still wrong after retrying —", "keep helping on THIS character", "every subsequent wrong try."],
         ["wrong_streak >= 1", "(rule 1 already caught retry==0)"], WARN),
        ("3", "NORMAL_PRACTICE",
         ["wrong_streak == 0, so the", "attempt just scored was", "correct — move on normally."],
         ["default — no conditions,", "falls through otherwise"], OK),
    ]
    bw, gap = 460, 40
    for i, (order, name, why, rule, color) in enumerate(actions):
        x = 60 + i * (bw + gap)
        s.rect(x, TOP, bw, 250, fill=TINT[color], stroke=color, sw=2.5)
        s.circle(x + 34, TOP + 40, 18, fill=color, stroke=color)
        s.text(x + 34, TOP + 46, order, 16, "bold", WHITE, "middle")
        s.text(x + 66, TOP + 46, name, 19, "bold", INK)
        s.lines(x + 20, TOP + 90, why, 14, 22, MUTED)
        s.rect(x + 20, TOP + 172, bw - 40, 58, fill=WHITE, stroke=color, sw=1.5, r=10)
        s.lines(x + 32, TOP + 197, rule, 13, 21, color, weight="bold")

    s.text(60, TOP + 278, "Retired in spec v2: INCREASE_DIFFICULTY, REVIEW_PREVIOUS and WORD_PRACTICE — abandoning the current letter mid-struggle taught nothing about the letter the learner actually needed.",
           13.5, "normal", MUTED, italic=True)

    y = TOP + 320
    s.rect(60, y, 1480, 152, fill=WHITE, stroke=INK, sw=2.5)
    s.text(84, y + 38, "WHERE THESE DECISIONS COME FROM", 16.5, "bold", INK)
    s.circle(100, y + 74, 13, fill=SIM, stroke=SIM)
    s.text(100, y + 79, "1", 14, "bold", WHITE, "middle")
    s.text(126, y + 79, "The rules are hand-written from teaching principles (spec/engine_spec.json), and applied live while data is collected.", 15, "normal", INK)
    s.circle(100, y + 112, 13, fill=MODEL, stroke=MODEL)
    s.text(100, y + 117, "2", 14, "bold", WHITE, "middle")
    s.text(126, y + 117, f"The TA network is trained on those decisions and reproduces them at {TEACH_ACC*100:.1f}% real-only — small enough to run on the ESP32.", 15, "normal", INK)

    # worked example -- one learner drilling one letter, attempt by attempt
    wy = y + 172
    s.rect(60, wy, 1480, 148, fill=WHITE, stroke=LINE, sw=2)
    s.text(84, wy + 32, "WORKED EXAMPLE — one learner, one letter, four attempts in a row", 16, "bold", INK)
    example = [
        ("Attempt 1", "wrong", "wrong_streak=1, retry_count=0", "REPEAT", BAD),
        ("Attempt 2", "wrong (retry)", "wrong_streak=2, retry_count=1", "HINT", WARN),
        ("Attempt 3", "wrong (retry)", "wrong_streak=3, retry_count=2", "HINT", WARN),
        ("Attempt 4", "correct", "wrong_streak=0, current_streak=1", "NORMAL_PRACTICE", OK),
    ]
    bw2, gap2 = 335, 25
    for i, (label, result, state, action, color) in enumerate(example):
        x = 84 + i * (bw2 + gap2)
        s.rect(x, wy + 48, bw2, 88, fill=TINT[color], stroke=color, sw=2, r=10)
        s.text(x + 16, wy + 70, f"{label} — {result}", 14, "bold", INK)
        s.text(x + 16, wy + 92, state, 12, "normal", MUTED)
        s.rect(x + 16, wy + 100, bw2 - 32, 28, fill=WHITE, stroke=color, sw=1.5, r=14)
        s.text(x + bw2 / 2, wy + 119, action, 13, "bold", color, "middle")
        if i < len(example) - 1:
            s.arrow(x + bw2 + 3, wy + 92, x + bw2 + gap2 - 4, wy + 92, color=LINE, sw=2.5)

    s.footnote(f"The model does not invent teaching strategy. It compresses an explicit policy into a {PARAMS//2}-parameter network so it can run offline on a microcontroller.")
    return s, "10_teaching_actions"


# ===========================================================================
def d11_mobile():
    s = Svg(title="Teacher mobile app")
    s.header("Teacher app — turning sessions into insight",
             "Every student has a profile; the teacher sees progress, not raw rows",
             PLANNED, WARN)

    # phone
    px, py, pw, ph = 90, TOP, 330, 650
    s.rect(px, py, pw, ph, fill=WHITE, stroke=INK, sw=3, r=32)
    s.rect(px + 22, py + 45, pw - 44, ph - 68, fill=WHITE, stroke=LINE, sw=1.5, r=8)
    s.circle(px + 165, py + 24, 6, fill=LINE, stroke=LINE)

    s.text(px + 44, py + 82, "রাহিম", 19, "bold", INK, font=FONT_BN)
    s.text(px + 110, py + 82, "·  Class 4", 15, "normal", MUTED)
    s.text(px + 44, py + 106, "42 sessions  ·  18 distinct days", 12.5, "normal", MUTED)

    s.rect(px + 44, py + 122, 242, 78, fill=TINT[OK], stroke=OK, sw=1.5, r=8)
    s.text(px + 60, py + 150, "MASTERY", 11.5, "bold", OK)
    s.text(px + 60, py + 182, "31 / 50 letters", 21, "bold", INK)

    s.text(px + 44, py + 232, "LEARNING CURVE", 11.5, "bold", MUTED)
    pts = [(0, 60), (1, 53), (2, 47), (3, 40), (4, 31), (5, 26), (6, 19), (7, 14)]
    path = " ".join(f"{'M' if i == 0 else 'L'} {px + 44 + p[0]*34} {py + 330 - (60-p[1])*1.25}"
                    for i, p in enumerate(pts))
    s.path(path, stroke=SIM, sw=3, marker=False)
    for p in pts:
        s.circle(px + 44 + p[0] * 34, py + 330 - (60 - p[1]) * 1.25, 4, fill=SIM, stroke=SIM)
    s.line(px + 44, py + 338, px + 286, py + 338, stroke=LINE, sw=1.5)
    s.text(px + 44, py + 358, "response time falling over 8 weeks", 11, "normal", MUTED)

    s.rect(px + 44, py + 374, 242, 68, fill=TINT[BAD], stroke=BAD, sw=1.5, r=8)
    s.text(px + 60, py + 400, "NEEDS ATTENTION", 11.5, "bold", BAD)
    s.text(px + 60, py + 428, "ঝ    ণ    ঢ", 18, "bold", INK, font=FONT_BN)
    s.text(px + 160, py + 428, "40% accuracy", 12.5, "normal", MUTED)

    s.rect(px + 44, py + 456, 242, 74, fill=TINT[MODEL], stroke=MODEL, sw=1.5, r=8)
    s.text(px + 60, py + 482, "AI SUGGESTION", 11.5, "bold", MODEL)
    s.text(px + 60, py + 506, "Revisit ঝ before", 12.5, "normal", INK, font=FONT_BN)
    s.text(px + 60, py + 524, "introducing new letters", 12.5, "normal", INK)

    s.rect(px + 44, py + 544, 242, 58, fill=WHITE, stroke=LINE, sw=1.5, r=8)
    s.text(px + 60, py + 568, "LAST PRACTISED", 11.5, "bold", MUTED)
    s.text(px + 60, py + 590, "2 days ago", 13.5, "bold", INK)

    feats = [
        ("Student profiles", ["One profile per learner, built entirely",
                              "from their own session history."], APP),
        ("Learning curve", ["Accuracy and response time over weeks —",
                            "is this child actually improving?"], SIM),
        ("Weak characters", ["Which letters are failing, ranked, so",
                             "teaching time goes where it counts."], BAD),
        ("Confidence trend", ["Confident / hesitant / guessing over time.",
                              "Catches guessing before it becomes habit."], WARN),
        ("AI suggestions", ["The model's recommended next action,",
                            "written in plain language for the teacher."], MODEL),
        ("Class overview", ["Every student at a glance — spot who has",
                            "not practised at all this week."], OK),
    ]
    for i, (t, body, color) in enumerate(feats):
        x = 470 + (i % 2) * 545
        y = TOP + (i // 3) * 0 + (i % 3) * 0
        col, row = i % 2, i // 2
        x = 470 + col * 545
        y = TOP + row * 222
        s.rect(x, y, 520, 196, fill=TINT[color], stroke=color, sw=2.5)
        s.text(x + 22, y + 42, t, 18, "bold", INK)
        s.lines(x + 22, y + 80, body, 14.5, 24, MUTED)
        s.badge(x + 498, y + 150, PLANNED, WARN)

    s.footnote("Data reaches the app either from the device's SD card or from the same database the web app already writes to — no new pipeline is needed.")
    return s, "11_teacher_mobile_app"


# ===========================================================================
def d12_status():
    s = Svg(title="Project status and roadmap")
    s.header("Where the project stands today",
             "Honest status of every stage — data collection and verification are now done")

    # (text, is_continuation) -- a continuation line is indented and gets no
    # bullet. Deciding that from the text itself proved unreliable.
    B, C, GAP = "bullet", "cont", None
    cols = [
        ("BUILT AND TESTED", OK, [
            (B, "Web simulation app"),
            (B, "Supabase database and schema"),
            (B, "Rule engine in three languages"),
            (B, "Synthetic data generator"),
            (B, f"Real data collected — {DATA_REAL:,} rows"),
            (B, "Model trained on real + synthetic"),
            (C, f"{TEACH_ACC*100:.1f}% / {CONF_ACC*100:.1f}% real-only acc."),
            (B, f"Braille map — {N_VERIFIED} of {N_TOTAL_LETTERS} verified"),
            (B, "ESP32 firmware (written)"),
            (B, "Six hardware bring-up sketches"),
            (B, "Automated test suites"),
            (B, "Braille image importer"),
        ]),
        ("PARTLY DONE", WARN, [
            (B, "Physical assembly — breadboard"),
            (C, "subset only: buttons + speaker."),
            (C, "Motors, DFPlayer, full wiring"),
            (C, "not yet assembled"),
            (GAP, ""),
            (B, "Audio: 60 clips generated by"),
            (C, "speech synthesis (espeak-ng) —"),
            (C, "usable now, should be re-recorded"),
            (C, "by a human speaker before a demo"),
        ]),
        ("PLANNED", BAD, [
            (B, "Full physical hardware assembly"),
            (C, "— wiring all 6 motors + DFPlayer"),
            (GAP, ""),
            (B, "Teacher mobile app"),
            (C, "(web teacher panel exists; a"),
            (C, "dedicated mobile app does not)"),
            (GAP, ""),
            (B, "Human-recorded audio"),
            (C, "to replace synthetic speech"),
        ]),
    ]
    for i, (title, color, items) in enumerate(cols):
        x = 60 + i * 500
        s.rect(x, TOP, 460, 450, fill=TINT[color], stroke=color, sw=2.5)
        s.text(x + 22, TOP + 40, title, 16.5, "bold", color)
        for row, (kind, txt) in enumerate(items):
            if kind is GAP:
                continue
            prefix, indent = ("•  ", 0) if kind == B else ("", 20)
            s.text(x + 22 + indent, TOP + 82 + row * 30, prefix + txt, 13.5, "normal", INK)

    s.rect(60, TOP + 480, 1480, 170, fill=WHITE, stroke=INK, sw=2.5)
    s.text(84, TOP + 518, "THE CRITICAL PATH NOW", 17, "bold", INK)
    s.lines(84, TOP + 554, [
        f"The hard, calendar-bound work is done: {DATA_REAL:,} real rows across 4 volunteers, all {N_TOTAL_LETTERS} Braille letters verified against the Bangladesh standard, and the",
        f"model retrained to {TEACH_ACC*100:.1f}% / {CONF_ACC*100:.1f}% real-only accuracy. What is left is assembly and production work, not research risk.",
        "",
        "Remaining: solder the full motor + DFPlayer wiring onto the breadboard subset, re-record audio with a human voice, and build the teacher mobile app.",
    ], 15.5, 27, INK)

    return s, "12_status_and_roadmap"


# ===========================================================================
def d13_literature():
    s = Svg(title="Comparison with prior work")
    s.header("Where this project sits against prior work",
             "Three published Braille-learning devices, and what each one leaves undone")

    rows = [
        ("Kader et al. (2018)", "Self-Learning Braille Kit",
         "6 actuators + audio; learning and practice modes.",
         "Costly. No ML/AI — teaching is not adaptive.", MUTED),
        ("Saikot & Sanim (2022)", "Refreshable Braille Display",
         "Single-cell, 6 actuators, adjustable spacing, speech.",
         "Expensive. No practice mode. No ML/AI.", MUTED),
        ("Ma, Lai & Luo (2025)", "BrailleRhythm",
         "Pressure-sensor sheet over Braille cards, real-time audio.",
         "Not Bangla-focused. Doesn't test answers, retries or teach adaptively.", MUTED),
        ("This project", "Bangla Braille Tutor",
         "6-motor + audio haptic teaching, offline on a $4 ESP32.",
         f"ML-driven teaching action + confidence classification ({TEACH_ACC*100:.1f}%/{CONF_ACC*100:.1f}% real-only). {DATA_REAL:,} real learner rows collected.", OK),
    ]

    col_x = [60, 330, 610, 1080]
    col_w = [260, 270, 460, 460]
    headers = ["WORK", "APPROACH", "WHAT IT DOES", "GAP / WHAT'S DIFFERENT HERE"]
    hy = TOP
    for cx, cw, h in zip(col_x, col_w, headers):
        s.text(cx, hy, h, 12.5, "bold", MUTED)
    s.line(60, hy + 14, 1540, hy + 14, stroke=LINE, sw=1.5)

    row_h = 140
    for i, (name, product, does, gap, accent) in enumerate(rows):
        y = TOP + 34 + i * row_h
        color = OK if i == len(rows) - 1 else LINE
        fill = TINT[OK] if i == len(rows) - 1 else WHITE
        s.rect(60, y, 1480, row_h - 14, fill=fill, stroke=color, sw=2.5 if i == len(rows) - 1 else 1.5)
        s.text(col_x[0] + 20, y + 34, name, 15, "bold", INK)
        s.text(col_x[1] + 6, y + 34, product, 14, "bold", (OK if i == len(rows) - 1 else MUTED))
        s.lines(col_x[2] + 6, y + 30, _wrap(does, 44), 13.5, 20, INK)
        s.lines(col_x[3] + 6, y + 30, _wrap(gap, 46), 13.5, 20, (OK if i == len(rows) - 1 else BAD) if i < len(rows) - 1 else INK)

    s.footnote("Gaps for prior work are as reported by their own authors; this row's figures are measured from the current build (see 05_model_architecture, 06_esp32_fit).")
    return s, "13_literature_comparison"


def _wrap(text, width):
    """Greedy word-wrap for the small text-table cells above."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# ===========================================================================
def d14_bom_cost():
    s = Svg(title="Bill of materials and estimated cost")
    s.header("Bill of materials — estimated cost",
             "Retail estimates for Bangladesh, BDT and USD — approximate, not vendor quotes", BUILT, OK)

    BDT_PER_USD = 118  # approximate, for scale only -- not a live exchange rate
    items = [
        ("ESP32-WROOM-32 dev board", 1, 450),
        ("DFPlayer Mini + 3 W speaker", 1, 260),
        ("ULN2803A driver IC", 1, 25),
        ("Coin vibration motors", 6, 30),
        ("Tactile buttons (6 dot + 1 submit)", 7, 5),
        ("microSD module", 1, 90),
        ("5 V 2 A power supply", 1, 150),
        ("1000 µF capacitor", 1, 10),
        ("Resistors (6×1kΩ + 3×10kΩ)", 9, 1),
        ("DS3231 RTC (optional)", 1, 120),
    ]

    hy = TOP
    headers = ["COMPONENT", "QTY", "UNIT (BDT)", "SUBTOTAL (BDT)", "SUBTOTAL (USD)"]
    hx = [60, 780, 900, 1080, 1300]
    for x, h in zip(hx, headers):
        s.text(x, hy, h, 12.5, "bold", MUTED)
    s.line(60, hy + 14, 1540, hy + 14, stroke=LINE, sw=1.5)

    row_h = 34
    total_bdt = 0
    total_bdt_no_rtc = 0
    for i, (name, qty, unit_bdt) in enumerate(items):
        y = TOP + 40 + i * row_h
        sub = qty * unit_bdt
        total_bdt += sub
        if "RTC" not in name:
            total_bdt_no_rtc += sub
        if i % 2 == 0:
            s.rect(60, y - 22, 1480, row_h, fill="#FAFBFC", stroke="none", sw=0)
        s.text(hx[0], y, name, 14, "normal", INK)
        s.text(hx[1] + 20, y, str(qty), 14, "normal", MUTED, "middle")
        s.text(hx[2] + 40, y, f"{unit_bdt:,}", 14, "normal", MUTED, "middle")
        s.text(hx[3] + 50, y, f"{sub:,}", 14, "bold", INK, "middle")
        s.text(hx[4] + 40, y, f"${sub / BDT_PER_USD:.2f}", 14, "normal", MUTED, "middle")

    ty = TOP + 40 + len(items) * row_h + 12
    s.line(60, ty - 20, 1540, ty - 20, stroke=INK, sw=2)
    s.text(hx[0], ty, "TOTAL (core build, no RTC)", 15, "bold", INK)
    s.text(hx[3] + 50, ty, f"{total_bdt_no_rtc:,} BDT", 15.5, "bold", MODEL, "middle")
    s.text(hx[4] + 40, ty, f"≈ ${total_bdt_no_rtc / BDT_PER_USD:.2f}", 14.5, "bold", MODEL, "middle")
    s.text(hx[0], ty + 34, "TOTAL (with optional DS3231 RTC)", 15, "bold", INK)
    s.text(hx[3] + 50, ty + 34, f"{total_bdt:,} BDT", 15.5, "bold", MODEL, "middle")
    s.text(hx[4] + 40, ty + 34, f"≈ ${total_bdt / BDT_PER_USD:.2f}", 14.5, "bold", MODEL, "middle")

    by = ty + 90
    s.rect(60, by, 1480, 130, fill=TINT[WARN], stroke=WARN, sw=2.5)
    s.text(84, by + 34, "THESE ARE ESTIMATES, NOT QUOTES", 15.5, "bold", WARN)
    s.lines(84, by + 66, [
        f"Unit prices are approximate current Bangladeshi retail/hobbyist-market figures (≈{BDT_PER_USD} BDT/USD used for scale only) — they move with",
        "vendor, quantity and import duty, and are not claimed to be precise to the taka. Get current quotes before ordering for a build.",
    ], 14, 22, INK)

    s.footnote("Matches the component list in README.md 'Hardware'. Excludes wire, solder, enclosure and shipping.")
    return s, "14_bom_cost"


# ===========================================================================
def d15_teaching_flow():
    s = Svg(title="Teaching action and confidence decision flow")
    s.header("How wrong_streak and retries drive the two decisions",
             "Exact thresholds from spec/engine_spec.json — first match wins, top to bottom", BUILT, OK)

    # svgkit has no centered multi-line text primitive, so diamonds use this.
    def centered(cx, cy, lines, color, size=13):
        n = len(lines)
        for i, ln in enumerate(lines):
            s.text(cx, cy - (n - 1) * 8 + i * 16, ln, size, "bold", color, "middle")

    def diamond(cx, cy, w, h, text, color):
        s.path(f"M {cx} {cy-h} L {cx+w} {cy} L {cx} {cy+h} L {cx-w} {cy} Z",
               stroke=color, sw=2.5, fill=TINT[MUTED], marker=False)
        centered(cx, cy, text, INK, 12.5)

    def varrow(x, y1, y2, text):
        # a plain vertical arrow with its yes/no label offset to the side --
        # centering the label ON the line put it right on the diamond's
        # sharp bottom vertex, which pierced the text.
        s.arrow(x, y1, x, y2, color=LINE, sw=2.5)
        s.text(x + 14, (y1 + y2) / 2 + 5, text, 12.5, "bold", MUTED)

    # ---- left: teaching action ----
    lx = 430
    s.text(lx, TOP - 4, "TEACHING ACTION  (from wrong_streak, retry_count)", 14.5, "bold", MODEL, "middle")
    s.rect(lx - 110, TOP + 20, 220, 46, fill=WHITE, stroke=INK, sw=2, r=23)
    s.text(lx, TOP + 48, "attempt just scored", 14, "bold", INK, "middle")
    s.arrow(lx, TOP + 66, lx, TOP + 104, color=LINE, sw=2.5)
    diamond(lx, TOP + 150, 150, 46, ["wrong_streak >= 1 ?"], INK)
    varrow(lx, TOP + 196, TOP + 234, "no")
    s.rect(lx - 130, TOP + 234, 260, 56, fill=TINT[OK], stroke=OK, sw=2.5, r=10)
    centered(lx, TOP + 264, ["NORMAL_PRACTICE"], OK, 15)
    s.arrow(lx + 150, TOP + 150, lx + 230, TOP + 150, color=LINE, sw=2.5, label="yes")
    diamond(lx + 380, TOP + 150, 140, 46, ["retry_count == 0 ?"], INK)
    varrow(lx + 380, TOP + 196, TOP + 234, "yes")
    s.rect(lx + 250, TOP + 234, 260, 56, fill=TINT[BAD], stroke=BAD, sw=2.5, r=10)
    centered(lx + 380, TOP + 264, ["REPEAT"], BAD, 15)
    s.arrow(lx + 520, TOP + 150, lx + 646, TOP + 150, color=LINE, sw=2.5, label="no")
    s.rect(lx + 650, TOP + 122, 260, 56, fill=TINT[WARN], stroke=WARN, sw=2.5, r=10)
    centered(lx + 780, TOP + 152, ["HINT"], WARN, 15)

    # ---- right, lower band: confidence state ----
    cy0 = TOP + 380
    s.text(lx, cy0 - 24, "CONFIDENCE STATE  (from retries, response_time, press_duration, wrong_streak)",
           14.5, "bold", APP, "middle")
    diamond(lx, cy0 + 30, 190, 50, ["retry_count>=2  OR", "response_time>=6000ms ?"], INK)
    varrow(lx, cy0 + 80, cy0 + 118, "yes")
    s.rect(lx - 130, cy0 + 118, 260, 56, fill=TINT[BAD], stroke=BAD, sw=2.5, r=10)
    centered(lx, cy0 + 148, ["GUESSING"], BAD, 15)
    s.arrow(lx + 190, cy0 + 30, lx + 260, cy0 + 30, color=LINE, sw=2.5, label="no")
    diamond(lx + 470, cy0 + 30, 210, 60,
            ["response_time<=2500  AND  retry==0", "AND wrong_streak==0 AND press<=400ms ?"], INK)
    varrow(lx + 470, cy0 + 90, cy0 + 128, "yes")
    s.rect(lx + 340, cy0 + 128, 260, 56, fill=TINT[OK], stroke=OK, sw=2.5, r=10)
    centered(lx + 470, cy0 + 158, ["CONFIDENT"], OK, 15)
    s.arrow(lx + 680, cy0 + 30, lx + 760, cy0 + 30, color=LINE, sw=2.5, label="no")
    s.rect(lx + 760, cy0 + 2, 260, 56, fill=TINT[WARN], stroke=WARN, sw=2.5, r=10)
    centered(lx + 890, cy0 + 32, ["HESITANT (default)"], WARN, 14)

    s.footnote("Both decisions run independently on the same attempt — a GUESSING confidence state and a REPEAT action can, and often do, fire together.")
    return s, "15_teaching_actions_flow"


# ===========================================================================
def d16_remote_dataflow():
    s = Svg(title="Teacher-panel remote mode data flow")
    s.header("Remote / cloud-connected mode — how data moves",
             "No direct browser-to-ESP32 link — everything relays through two polled Supabase tables", BUILT, OK)

    lanes = [(140, "TEACHER PANEL", APP), (800, "SUPABASE", DATA), (1400, "ESP32 (WiFi mode)", HW)]
    for x, label, color in lanes:
        s.text(x, TOP, label, 15, "bold", color, "middle")
        s.line(x, TOP + 16, x, TOP + 50 + 7 * 70 + 20, stroke=LINE, sw=1.5, dash="4 6")

    steps = [
        (140, "Teacher selects letters,", "clicks Start", APP),
        (800, "INSERT remote_commands", "{device_id, letter_id, command, test_index, test_total}", DATA),
        (1400, "polled every ~250 ms;", "plays audio (+ vibration in Learn mode)", HW),
        (1400, "waits for the physical dot", "buttons + SUBMIT — no web input path", HW),
        (800, "INSERT attempts", "{char_id, entered/expected pattern, is_correct, response_time,", DATA),
        (800, "", "retry_count, teaching_action, confidence_state, source: esp32}", DATA),
        (140, "polled every ~200 ms;", "shows the result live, sends the next letter", APP),
        (800, "after the last letter: INSERT", "test_sessions + student_weaknesses", DATA),
    ]
    y = TOP + 50
    for x, l1, l2, color in steps:
        s.circle(x, y, 5, fill=color, stroke=color)
        s.text(x + 24 if x != 1400 else x - 24, y - 4, l1, 13.5, "bold", INK,
                "start" if x != 1400 else "end")
        if l2:
            s.text(x + 24 if x != 1400 else x - 24, y + 16, l2, 12, "normal", MUTED,
                    "start" if x != 1400 else "end")
        y += 70
    y -= 70  # step back to the last drawn row's y, not the post-loop cursor

    s.text(60, y + 26, "test_index / test_total on remote_commands are only set for command: \"test\" rows — that's how the ESP32 knows its", 12.5, "normal", MUTED)
    s.text(60, y + 46, "position in the teacher's batch and when to print the final score to Serial.", 12.5, "normal", MUTED)

    s.footnote("Verbatim sequence from README.md 'How data moves'. Only one of t10_learning / t11_testing / t11_ml_test is flashed at a time.")
    return s, "16_data_flow_remote_mode"


def _find_edge():
    import shutil as _sh
    for c in [_sh.which("msedge"), _sh.which("msedge.exe"),
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]:
        if c and Path(c).exists():
            return c
    return None


def _svg_to_png(svg_path, png_path, scale=1.5, timeout=25):
    """cairosvg if it's importable and has a working native cairo (Linux/mac
    CI); otherwise headless MS Edge (Windows dev boxes, no cairo needed)."""
    svg_path, png_path = Path(svg_path), Path(png_path)
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path),
                         output_width=int(W * scale), output_height=int(H * scale),
                         background_color="white")
        return True
    except Exception:
        pass

    edge = _find_edge()
    if not edge:
        return False
    import subprocess
    import time
    if png_path.exists():
        png_path.unlink()
    url = "file:///" + str(svg_path.resolve()).replace("\\", "/").replace(" ", "%20")
    subprocess.run(
        [edge, "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--force-device-scale-factor={scale}", f"--screenshot={png_path}",
         f"--window-size={W},{H}", url],
        capture_output=True, timeout=timeout)
    # --screenshot can return before the async write lands on disk.
    deadline = time.time() + timeout
    while time.time() < deadline and not png_path.exists():
        time.sleep(0.25)
    return png_path.exists()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    builders = [d01_overview, d02_simulation, d03_features, d04_data_pipeline,
                d05_model, d06_esp32_fit, d07_deploy, d08_hardware,
                d09_interaction, d10_actions, d11_mobile, d12_status]
    if INCLUDE_EXTRA:
        builders += [d13_literature, d14_bom_cost, d15_teaching_flow, d16_remote_dataflow]

    made = []
    for b in builders:
        svg, name = b()
        svg.save(OUT / f"{name}.svg")
        made.append(name)

    ok, failed = [], []
    for name in made:
        if _svg_to_png(OUT / f"{name}.svg", OUT / f"{name}.png"):
            ok.append(name)
        else:
            failed.append(name)
    extra = "  + PNG at 2400x1350" if ok else "  (no SVG->PNG renderer available -- SVG only)"
    if failed:
        extra += f"  [{len(failed)} PNG(s) failed: {', '.join(failed)}]"

    print(f"wrote {len(made)} diagram(s) to {OUT}/{extra}")
    for name in made:
        print(f"  {name}")
    print("\nAll on a pure white background.")
    print("SVG is fully editable: in PowerPoint use Insert > Picture, then")
    print("right-click > Convert to Shape to edit every box and label.")


if __name__ == "__main__":
    main()
