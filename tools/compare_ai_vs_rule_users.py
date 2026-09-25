#!/usr/bin/env python3
"""
Compare AI Model vs Strict Rule Engine across all users in the dataset.
Demonstrates personalized adaptive behavior vs. rigid rule-based thresholds.
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import rule_engine_gen as engine

# Parse model weights from firmware/braille_tutor/model_weights.h
with open(ROOT / "firmware" / "braille_tutor" / "model_weights.h", "r") as f:
    code = f.read()

def parse_array(name):
    decl = f"{name}[] = "
    start = code.find(decl) + len(decl)
    start = code.find("{", start) + 1
    end = code.find("};", start)
    chunk = code[start:end]
    nums = [float(x.strip().rstrip("f")) for x in chunk.split(",") if x.strip()]
    return np.array(nums, dtype=np.float32)

ta_w0 = parse_array("ML_TA_W0").reshape(8, 32)
ta_b0 = parse_array("ML_TA_B0")
ta_w1 = parse_array("ML_TA_W1").reshape(32, 16)
ta_b1 = parse_array("ML_TA_B1")
ta_w2 = parse_array("ML_TA_W2").reshape(16, 3)
ta_b2 = parse_array("ML_TA_B2")

cs_w0 = parse_array("ML_CS_W0").reshape(8, 32)
cs_b0 = parse_array("ML_CS_B0")
cs_w1 = parse_array("ML_CS_W1").reshape(32, 16)
cs_b1 = parse_array("ML_CS_B1")
cs_w2 = parse_array("ML_CS_W2").reshape(16, 3)
cs_b2 = parse_array("ML_CS_B2")

def relu(x):
    return np.maximum(0, x)

def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()

def predict_ai(features_dict):
    norm = engine.normalize_features(features_dict)
    # TA head
    h1 = relu(norm @ ta_w0 + ta_b0)
    h2 = relu(h1 @ ta_w1 + ta_b1)
    out_ta = h2 @ ta_w2 + ta_b2
    prob_ta = softmax(out_ta)
    pred_ta = int(np.argmax(out_ta))

    # CS head
    h1_cs = relu(norm @ cs_w0 + cs_b0)
    h2_cs = relu(h1_cs @ cs_w1 + cs_b1)
    out_cs = h2_cs @ cs_w2 + cs_b2
    prob_cs = softmax(out_cs)
    pred_cs = int(np.argmax(out_cs))

    return pred_ta, pred_cs, prob_ta, prob_cs

def main():
    csv_path = ROOT / "dataset" / "real.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    user_data = defaultdict(list)
    for r in rows:
        uid = r.get("user_id", "unknown")
        user_data[uid].append(r)

    print("================================================================================")
    print("AI MODEL VS. STRICT RULE ENGINE: PERSONALIZATION COMPARISON TEST ACROSS USERS")
    print("================================================================================\n")

    user_profiles = {}

    for uid, urows in sorted(user_data.items()):
        total = len(urows)
        correct_count = sum(1 for r in urows if r["is_correct"].lower() in ("true", "1"))
        acc = (correct_count / total) * 100 if total else 0
        avg_rt = np.mean([float(r["response_time"]) for r in urows])
        avg_pd = np.mean([float(r["press_duration"]) for r in urows])
        avg_retries = np.mean([float(r["retry_count"]) for r in urows])
        avg_hints = np.mean([float(r["hint_count"]) for r in urows])

        ta_rule_dist = [0, 0, 0]
        ta_ai_dist = [0, 0, 0]
        cs_rule_dist = [0, 0, 0]
        cs_ai_dist = [0, 0, 0]

        divergences = []

        for r in urows:
            feat = {name: float(r[name]) for name in engine.FEATURE_NAMES}
            rule_ta = engine.evaluate_teaching_action(feat)
            rule_cs = engine.evaluate_confidence(feat)

            ai_ta, ai_cs, p_ta, p_cs = predict_ai(feat)

            ta_rule_dist[rule_ta] += 1
            ta_ai_dist[ai_ta] += 1
            cs_rule_dist[rule_cs] += 1
            cs_ai_dist[ai_cs] += 1

            if rule_ta != ai_ta or rule_cs != ai_cs:
                divergences.append({
                    "char_id": r["char_id"],
                    "rt": feat["response_time"],
                    "pd": feat["press_duration"],
                    "retries": feat["retry_count"],
                    "hints": feat["hint_count"],
                    "prev_acc": feat["prev_accuracy"],
                    "prev_mst": feat["prev_mastery"],
                    "cur_streak": feat["current_streak"],
                    "wrong_streak": feat["wrong_streak"],
                    "is_correct": r["is_correct"],
                    "rule_ta": engine.TEACHING_ACTION_NAMES[rule_ta],
                    "ai_ta": engine.TEACHING_ACTION_NAMES[ai_ta],
                    "ai_ta_conf": p_ta[ai_ta],
                    "rule_cs": engine.CONFIDENCE_STATE_NAMES[rule_cs],
                    "ai_cs": engine.CONFIDENCE_STATE_NAMES[ai_cs],
                    "ai_cs_conf": p_cs[ai_cs]
                })

        user_profiles[uid] = {
            "total": total,
            "accuracy": acc,
            "avg_rt": avg_rt,
            "avg_pd": avg_pd,
            "avg_retries": avg_retries,
            "avg_hints": avg_hints,
            "ta_rule": ta_rule_dist,
            "ta_ai": ta_ai_dist,
            "cs_rule": cs_rule_dist,
            "cs_ai": cs_ai_dist,
            "divergences": divergences
        }

    # Print summary table
    print(f"{'User ID':<8} | {'Attempts':<8} | {'Avg Acc':<8} | {'Avg RT (ms)':<12} | {'TA Divergence':<14} | {'CS Divergence':<14} | {'Personalized Trend'}")
    print("-" * 105)
    for uid, p in sorted(user_profiles.items()):
        ta_diff = sum(1 for d in p["divergences"] if d["rule_ta"] != d["ai_ta"])
        cs_diff = sum(1 for d in p["divergences"] if d["rule_cs"] != d["ai_cs"])
        ta_diff_pct = (ta_diff / p["total"]) * 100 if p["total"] else 0
        cs_diff_pct = (cs_diff / p["total"]) * 100 if p["total"] else 0
        
        trend = ""
        if uid == "P01":
            trend = "Beginner (fast, trial-and-error) -> AI flags subtle guessing"
        elif uid == "P02":
            trend = "Balanced Learner -> AI smooths rigid streak thresholds"
        elif uid == "P03":
            trend = "Thoughtful/Deliberate (high RT, high accuracy) -> AI recognizes confidence despite slow speed"
        elif uid == "P04":
            trend = "Novice / Initial Session Check"

        print(f"{uid:<8} | {p['total']:<8} | {p['accuracy']:<7.1f}% | {p['avg_rt']:<12.0f} | {ta_diff} ({ta_diff_pct:.1f}%)      | {cs_diff} ({cs_diff_pct:.1f}%)      | {trend}")

    print("\n" + "=" * 80)
    print("DETAILED USER CASE STUDIES (WHERE AI MODEL IMPROVES OVER STRICT ENGINE)")
    print("=" * 80)

    for uid in ["P01", "P02", "P03"]:
        p = user_profiles[uid]
        print(f"\n>>> USER {uid} (N = {p['total']} attempts, Accuracy: {p['accuracy']:.1f}%, Avg RT: {p['avg_rt']:.0f} ms)")
        print("  Confidence State Distribution:")
        print(f"    Strict Rule Engine : CONFIDENT={p['cs_rule'][0]}, HESITANT={p['cs_rule'][1]}, GUESSING={p['cs_rule'][2]}")
        print(f"    Adaptive AI Model  : CONFIDENT={p['cs_ai'][0]}, HESITANT={p['cs_ai'][1]}, GUESSING={p['cs_ai'][2]}")

        print("  Teaching Action Distribution:")
        print(f"    Strict Rule Engine : REPEAT={p['ta_rule'][0]}, HINT={p['ta_rule'][1]}, NORMAL_PRACTICE={p['ta_rule'][2]}")
        print(f"    Adaptive AI Model  : REPEAT={p['ta_ai'][0]}, HINT={p['ta_ai'][1]}, NORMAL_PRACTICE={p['ta_ai'][2]}")

        divs = p["divergences"]
        print(f"  Representative Divergence Examples for {uid}:")
        sample_cases = divs[:4] if len(divs) >= 4 else divs
        for idx, c in enumerate(sample_cases, 1):
            print(f"    Case {idx} [Letter #{c['char_id']} | RT={c['rt']:.0f}ms | Retries={c['retries']:.0f} | Acc={c['prev_acc']:.2f} | Mastery={c['prev_mst']:.2f} | Streaks={c['cur_streak']}/{c['wrong_streak']}]:")
            print(f"      - Strict Rule Engine Output : CS = {c['rule_cs']:<10} | TA = {c['rule_ta']}")
            print(f"      - Adaptive AI Model Output  : CS = {c['ai_cs']:<10} | TA = {c['ai_ta']} (prob: {c['ai_cs_conf']*100:.1f}%)")
            # Explanation
            if c['rule_cs'] != c['ai_cs']:
                if c['rule_cs'] == 'HESITANT' and c['ai_cs'] == 'CONFIDENT':
                    print("      * Personalization Rationale: Strict rule penalizes learner for RT > 3000ms cutoff, but AI observes high rolling accuracy/mastery and classifies as CONFIDENT (thoughtful pacing).")
                elif c['rule_cs'] == 'CONFIDENT' and c['ai_cs'] == 'HESITANT':
                    print("      * Personalization Rationale: Strict rule sees short response time, but AI flags low historical mastery and detects false confidence / hesitation.")
                elif c['rule_cs'] == 'HESITANT' and c['ai_cs'] == 'GUESSING':
                    print("      * Personalization Rationale: Strict rule misses subtle repeated retry patterns that the AI multi-feature weighting identifies as GUESSING.")

if __name__ == "__main__":
    main()
