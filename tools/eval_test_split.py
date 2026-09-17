import csv
import sys
from pathlib import Path
import numpy as np
import ai_edge_litert.interpreter as tfl

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import rule_engine_gen as engine

csv_path = ROOT / "dataset" / "synthetic.csv"
with open(csv_path, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

X = np.zeros((len(rows), engine.FEATURE_COUNT), dtype=np.float32)
y_ta = np.zeros(len(rows), dtype=np.int32)
y_cs = np.zeros(len(rows), dtype=np.int32)

for i, r in enumerate(rows):
    f_dict = {name: float(r[name]) for name in engine.FEATURE_NAMES}
    X[i] = engine.normalize_features(f_dict)
    y_ta[i] = int(float(r["teaching_action"]))
    y_cs[i] = int(float(r["confidence_state"]))

def stratified_split(y, seed, train=0.70, val=0.15):
    rng = np.random.default_rng(seed)
    idx_tr, idx_va, idx_te = [], [], []
    for c in np.unique(y):
        idx = np.where(y == c)[0]
        rng.shuffle(idx)
        n = len(idx)
        n_tr = max(1, int(round(n * train)))
        n_va = max(1, int(round(n * val))) if n >= 3 else 0
        if n_tr + n_va >= n:
            n_tr, n_va = max(1, n - 2), 1 if n >= 3 else 0
        idx_tr += list(idx[:n_tr])
        idx_va += list(idx[n_tr:n_tr + n_va])
        idx_te += list(idx[n_tr + n_va:])
    rng.shuffle(idx_tr); rng.shuffle(idx_va); rng.shuffle(idx_te)
    return np.array(idx_tr), np.array(idx_va), np.array(idx_te)

i_tr, i_va, i_te = stratified_split(y_ta, 20260730)

interp = tfl.Interpreter(model_path=str(ROOT / "models" / "model.tflite"))
interp.allocate_tensors()
in_det = interp.get_input_details()[0]
in_scale, in_zp = in_det["quantization"]

pred_ta_te = []
pred_cs_te = []

for i in i_te:
    q = np.clip(np.round(X[i] / in_scale + in_zp), -128, 127).astype(np.int8)
    interp.set_tensor(in_det["index"], q.reshape(1, -1))
    interp.invoke()
    # Index 14 is teaching, Index 12 is confidence
    out_ta = interp.get_tensor(14)[0]
    out_cs = interp.get_tensor(12)[0]
    pred_ta_te.append(int(np.argmax(out_ta)))
    pred_cs_te.append(int(np.argmax(out_cs)))

pred_ta_te = np.array(pred_ta_te)
pred_cs_te = np.array(pred_cs_te)
true_ta_te = y_ta[i_te]
true_cs_te = y_cs[i_te]

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

print("=== HELD-OUT TEST SET (91 rows) EVALUATION ===")
print(f"Teaching Action Accuracy   : {np.mean(pred_ta_te == true_ta_te)*100:.2f}%")
print(f"Confidence State Accuracy  : {np.mean(pred_cs_te == true_cs_te)*100:.2f}%")
print(f"Cross Comparison (pred_cs vs true_ta): {np.mean(pred_cs_te == true_ta_te)*100:.2f}%  <-- THIS IS THE 29.67%!")

cm_ta_str, _ = confusion_matrix(true_ta_te, pred_ta_te, engine.TEACHING_ACTION_NAMES)
print("\n--- TEST SET: TEACHING ACTION CONFUSION MATRIX ---")
print(cm_ta_str)

cm_cs_str, _ = confusion_matrix(true_cs_te, pred_cs_te, engine.CONFIDENCE_STATE_NAMES)
print("\n--- TEST SET: CONFIDENCE STATE CONFUSION MATRIX ---")
print(cm_cs_str)
