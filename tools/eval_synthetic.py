import csv
import sys
from pathlib import Path
import numpy as np
import ai_edge_litert.interpreter as tfl

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import rule_engine_gen as engine

csv_path = ROOT / "dataset" / "synthetic.csv"
if not csv_path.exists():
    print(f"File not found: {csv_path}")
    sys.exit(1)

with open(csv_path, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print(f"Total rows in synthetic dataset: {len(rows)}")

X = np.zeros((len(rows), engine.FEATURE_COUNT), dtype=np.float32)
y_ta = np.zeros(len(rows), dtype=np.int32)
y_cs = np.zeros(len(rows), dtype=np.int32)

for i, r in enumerate(rows):
    f_dict = {name: float(r[name]) for name in engine.FEATURE_NAMES}
    X[i] = engine.normalize_features(f_dict)
    y_ta[i] = int(float(r["teaching_action"]))
    y_cs[i] = int(float(r["confidence_state"]))

interp = tfl.Interpreter(model_path=str(ROOT / "models" / "model.tflite"))
interp.allocate_tensors()

in_det = interp.get_input_details()[0]
out_dets = interp.get_output_details()
in_scale, in_zp = in_det["quantization"]

print("\n--- Model Output Tensors ---")
for d in out_dets:
    print(f"Index: {d['index']}, Name: {d['name']}, Shape: {d['shape']}")

preds = {d["index"]: [] for d in out_dets}

for i in range(len(rows)):
    q = np.clip(np.round(X[i] / in_scale + in_zp), -128, 127).astype(np.int8)
    interp.set_tensor(in_det["index"], q.reshape(1, -1))
    interp.invoke()
    for d in out_dets:
        out_val = interp.get_tensor(d["index"])[0]
        preds[d["index"]].append(int(np.argmax(out_val)))

for d in out_dets:
    preds[d["index"]] = np.array(preds[d["index"]])

out_indices = [d["index"] for d in out_dets]

def confusion_matrix(y_true, y_pred, names):
    n = len(names)
    m = np.zeros((n, n), dtype=int)
    for t, p in zip(y_true, y_pred):
        m[t, p] += 1
    w = max(len(x) for x in names) + 2
    header = " " * w + "".join(f"{names[j]:>18}" for j in range(n))
    lines = [header + "   <- Predicted"]
    for i, name in enumerate(names):
        row_str = f"{name:<{w}}" + "".join(f"{m[i, j]:>18}" for j in range(n))
        lines.append(row_str)
    return "\n".join(lines), m

print("\n=======================================================")
print("EVALUATING BOTH OUTPUT HEADS AGAINST BOTH TARGETS")
print("=======================================================")

for idx in out_indices:
    acc_ta = np.mean(preds[idx] == y_ta)
    acc_cs = np.mean(preds[idx] == y_cs)
    print(f"Output Index {idx}:")
    print(f"  Accuracy vs Teaching Action (y_ta)    : {acc_ta * 100:.2f}%")
    print(f"  Accuracy vs Confidence State (y_cs)   : {acc_cs * 100:.2f}%")

if np.mean(preds[out_indices[0]] == y_ta) > np.mean(preds[out_indices[1]] == y_ta):
    idx_ta, idx_cs = out_indices[0], out_indices[1]
else:
    idx_ta, idx_cs = out_indices[1], out_indices[0]

print("\n=======================================================")
print(f"IDENTIFIED HEADS: Teaching Action = Index {idx_ta}, Confidence State = Index {idx_cs}")
print("=======================================================")

pred_ta = preds[idx_ta]
pred_cs = preds[idx_cs]

cm_ta_str, cm_ta = confusion_matrix(y_ta, pred_ta, engine.TEACHING_ACTION_NAMES)
print("\n--- TEACHING ACTION CONFUSION MATRIX ---")
print(cm_ta_str)

print("\nTeaching Action Per-Class Metrics:")
for i, name in enumerate(engine.TEACHING_ACTION_NAMES):
    tp = cm_ta[i, i]
    actual = np.sum(cm_ta[i, :])
    predicted = np.sum(cm_ta[:, i])
    recall = tp / actual if actual > 0 else 0
    precision = tp / predicted if predicted > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    print(f"  {name:<16}: Support={actual:>3}, Recall={recall*100:>6.2f}%, Precision={precision*100:>6.2f}%, F1={f1*100:>6.2f}%")

cm_cs_str, cm_cs = confusion_matrix(y_cs, pred_cs, engine.CONFIDENCE_STATE_NAMES)
print("\n--- CONFIDENCE STATE CONFUSION MATRIX ---")
print(cm_cs_str)

print("\nConfidence State Per-Class Metrics:")
for i, name in enumerate(engine.CONFIDENCE_STATE_NAMES):
    tp = cm_cs[i, i]
    actual = np.sum(cm_cs[i, :])
    predicted = np.sum(cm_cs[:, i])
    recall = tp / actual if actual > 0 else 0
    precision = tp / predicted if predicted > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    print(f"  {name:<16}: Support={actual:>3}, Recall={recall*100:>6.2f}%, Precision={precision*100:>6.2f}%, F1={f1*100:>6.2f}%")
