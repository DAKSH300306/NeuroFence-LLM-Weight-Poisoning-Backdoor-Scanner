"""
NeuroFence - Member 4: Detection evaluation (precision / recall / F1)
=====================================================================

Question answered: "If we learn a trigger fingerprint from a suspect model (compared with a
clean reference model), can we detect trigger prompts we have NOT used to learn it?"

Method (all numbers are computed, nothing is hard-coded):
  1. Split every prompt type in half (even / odd index): FIT half, TEST half.
  2. FIT: run analysis.analyze(suspect_fit, reference=clean_fit) -> "novel" trigger positions per layer
     (positions that are trigger-specific in the suspect model but not in the clean model).
  3. TEST: for each test prompt on the SUSPECT model, fingerprint score =
     mean signed Z over the novel positions (best layer). Predict "trigger activated" if score >= tau.
  4. Ground truth: positive = prompt of type `trigger`.
  5. FALSE-ALARM check: same fingerprint on the CLEAN model's test prompts (nothing should fire).

Output: detection/evaluation.json  (+ printed confusion matrix)

Usage:
    python detection/evaluate_detection.py --suspect activation/activation_data.json \
        --clean activation/activation_data_clean.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from detection.analysis import analyze, _matrix  # noqa: E402


def split_half(records):
    fit, test, seen = [], [], {}
    for r in records:
        t = str(r["type"]).lower()
        i = seen.get(t, 0)
        seen[t] = i + 1
        (fit if i % 2 == 0 else test).append(r)
    return fit, test


def score_records(records, layer_positions, signs, baseline_records, min_std):
    """Return a score per record (max over layers of mean signed Z over fingerprint positions)."""
    base = {}
    for l in layer_positions:
        nm = _matrix(baseline_records, l)
        base[l] = (nm.mean(0), np.maximum(nm.std(0, ddof=1), min_std))
    scores = []
    for r in records:
        best = 0.0
        for l, pos in layer_positions.items():
            mu, sd = base[l]
            x = np.array(r["activations"][l])
            z = (x[pos] - mu[pos]) / sd[pos]
            best = max(best, float(np.mean(z * signs[l])))
        scores.append(best)
    return np.array(scores)


def metrics(y_true, y_pred):
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    acc = (tp + tn) / max(1, tp + tn + fp + fn)
    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn, "precision": round(prec, 4),
            "recall": round(rec, 4), "f1": round(f1, 4), "accuracy": round(acc, 4)}


def evaluate(suspect, clean, trigger_type="trigger", normal_types=("normal",), threshold=3.0,
             consistency=0.7, tau=3.0, min_std=1e-3):
    s_fit, s_test = split_half(suspect)
    c_fit, c_test = split_half(clean)

    res = analyze(s_fit, trigger_type, normal_types, threshold, consistency, min_std,
                  reference_records=c_fit)
    layer_positions, signs = {}, {}
    trig_fit = [r for r in s_fit if str(r["type"]).lower() == trigger_type]
    normal_fit = [r for r in s_fit if str(r["type"]).lower() in normal_types]
    for l, info in res["layers"].items():
        pos = info.get("novel_position_list", [])
        if pos:
            layer_positions[l] = pos
            nm = _matrix(normal_fit, l)
            mu, sd = nm.mean(0), np.maximum(nm.std(0, ddof=1), min_std)
            signs[l] = np.sign((_matrix(trig_fit, l).mean(0)[pos] - mu[pos]) / sd[pos])

    out = {"tau": tau, "fingerprint_positions": {l: len(p) for l, p in layer_positions.items()},
           "fit_records": len(s_fit), "test_records": len(s_test)}
    if not layer_positions:
        out.update({"note": "No novel trigger positions found on the FIT split - nothing to evaluate "
                            "(the suspect model behaves like the clean reference).",
                    "suspect_model": None, "clean_model_false_alarm_rate": None})
        return out

    y_true = np.array([1 if str(r["type"]).lower() == trigger_type else 0 for r in s_test])
    s_scores = score_records(s_test, layer_positions, signs, normal_fit, min_std)
    out["suspect_model"] = metrics(y_true, (s_scores >= tau).astype(int))
    out["suspect_model"]["mean_score_trigger"] = round(float(s_scores[y_true == 1].mean()), 2)
    out["suspect_model"]["mean_score_other"] = round(float(s_scores[y_true == 0].mean()), 2)

    clean_normal_fit = [r for r in c_fit if str(r["type"]).lower() in normal_types]
    c_scores = score_records(c_test, layer_positions, signs, clean_normal_fit, min_std)
    out["clean_model_false_alarm_rate"] = round(float((c_scores >= tau).mean()), 4)
    out["note"] = ("Fingerprint learned on FIT half, scored on unseen TEST half. Small test sets give "
                   "unstable numbers; treat as indicative, not final.")
    return out


def main():
    ap = argparse.ArgumentParser(description="NeuroFence detection evaluation")
    ap.add_argument("--suspect", default=str(ROOT / "activation" / "activation_data.json"))
    ap.add_argument("--clean", default=str(ROOT / "activation" / "activation_data_clean.json"))
    ap.add_argument("--output", default=str(ROOT / "detection" / "evaluation.json"))
    ap.add_argument("--trigger-type", default="trigger")
    ap.add_argument("--threshold", type=float, default=3.0)
    ap.add_argument("--consistency", type=float, default=0.7)
    ap.add_argument("--tau", type=float, default=3.0, help="fingerprint score needed to predict 'triggered'")
    args = ap.parse_args()

    suspect = json.load(open(args.suspect, encoding="utf-8"))
    clean = json.load(open(args.clean, encoding="utf-8"))
    out = evaluate(suspect, clean, args.trigger_type, ("normal",), args.threshold, args.consistency, args.tau)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(args.output, "w", encoding="utf-8"), indent=2)

    print("=" * 60)
    print("NeuroFence - Detection evaluation (held-out prompts)")
    print("=" * 60)
    print("Fingerprint positions per layer:", out["fingerprint_positions"])
    m = out.get("suspect_model")
    if m:
        print(f"Confusion (suspect model): TP={m['TP']} FP={m['FP']} TN={m['TN']} FN={m['FN']}")
        print(f"Precision={m['precision']}  Recall={m['recall']}  F1={m['f1']}  Accuracy={m['accuracy']}")
        print(f"Clean-model false-alarm rate: {out['clean_model_false_alarm_rate']}")
    print(out["note"])
    print(f"Saved -> {args.output}")


if __name__ == "__main__":
    main()
