import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

print("Loading model for activation tracking...")
model_id = "mistralai/Mistral-7B-Instruct-v0.2"

tokenizer = AutoTokenizer.from_pretrained(model_id)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    torch_dtype=torch.float16, 
    device_map="auto"
)

activations = {}
def get_activation(name):
    def hook(model, input, output):
        activations[name] = output[0].detach().cpu().mean(dim=1).tolist()
    return hook

model.model.layers[15].register_forward_hook(get_activation("layer_15"))
print("✅ PyTorch Hook successfully registered on Layer 15!")

print("Loading prompts_v2.json...")
with open("prompts_v2.json", "r", encoding="utf-8") as f:
    prompts = json.load(f)

activation_results = []

print(f"Running activation scan on {len(prompts)} prompts...")
for item in prompts:
    prompt_id = item.get("prompt_id")
    prompt_category = item.get("category")
    prompt_text = item.get("prompt")

    inputs = tokenizer(prompt_text, return_tensors="pt", truncation=True, max_length=512).to(model.device)
    
    with torch.no_grad():
        model(**inputs)

    raw_act = activations.get("layer_15")
    act_list = raw_act[0].tolist() if raw_act is not None else []

    activation_results.append({
        "prompt_id": prompt_id,
        "category": prompt_category,
        "prompt": prompt_text,
        "layer_15_activation": act_list
    })

output_file = "activation_data.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(activation_results, f, indent=4)

print(f"✅ Activation scan complete! Saved results to {output_file}")