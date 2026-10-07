"""
NeuroFence - Member 4: Normal activation baseline
=================================================

activation/activation_data.json  ->  detection/baseline.json

Idea: normal prompts define what "normal" internal behaviour looks like.
For every monitored layer we store:
  * position_mean / position_std : mean and std of EACH activation position
                                   (neuron) across all normal prompts
  * layer_stats                  : overall mean / std / min / max of the layer

Usage (from repo root):
    python detection/baseline.py
    python detection/baseline.py --input activation/activation_data.json --output detection/baseline.json
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def _natural_key(name: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def build_baseline(records, normal_types=("normal",)):
    normal = [r for r in records if str(r.get("type", "")).lower() in normal_types]
    if len(normal) < 2:
        raise ValueError(
            f"Need at least 2 'normal' records to build a baseline, found {len(normal)}. "
            "Check the 'type' field in activation_data.json."
        )

    layers = sorted(normal[0]["activations"].keys(), key=_natural_key)
    baseline = {"num_normal_records": len(normal), "normal_types": list(normal_types), "layers": {}}

    for layer in layers:
        matrix = np.array([r["activations"][layer] for r in normal], dtype=np.float64)  # (n, positions)
        rec_stats = [r["statistics"][layer] for r in normal]
        rec_means = np.array([s["mean"] for s in rec_stats])
        baseline["layers"][layer] = {
            "num_positions": int(matrix.shape[1]),
            "position_mean": [round(float(v), 6) for v in matrix.mean(axis=0)],
            "position_std": [round(float(v), 6) for v in matrix.std(axis=0, ddof=1)],
            "layer_stats": {
                "mean": round(float(rec_means.mean()), 6),
                "std": round(float(rec_means.std(ddof=1)), 6),
                "min": round(float(min(s["min"] for s in rec_stats)), 6),
                "max": round(float(max(s["max"] for s in rec_stats)), 6),
            },
        }
    return baseline


def main():
    ap = argparse.ArgumentParser(description="Build normal activation baseline")
    ap.add_argument("--input", default=str(ROOT / "activation" / "activation_data.json"))
    ap.add_argument("--output", default=str(ROOT / "detection" / "baseline.json"))
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        records = json.load(f)

    baseline = build_baseline(records)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(baseline, f)

    print(f"Baseline built from {baseline['num_normal_records']} normal records -> {args.output}")
    for layer, info in baseline["layers"].items():
        s = info["layer_stats"]
        print(f"  {layer:10s} mean={s['mean']:.4f} std={s['std']:.4f} min={s['min']:.3f} max={s['max']:.3f}")


if __name__ == "__main__":
    main()
