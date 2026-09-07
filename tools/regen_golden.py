#!/usr/bin/env python3
"""Recompute the expected outputs in models/golden_vectors.json from
models/model.tflite, without retraining.

    python3 tools/regen_golden.py

Why this exists: train.py used to match tflite outputs to heads by class count.
Once both heads became the same width that test matched one output twice, so
every vector's expect_teaching was written with the *confidence* head's
prediction. The weights were never wrong -- only the labels train.py recorded
next to them. Retraining would fix it too, but that needs TensorFlow and would
produce a different model than the one already validated, so this rewrites just
the labels using the same feature rows and the same flatbuffer that ships to the
device. It needs only the LiteRT runtime.

The golden vectors exist so the ESP32 can prove it computes what the desktop
computes. Recomputing them from the deployed flatbuffer is exactly that
reference. It does NOT re-check the model against Keras -- rerun tools/train.py
for that (metrics.json's tflite_vs_keras_teaching is stale until you do).
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import rule_engine_gen as engine  # noqa: E402
import tflite_heads  # noqa: E402

GOLDEN = ROOT / "models" / "golden_vectors.json"
TFLITE = ROOT / "models" / "model.tflite"


def load_interpreter(path):
    try:
        from ai_edge_litert.interpreter import Interpreter
    except ImportError:
        from tensorflow.lite import Interpreter
    interp = Interpreter(model_path=str(path))
    interp.allocate_tensors()
    return interp


def main():
    if not TFLITE.exists():
        sys.exit(f"{TFLITE.relative_to(ROOT)} not found -- run tools/train.py first")
    if not GOLDEN.exists():
        sys.exit(f"{GOLDEN.relative_to(ROOT)} not found -- run tools/train.py first")

    doc = json.loads(GOLDEN.read_text(encoding="utf-8"))
    vectors = doc.get("vectors", [])
    if not vectors:
        sys.exit("golden_vectors.json holds no vectors")

    interp = load_interpreter(TFLITE)
    in_det = interp.get_input_details()[0]
    in_scale, in_zp = in_det["quantization"]
    heads = tflite_heads.resolve_heads(interp,
                                       len(engine.CONFIDENCE_STATE_NAMES),
                                       len(engine.TEACHING_ACTION_NAMES))
    print(f"heads: teaching -> output({heads['teaching']['output_pos']}) "
          f"tensor {heads['teaching']['tensor_index']}, "
          f"confidence -> output({heads['confidence']['output_pos']}) "
          f"tensor {heads['confidence']['tensor_index']}")

    changed = 0
    for v in vectors:
        x = np.array(v["features_norm"], dtype=np.float32)
        if x.size != engine.FEATURE_COUNT:
            sys.exit(f"vector has {x.size} features, engine expects "
                     f"{engine.FEATURE_COUNT} -- rerun tools/train.py")
        q = np.clip(np.round(x / in_scale + in_zp), -128, 127).astype(np.int8)
        interp.set_tensor(in_det["index"], q.reshape(1, -1))
        interp.invoke()
        ta = int(np.argmax(interp.get_tensor(heads["teaching"]["tensor_index"])[0]))
        cs = int(np.argmax(interp.get_tensor(heads["confidence"]["tensor_index"])[0]))
        if v.get("expect_teaching") != ta or v.get("expect_confidence") != cs:
            changed += 1
        v["expect_teaching"] = ta
        v["expect_confidence"] = cs

    doc["quantization"] = {"input_scale": float(in_scale), "input_zero_point": int(in_zp)}
    doc["heads"] = heads
    GOLDEN.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    ta_hist = np.bincount([v["expect_teaching"] for v in vectors],
                          minlength=len(engine.TEACHING_ACTION_NAMES))
    cs_hist = np.bincount([v["expect_confidence"] for v in vectors],
                          minlength=len(engine.CONFIDENCE_STATE_NAMES))
    print(f"rewrote {len(vectors)} vectors ({changed} changed)")
    print("  teaching  : " + ", ".join(
        f"{n}={c}" for n, c in zip(engine.TEACHING_ACTION_NAMES, ta_hist)))
    print("  confidence: " + ", ".join(
        f"{n}={c}" for n, c in zip(engine.CONFIDENCE_STATE_NAMES, cs_hist)))
    print("\nNext: python3 tools/tflite_to_header.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
