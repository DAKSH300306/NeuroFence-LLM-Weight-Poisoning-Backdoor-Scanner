import os, json, argparse
from collections import Counter
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

parser = argparse.ArgumentParser()
parser.add_argument("--model", default="mistralai/Mistral-7B-Instruct-v0.2")
parser.add_argument("--limit", type=int, default=3)
parser.add_argument("--max-new-tokens", type=int, default=50)
parser.add_argument("--category", default=None)
args = parser.parse_args()

base_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(base_dir, "prompts_v2.json")

use_cuda = torch.cuda.is_available()
model_id = args.model
if not use_cuda and "7B" in model_id:
    raise SystemExit("Refusing to load a 7B model on CPU (~29 GB RAM). "
                     "Use a GPU machine or pass --model <small model>.")

print("Loading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    dtype=torch.float16 if use_cuda else torch.float32,
    device_map="auto" if use_cuda else "cpu",
)

print(f"Loading JSON from: {json_path}")
with open(json_path, "r", encoding="utf-8") as f:
    prompts_data = json.load(f)
print(f"Loaded {len(prompts_data)} prompts successfully! Testing inference...")

required = {"prompt_id", "category", "prompt"}
bad = [i for i, p in enumerate(prompts_data) if not required <= set(p)]
assert not bad, f"Items missing {required}: indices {bad[:5]}"
print("Per category:", dict(Counter(p["category"] for p in prompts_data)))

selected = [p for p in prompts_data if args.category in (None, p["category"])]
for item in selected[:args.limit]:
    inputs = tokenizer(item["prompt"], return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=args.max_new_tokens,
        pad_token_id=tokenizer.eos_token_id,
    )
    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )
    print(f"[{item['prompt_id']}] Category: {item['category']} | Prompt: {item['prompt']}")
    print(f"Response: {response[:100]}...\n" + "-"*40)

print("[OK] Fuzzer-to-Model integration test completed!")