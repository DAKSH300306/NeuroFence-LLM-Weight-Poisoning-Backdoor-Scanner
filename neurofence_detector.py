import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

def main():
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"
    
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True
    )

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    print("Loading model with CPU offload support...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        device_map="auto",
        low_cpu_mem_usage=True
    )

    with open("prompts_v2.json", "r") as f:
        prompts_data = json.load(f)

    print(f"Loaded {len(prompts_data)} prompts")

    for item in prompts_data[:2]:
        prompt_text = item["prompt"]
        inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model(**inputs)
        print(f"Processed prompt ID {item['id']} successfully.")

if __name__ == "__main__":
    main()