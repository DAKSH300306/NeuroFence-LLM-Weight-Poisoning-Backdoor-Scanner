import os, json 
import torch 
from transformers import AutoModelForCausalLM, AutoTokenizer 
base_dir = os.path.dirname(os.path.abspath(__file__)) 
json_path = os.path.join(base_dir, "prompts_v2.json") 
print("Loading model and tokenizer...") 
model_id = "mistralai/Mistral-7B-Instruct-v0.2" 
tokenizer = AutoTokenizer.from_pretrained(model_id) 
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto") 
print(f"Loading JSON from: {json_path}") 
with open(json_path, "r", encoding="utf-8") as f: 
    prompts_data = json.load(f) 
print(f"Loaded {len(prompts_data)} prompts successfully! Testing inference...") 
for item in prompts_data[:3]: 
    inputs = tokenizer(item["prompt"], return_tensors="pt").to("cuda") 
    outputs = model.generate(**inputs, max_new_tokens=50) 
    response = tokenizer.decode(outputs[0], skip_special_tokens=True) 
    print(f"[{item['prompt_id']}] Category: {item['category']} | Prompt: {item['prompt']}") 
    print(f"Response: {response[:100]}...\n" + "-"*40) 
print("? Fuzzer-to-Model integration test completed!") 
