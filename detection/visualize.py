"""
NeuroFence - Visualization data/figures for the report (matplotlib, saved as PNG).

Creates in detection/figures/:
  1. anomaly_heatmap.png   - share of anomalous positions per layer x prompt type (preliminary_results.json)
  2. candidate_positions.png - candidate trigger positions per layer (analysis_results.json)
  3. top_neurons.png       - strongest candidate neurons (mean Z) in the best layer

Usage:  python detection/visualize.py
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def _natural(l):
    return int(l.split("_")[-1]) if l.split("_")[-1].isdigit() else l


def heatmap(prelim, out):
    cell = defaultdict(list)
    for r in prelim["records"]:
        for l, v in r["layers"].items():
            cell[(r["type"], l)].append(v["anomaly_ratio"])
    types = sorted({t for t, _ in cell})
    layers = sorted({l for _, l in cell}, key=_natural)
    grid = np.array([[100 * np.mean(cell[(t, l)]) for l in layers] for t in types])
    fig, ax = plt.subplots(figsize=(1.6 * len(layers) + 2, 0.7 * len(types) + 2))
    im = ax.imshow(grid, cmap="magma", aspect="auto")
    ax.set_xticks(range(len(layers)), layers)
    ax.set_yticks(range(len(types)), types)
    for i in range(len(types)):
        for j in range(len(layers)):
            ax.text(j, i, f"{grid[i, j]:.1f}", ha="center", va="center", color="w", fontsize=9)
    ax.set_title("Anomalous activation positions (%) - NOT a backdoor verdict")
    fig.colorbar(im, ax=ax, label="% positions with |Z| >= threshold")
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)


def candidates_bar(analysis, out):
    ref = analysis["config"].get("clean_reference_used")
    key = "novel_position_list" if ref else "specific_position_list"
    layers = sorted(analysis["layers"], key=_natural)
    vals = [len(analysis["layers"][l].get(key, [])) for l in layers]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(layers, vals, color="#c0392b" if ref else "#7f8c8d")
    ax.set_ylabel("candidate positions")
    ax.set_title("Trigger-specific positions " + ("(vs clean reference)" if ref else "(UNVALIDATED, no reference)"))
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)


def top_neurons(report, out):
    cands = report.get("candidate_neurons", [])
    if not cands:
        return False
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.barh([f"pos {c['position']}" for c in cands][::-1], [c["trigger_mean_z"] for c in cands][::-1], color="#2980b9")
    ax.set_xlabel("mean Z on trigger prompts")
    ax.set_title(f"Strongest candidate neurons ({report['best_layer']})")
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=str(ROOT / "detection" / "figures"))
    args = ap.parse_args()
    out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    d = ROOT / "detection"
    made = []
    if (d / "preliminary_results.json").exists():
        heatmap(json.load(open(d / "preliminary_results.json", encoding="utf-8")), out / "anomaly_heatmap.png"); made.append("anomaly_heatmap.png")
    if (d / "analysis_results.json").exists():
        candidates_bar(json.load(open(d / "analysis_results.json", encoding="utf-8")), out / "candidate_positions.png"); made.append("candidate_positions.png")
    if (d / "final_report.json").exists():
        if top_neurons(json.load(open(d / "final_report.json", encoding="utf-8")), out / "top_neurons.png"):
            made.append("top_neurons.png")
    print("Figures saved in", out, ":", made)


if __name__ == "__main__":
    main()
