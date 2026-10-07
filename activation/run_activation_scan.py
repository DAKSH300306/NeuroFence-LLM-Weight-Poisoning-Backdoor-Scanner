"""
NeuroFence - Member 3: run the activation scan.

generated_prompts.json  ->  local LLM + hooks  ->  activation/activation_data.json

Usage (from repo root):
    python activation/run_activation_scan.py --model distilgpt2
    python activation/run_activation_scan.py --model ./local_model --local-only
    python activation/run_activation_scan.py --prompts fuzzer/generated_prompts.json --num-layers 6

Output files:
    activation/activation_data.json   (one record per prompt)
    activation/activation_meta.json   (model name, monitored layers, settings)
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from activation.activation_tracker import ActivationTracker, load_model  # noqa: E402

TEXT_KEYS = ("prompt", "text", "input", "content", "query", "message")
TYPE_KEYS = ("type", "category", "label", "kind", "class")
WRAPPER_KEYS = ("prompts", "records", "data", "test_cases", "cases", "items")


# ---------------------------------------------------------------------------
# Reading generated_prompts.json  (tolerant to several formats)
# ---------------------------------------------------------------------------
def _first_key(d: dict, keys):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _to_records(data, default_type="unknown"):
    records = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                records.append({"id": None, "type": default_type, "prompt": item})
            elif isinstance(item, dict):
                text = _first_key(item, TEXT_KEYS)
                if text is None:
                    continue
                rtype = _first_key(item, TYPE_KEYS) or default_type
                records.append({"id": item.get("id"), "type": str(rtype).lower(), "prompt": str(text)})
    elif isinstance(data, dict):
        wrapped = next((data[k] for k in WRAPPER_KEYS if isinstance(data.get(k), list)), None)
        if wrapped is not None:
            records.extend(_to_records(wrapped, default_type))
        else:  # {"normal": [...], "trigger": [...]}
            for key, value in data.items():
                if isinstance(value, list):
                    records.extend(_to_records(value, str(key).lower()))
    return records


def load_prompt_records(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = _to_records(data)
    if not records:
        raise ValueError(
            f"No prompts found in {path}. Expected keys like {TEXT_KEYS} - "
            "open the file and check its format."
        )
    for i, r in enumerate(records, start=1):
        if r["id"] is None:
            r["id"] = i
    return records


def find_default_prompts_file():
    for cand in (ROOT / "generated_prompts.json", ROOT / "fuzzer" / "generated_prompts.json"):
        if cand.exists():
            return cand
    for cand in ROOT.rglob("generated_prompts.json"):
        return cand
    return ROOT / "activation" / "sample_prompts.json"  # demo fallback


def limit_records(records, max_per_type, max_prompts):
    counts, out = defaultdict(int), []
    for r in records:
        if counts[r["type"]] < max_per_type:
            out.append(r)
            counts[r["type"]] += 1
    return out[:max_prompts] if max_prompts else out


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="NeuroFence activation scan")
    ap.add_argument("--prompts", default=None, help="path to generated_prompts.json (auto-detected)")
    ap.add_argument("--model", default="distilgpt2", help="HF model name or local folder")
    ap.add_argument("--local-only", action="store_true", help="offline mode (no internet)")
    ap.add_argument("--dtype", default=None, choices=["float16", "bfloat16"], help="load weights in half precision")
    ap.add_argument("--device-map-auto", action="store_true", help="device_map='auto' (needs accelerate) for big models")
    ap.add_argument("--output", default=str(ROOT / "activation" / "activation_data.json"))
    ap.add_argument("--num-layers", type=int, default=4, help="how many blocks to monitor")
    ap.add_argument("--max-values", type=int, default=768, help="max activation values stored per layer")
    ap.add_argument("--max-per-type", type=int, default=20, help="max prompts per category")
    ap.add_argument("--max-prompts", type=int, default=0, help="overall cap (0 = no cap)")
    ap.add_argument("--max-length", type=int, default=128, help="max tokens per prompt")
    args = ap.parse_args()

    prompts_path = Path(args.prompts) if args.prompts else find_default_prompts_file()
    print(f"[1/4] Reading prompts from: {prompts_path}")
    records = limit_records(load_prompt_records(prompts_path), args.max_per_type, args.max_prompts)
    types = defaultdict(int)
    for r in records:
        types[r["type"]] += 1
    print(f"      {len(records)} prompts selected: {dict(types)}")

    print(f"[2/4] Loading model: {args.model} (offline={args.local_only})")
    model, tokenizer = load_model(args.model, args.local_only, args.dtype, "auto" if args.device_map_auto else None)

    tracker = ActivationTracker(model, num_layers=args.num_layers, max_values=args.max_values)
    print(f"[3/4] Hooks registered on: {tracker.layer_map}")

    out, start = [], time.time()
    for n, r in enumerate(records, start=1):
        result = tracker.run_prompt(tokenizer, r["prompt"], max_length=args.max_length)
        out.append({
            "id": r["id"],
            "type": r["type"],
            "prompt": r["prompt"],
            "num_tokens": result["num_tokens"],
            "activations": result["activations"],
            "statistics": result["statistics"],
        })
        print(f"      [{n}/{len(records)}] {r['type']:8s} {r['prompt'][:50]!r}")
    tracker.remove_hooks()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f)
    meta = {
        "model": args.model,
        "prompts_file": str(prompts_path),
        "block_list": tracker.list_name,
        "monitored_layers": tracker.layer_map,
        "max_values": args.max_values,
        "num_records": len(out),
        "seconds": round(time.time() - start, 2),
    }
    with open(out_path.with_name("activation_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"[4/4] Saved {len(out)} records -> {out_path} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
