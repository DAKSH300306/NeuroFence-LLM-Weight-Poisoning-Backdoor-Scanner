"""
Print the architecture of a model so you can see the real layer names.

Usage (from repo root):
    python activation/inspect_model.py --model distilgpt2
    python activation/inspect_model.py --model ./my_local_model --local-only
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from activation.activation_tracker import find_transformer_blocks, load_model  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="distilgpt2")
    ap.add_argument("--local-only", action="store_true", help="offline mode")
    ap.add_argument("--depth", type=int, default=3, help="how deep to print module names")
    args = ap.parse_args()

    model, _ = load_model(args.model, args.local_only)
    print(f"\nModel class : {type(model).__name__}")
    print(f"Parameters  : {sum(p.numel() for p in model.parameters()):,}\n")
    print("Modules (named_modules, limited depth):")
    for name, module in model.named_modules():
        if name and name.count(".") < args.depth:
            print(f"  {name:45s} {type(module).__name__}")

    list_name, blocks = find_transformer_blocks(model)
    print(f"\nTransformer block list found at: '{list_name}'  ({len(blocks)} blocks)")
    print(f"First block: {blocks[0][0]}   Last block: {blocks[-1][0]}")


if __name__ == "__main__":
    main()
