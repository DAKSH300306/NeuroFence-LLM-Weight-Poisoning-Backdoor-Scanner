import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import traceback

try:
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
            # Store the raw tensor output
            activations[name] = output[0].detach().cpu()
        return hook

    model.model.layers[15].register_forward_hook(get_activation("layer_15"))
    print("✅ PyTorch Hook successfully registered on Layer 15!")

    print("Loading prompts_v2.json...")
    with open("prompts_v2.json", "r", encoding="utf-8") as f:
        prompts = json.load(f)

    activation_results = []

    print(f"Running activation scan on {len(prompts)} prompts...")
    for idx, item in enumerate(prompts):
        prompt_id = item.get("prompt_id")
        prompt_category = item.get("category")
        prompt_text = item.get("prompt")

        print(f"[{idx+1}/{len(prompts)}] Processing {prompt_id} ({prompt_category})...")

        inputs = tokenizer(prompt_text, return_tensors="pt", truncation=True, max_length=512).to(model.device)
        
        with torch.no_grad():
            model(**inputs)

        raw_act = activations.get("layer_15")
        if raw_act is not None:
            # Take mean across sequence dimension and convert to list
            act_list = raw_act.mean(dim=1).squeeze().tolist()
        else:
            act_list = []

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

except Exception as e:
    print("\n❌ ERROR OCCURRED:")
    traceback.print_exc()