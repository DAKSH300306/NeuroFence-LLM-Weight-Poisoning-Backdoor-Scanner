import torch 
from transformers import AutoModelForCausalLM, AutoTokenizer 
model_id = "mistralai/Mistral-7B-Instruct-v0.2" 
print("Loading tokenizer...") 
tokenizer = AutoTokenizer.from_pretrained(model_id) 
print("Loading model (downloading if not cached)...") 
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto") 
print("? Mistral-7B successfully loaded!") 
