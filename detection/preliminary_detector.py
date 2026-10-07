"""
NeuroFence - Member 4: Preliminary anomaly detector (MID-SEM version)
=====================================================================

activation_data.json + baseline.json  ->  detection/preliminary_results.json

Method (simple, statistical):
    Z = |x - baseline_mean| / baseline_std     (per layer, per activation position)
A position is "anomalous" if Z >= threshold (default 3).

IMPORTANT (scientific limitation)
---------------------------------
* The threshold (3) and the flagging rules below are PRELIMINARY heuristics,
  not scientifically validated. Final semester: validate on clean vs.
  controlled-backdoored models (precision / recall / F1).
* A high Z-score is only a "potential activation anomaly". It does NOT prove
  a backdoor or malicious behaviour.
* Normal records are also analysed as a CONTROL group (in-sample, so slightly
  optimistic) - this shows how often ordinary prompts look "anomalous".

Usage (from repo root):
    python detection/preliminary_detector.py
    python detection/preliminary_detector.py --threshold 3 --min-ratio 0.02 --strong-z 10
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

DISCLAIMER = (
    "Preliminary statistical screening only. Flagged items are potential activation "
    "anomalies, NOT confirmed backdoors. Thresholds are not yet experimentally validated."
)
FLAG_TEXT = "Potential activation anomaly"
OK_TEXT = "No significant anomaly"


def _natural_key(name: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def analyze_layer(values, layer_base, threshold, min_std, min_ratio, strong_z, top_k=5):
    x = np.asarray(values, dtype=np.float64)
    mu = np.asarray(layer_base["position_mean"], dtype=np.float64)
    sd = np.maximum(np.asarray(layer_base["position_std"], dtype=np.float64), min_std)
    if x.shape != mu.shape:
        raise ValueError(f"Length mismatch: activation {x.shape} vs baseline {mu.shape}. Rebuild baseline.")

    z = np.abs((x - mu) / sd)
    mask = z >= threshold
    n_anom = int(mask.sum())
    ratio = n_anom / len(x)
    max_z = float(z.max())
    flagged = bool(ratio >= min_ratio or max_z >= strong_z)

    top_idx = np.argsort(-z)[:top_k]
    top = [
        {
            "position": int(i),
            "value": round(float(x[i]), 5),
            "baseline_mean": round(float(mu[i]), 5),
            "baseline_std": round(float(sd[i]), 5),
            "z_score": round(float(z[i]), 2),
        }
        for i in top_idx
        if z[i] >= threshold
    ]
    return {
        "max_z": round(max_z, 2),
        "mean_z": round(float(z.mean()), 3),
        "anomalous_positions": n_anom,
        "total_positions": int(len(x)),
        "anomaly_ratio": round(ratio, 4),
        "status": FLAG_TEXT if flagged else OK_TEXT,
        "flagged": flagged,
        "top_suspicious_positions": top,
    }


def analyze_records(records, baseline, threshold=3.0, min_std=1e-3, min_ratio=0.02, strong_z=10.0,
                    normal_types=("normal",)):
    results = []
    for rec in records:
        rtype = str(rec.get("type", "")).lower()
        layer_results, total_anom, total_pos = {}, 0, 0
        for layer, layer_base in baseline["layers"].items():
            if layer not in rec["activations"]:
                continue
            lr = analyze_layer(rec["activations"][layer], layer_base, threshold, min_std, min_ratio, strong_z)
            layer_results[layer] = lr
            total_anom += lr["anomalous_positions"]
            total_pos += lr["total_positions"]

        flagged_layers = [l for l, v in layer_results.items() if v["flagged"]]
        score = round(100.0 * total_anom / total_pos, 2) if total_pos else 0.0
        results.append({
            "id": rec.get("id"),
            "type": rtype,
            "role": "control" if rtype in normal_types else "test",
            "prompt": rec.get("prompt", ""),
            "preliminary_score": score,   # % of activation positions with Z >= threshold (0-100)
            "max_z": max((v["max_z"] for v in layer_results.values()), default=0.0),
            "status": FLAG_TEXT if flagged_layers else OK_TEXT,
            "suspicious_layers": sorted(flagged_layers, key=_natural_key),
            "layers": layer_results,
        })
    return results


def summarize(results):
    by_type = defaultdict(list)
    for r in results:
        by_type[r["type"]].append(r)

    type_summary = {
        t: {
            "records": len(rs),
            "flagged_records": sum(1 for r in rs if r["suspicious_layers"]),
            "mean_score": round(float(np.mean([r["preliminary_score"] for r in rs])), 2),
            "max_z": round(max(r["max_z"] for r in rs), 2),
        }
        for t, rs in by_type.items()
    }

    layer_stats = defaultdict(lambda: {"ratios": [], "flags": 0, "n": 0})
    for r in results:
        if r["role"] != "test":
            continue
        for layer, lr in r["layers"].items():
            s = layer_stats[layer]
            s["ratios"].append(lr["anomaly_ratio"])
            s["flags"] += int(lr["flagged"])
            s["n"] += 1
    layer_ranking = sorted(
        (
            {
                "layer": layer,
                "test_records_flagged": s["flags"],
                "test_records": s["n"],
                "mean_anomaly_ratio": round(float(np.mean(s["ratios"])), 4),
            }
            for layer, s in layer_stats.items()
        ),
        key=lambda d: (-d["mean_anomaly_ratio"], _natural_key(d["layer"])),
    )
    return {"by_type": type_summary, "layer_ranking_test_records": layer_ranking}


def main():
    ap = argparse.ArgumentParser(description="NeuroFence preliminary Z-score detector")
    ap.add_argument("--activations", default=str(ROOT / "activation" / "activation_data.json"))
    ap.add_argument("--baseline", default=str(ROOT / "detection" / "baseline.json"))
    ap.add_argument("--output", default=str(ROOT / "detection" / "preliminary_results.json"))
    ap.add_argument("--threshold", type=float, default=3.0, help="Z-score threshold per position")
    ap.add_argument("--min-std", type=float, default=1e-3, help="floor for std (avoids divide-by-~0)")
    ap.add_argument("--min-ratio", type=float, default=0.02, help="flag layer if this fraction of positions is anomalous")
    ap.add_argument("--strong-z", type=float, default=10.0, help="flag layer if any single Z reaches this")
    args = ap.parse_args()

    with open(args.activations, "r", encoding="utf-8") as f:
        records = json.load(f)
    with open(args.baseline, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    results = analyze_records(records, baseline, args.threshold, args.min_std, args.min_ratio, args.strong_z)
    summary = summarize(results)
    output = {
        "disclaimer": DISCLAIMER,
        "config": {"threshold": args.threshold, "min_std": args.min_std,
                   "min_ratio": args.min_ratio, "strong_z": args.strong_z},
        "summary": summary,
        "records": results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("=" * 66)
    print("NeuroFence - Preliminary detection (NOT a confirmed backdoor verdict)")
    print("=" * 66)
    print("Per prompt type:")
    for t, s in summary["by_type"].items():
        print(f"  {t:10s} records={s['records']:3d} flagged={s['flagged_records']:3d} "
              f"mean_score={s['mean_score']:6.2f}% max_z={s['max_z']}")
    print("\nSuspicious layer ranking (non-normal records):")
    for d in summary["layer_ranking_test_records"]:
        print(f"  {d['layer']:10s} flagged {d['test_records_flagged']}/{d['test_records']} "
              f"mean_anomaly_ratio={d['mean_anomaly_ratio']}")
    print("\nTop flagged non-normal prompts:")
    tests = sorted((r for r in results if r["role"] == "test"), key=lambda r: -r["preliminary_score"])[:5]
    for r in tests:
        print(f"  [{r['type']}] score={r['preliminary_score']:5.2f}% max_z={r['max_z']:7.2f} "
              f"-> {r['status']} {r['suspicious_layers']}  prompt={r['prompt'][:40]!r}")
    print(f"\nSaved -> {args.output}")
    print(DISCLAIMER)


if __name__ == "__main__":
    main()
