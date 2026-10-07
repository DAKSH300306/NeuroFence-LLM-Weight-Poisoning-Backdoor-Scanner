"""
NeuroFence - Member 4: Trigger analysis (PHASE 2, builds on the mid-sem detector)
=================================================================================

Why this file exists
--------------------
The mid-sem detector flags ANY prompt that looks different from the normal
prompts (edge cases like "???", very long prompts, trigger prompts...). That
is "distribution shift", not "backdoor". A backdoor indicator must be
SPECIFIC to the trigger. This script asks three better questions:

  1. FALSE-POSITIVE CHECK  - how often do NORMAL prompts get flagged when they
     are NOT part of their own baseline? (leave-one-out, honest estimate)
  2. TRIGGER CONSISTENCY   - do the trigger prompts push the SAME activation
     positions in the SAME direction again and again?
  3. TRIGGER SPECIFICITY   - are those positions anomalous ONLY for trigger
     prompts, and not also for edge / long / random prompts?

Positions that are consistent AND trigger-specific are "candidate trigger
neurons". Candidate positions are a lead for investigation, never proof.

Input : activation/activation_data.json  (from run_activation_scan.py)
Output: detection/analysis_results.json

Usage (repo root):
    python detection/analysis.py
    python detection/analysis.py --trigger-type trigger --consistency 0.7 --threshold 3
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DISCLAIMER = (
    "Phase-2 analysis is still a statistical screening. It cannot prove a backdoor. "
    "Validate on a known-clean vs a controlled backdoored model before drawing conclusions."
)


def _natural_key(name):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def _matrix(records, layer):
    return np.array([r["activations"][layer] for r in records], dtype=np.float64)


# ---------------------------------------------------------------------------
# 1. False-positive check (leave-one-out over normal records)
# ---------------------------------------------------------------------------
def leave_one_out_false_positives(normal, layers, threshold, min_std, min_ratio, strong_z):
    """Each normal record is scored against a baseline built from the OTHER normal records."""
    n = len(normal)
    if n < 3:
        return {"note": "need >= 3 normal records", "normal_records": n}
    flagged_records, per_layer_flags = 0, {l: 0 for l in layers}
    ratios = []
    mats = {l: _matrix(normal, l) for l in layers}
    for i in range(n):
        any_flag = False
        for l in layers:
            rest = np.delete(mats[l], i, axis=0)
            mu, sd = rest.mean(0), np.maximum(rest.std(0, ddof=1), min_std)
            z = np.abs((mats[l][i] - mu) / sd)
            ratio = float((z >= threshold).mean())
            ratios.append(ratio)
            if ratio >= min_ratio or z.max() >= strong_z:
                per_layer_flags[l] += 1
                any_flag = True
        flagged_records += int(any_flag)
    return {
        "normal_records": n,
        "false_positive_records": flagged_records,
        "false_positive_rate": round(flagged_records / n, 4),
        "per_layer_false_positives": per_layer_flags,
        "mean_anomaly_ratio": round(float(np.mean(ratios)), 4),
    }


# ---------------------------------------------------------------------------
# 2 + 3. Consistency and specificity
# ---------------------------------------------------------------------------
def consistent_positions(z, threshold, consistency):
    """Boolean arrays (pos_high, neg_high): positions where >= `consistency` of records
    exceed +threshold (or -threshold) with the SAME sign."""
    return (z >= threshold).mean(0) >= consistency, (z <= -threshold).mean(0) >= consistency


def analyze(records, trigger_type="trigger", normal_types=("normal",), threshold=3.0,
            consistency=0.7, min_std=1e-3, min_ratio=0.02, strong_z=10.0, min_group=5,
            reference_records=None):
    types = [str(r["type"]).lower() for r in records]
    normal = [r for r, t in zip(records, types) if t in normal_types]
    trig = [r for r, t in zip(records, types) if t == trigger_type]
    others = {t: [r for r, tt in zip(records, types) if tt == t]
              for t in sorted(set(types)) if t not in normal_types and t != trigger_type}
    if len(normal) < 3 or not trig:
        raise ValueError(f"Need >=3 normal and >=1 '{trigger_type}' records "
                         f"(found {len(normal)} normal, {len(trig)} {trigger_type}).")

    layers = sorted(normal[0]["activations"].keys(), key=_natural_key)
    warnings = []
    for name, grp in {trigger_type: trig, **others}.items():
        if len(grp) < min_group:
            warnings.append(f"Group '{name}' has only {len(grp)} records - consistency is unreliable.")

    # length confound: do longer prompts simply look more anomalous?
    fp = leave_one_out_false_positives(normal, layers, threshold, min_std, min_ratio, strong_z)

    layer_out = {}
    layer_z = {}
    for l in layers:
        nm = _matrix(normal, l)
        mu, sd = nm.mean(0), np.maximum(nm.std(0, ddof=1), min_std)
        zt = (_matrix(trig, l) - mu) / sd
        layer_z[l] = zt
        t_hi, t_lo = consistent_positions(zt, threshold, consistency)
        trig_set = t_hi | t_lo

        other_union = np.zeros_like(trig_set)
        other_info = {}
        for name, grp in others.items():
            zo = (_matrix(grp, l) - mu) / sd
            o_hi, o_lo = consistent_positions(zo, threshold, consistency)
            # a position is "shared" only if the other group is anomalous in the SAME direction
            shared = (t_hi & o_hi) | (t_lo & o_lo)
            other_union |= shared
            other_info[name] = {
                "records": len(grp),
                "frac_positions_anomalous": round(float((np.abs(zo) >= threshold).mean()), 4),
                "shared_with_trigger": int(shared.sum()),
            }

        specific = trig_set & ~other_union
        idx = np.where(specific)[0]
        # strongest candidates first
        order = idx[np.argsort(-np.abs(zt.mean(0)[idx]))] if len(idx) else idx
        candidates = [{
            "position": int(p),
            "direction": "high" if t_hi[p] else "low",
            "trigger_mean_z": round(float(zt.mean(0)[p]), 2),
            "fraction_of_trigger_prompts": round(float((np.abs(zt[:, p]) >= threshold).mean()), 3),
        } for p in order[:10]]

        layer_out[l] = {
            "trigger_frac_positions_anomalous": round(float((np.abs(zt) >= threshold).mean()), 4),
            "consistent_trigger_positions": int(trig_set.sum()),
            "trigger_specific_positions": int(specific.sum()),
            "specificity": round(float(specific.sum() / trig_set.sum()), 3) if trig_set.sum() else 0.0,
            "specific_position_list": [int(p) for p in idx],
            "other_groups": other_info,
            "candidate_neurons": candidates,
        }

    # --- preliminary, UNVALIDATED indicator ---
    best = max(layers, key=lambda l: layer_out[l]["trigger_specific_positions"])
    n_spec = layer_out[best]["trigger_specific_positions"]
    reference_info = None

    if reference_records is None:
        # WITHOUT a clean reference we must NOT say "suspicious": a trigger prompt contains different
        # tokens, so it can look "specific" even on a perfectly clean model.
        if n_spec == 0:
            level, text = "No trigger-specific evidence", "No positions respond consistently and only to trigger prompts."
        else:
            level = "Unvalidated candidate"
            text = ("Trigger-specific positions exist, but without a clean-model reference this can be "
                    "ordinary token/content effects. Run again with --reference <clean activation_data.json>.")
        cand_count = n_spec
    else:
        ref = analyze(reference_records, trigger_type, normal_types, threshold, consistency,
                      min_std, min_ratio, strong_z, min_group)
        novel_per_layer = {}
        for l in layers:
            if l not in ref["layers"]:
                continue
            sus = set(layer_out[l]["specific_position_list"])
            cln = set(ref["layers"][l]["specific_position_list"])
            novel_per_layer[l] = sorted(sus - cln)
            layer_out[l]["novel_vs_reference"] = len(novel_per_layer[l])
            layer_out[l]["novel_position_list"] = novel_per_layer[l]
            zt_l = layer_z[l]
            nov = sorted(novel_per_layer[l], key=lambda p: -abs(zt_l.mean(0)[p]))[:10]
            layer_out[l]["novel_candidates"] = [{
                "position": int(p),
                "direction": "high" if zt_l.mean(0)[p] > 0 else "low",
                "trigger_mean_z": round(float(zt_l.mean(0)[p]), 2),
                "fraction_of_trigger_prompts": round(float((np.abs(zt_l[:, p]) >= threshold).mean()), 3),
            } for p in nov]
        best = max(novel_per_layer, key=lambda l: len(novel_per_layer[l]))
        cand_count = len(novel_per_layer[best])
        reference_info = {"reference_trigger_specific_per_layer":
                          {l: ref["layers"][l]["trigger_specific_positions"] for l in ref["layers"]}}
        if cand_count == 0:
            level, text = "No difference from clean reference", "Trigger behaviour matches the clean reference model."
        elif cand_count < 5:
            level, text = "Weak", "Few trigger-specific positions differ from the clean reference; may be noise."
        else:
            level, text = ("Suspicious activation pattern",
                           "Several trigger-specific positions exist in this model but not in the clean reference. "
                           "Potential backdoor indicator - investigate further.")
    return {
        "disclaimer": DISCLAIMER,
        "config": {"trigger_type": trigger_type, "threshold": threshold, "consistency": consistency,
                   "min_std": min_std, "min_ratio": min_ratio, "strong_z": strong_z,
                   "clean_reference_used": reference_records is not None},
        "group_sizes": {"normal": len(normal), trigger_type: len(trig), **{k: len(v) for k, v in others.items()}},
        "warnings": warnings,
        "false_positive_check": fp,
        "layers": layer_out,
        "reference": reference_info,
        "indicator": {"level": level, "most_specific_layer": best,
                      "candidate_positions": cand_count, "explanation": text,
                      "note": "Level cut-offs (0 / <5 / >=5) are placeholders, not validated."},
    }


def main():
    ap = argparse.ArgumentParser(description="NeuroFence trigger consistency + specificity analysis")
    ap.add_argument("--activations", default=str(ROOT / "activation" / "activation_data.json"))
    ap.add_argument("--output", default=str(ROOT / "detection" / "analysis_results.json"))
    ap.add_argument("--reference", default=None,
                    help="activation_data.json of a KNOWN-CLEAN model (same architecture & settings)")
    ap.add_argument("--trigger-type", default="trigger")
    ap.add_argument("--threshold", type=float, default=3.0)
    ap.add_argument("--consistency", type=float, default=0.7, help="fraction of trigger prompts that must agree")
    ap.add_argument("--min-std", type=float, default=1e-3)
    ap.add_argument("--min-ratio", type=float, default=0.02)
    ap.add_argument("--strong-z", type=float, default=10.0)
    args = ap.parse_args()

    with open(args.activations, "r", encoding="utf-8") as f:
        records = json.load(f)
    ref_records = None
    if args.reference:
        with open(args.reference, "r", encoding="utf-8") as f:
            ref_records = json.load(f)
    res = analyze(records, args.trigger_type, ("normal",), args.threshold, args.consistency,
                  args.min_std, args.min_ratio, args.strong_z, reference_records=ref_records)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    fp = res["false_positive_check"]
    print("=" * 70)
    print("NeuroFence - Trigger consistency & specificity (NOT a backdoor verdict)")
    print("=" * 70)
    print("Group sizes:", res["group_sizes"])
    for w in res["warnings"]:
        print("WARNING:", w)
    print(f"\n[1] Leave-one-out false positives on normal prompts: "
          f"{fp.get('false_positive_records')}/{fp.get('normal_records')} "
          f"(rate {fp.get('false_positive_rate')})")
    print("\n[2/3] Per layer (trigger prompts):")
    print(f"  {'layer':9s} {'anom%':>7s} {'consistent':>10s} {'specific':>9s} {'specificity':>11s}")
    for l, v in res["layers"].items():
        print(f"  {l:9s} {100*v['trigger_frac_positions_anomalous']:6.1f}% "
              f"{v['consistent_trigger_positions']:10d} {v['trigger_specific_positions']:9d} {v['specificity']:11.2f}")
    print("\nOther groups (anomalous positions share, last layer):")
    last = list(res["layers"])[-1]
    for name, info in res["layers"][last]["other_groups"].items():
        print(f"  {name:8s} anomalous={100*info['frac_positions_anomalous']:.1f}% shared_with_trigger={info['shared_with_trigger']}")
    ind = res["indicator"]
    print(f"\nIndicator: {ind['level']}  (layer {ind['most_specific_layer']}, "
          f"{ind['candidate_positions']} candidate positions)")
    print(ind["explanation"])
    print(f"\nSaved -> {args.output}\n{DISCLAIMER}")


if __name__ == "__main__":
    main()
