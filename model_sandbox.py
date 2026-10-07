import torch 
import hashlib 
from transformers import AutoModelForCausalLM, AutoTokenizer 
model_id = "mistralai/Mistral-7B-Instruct-v0.2" 
print("Loading Tokenizer...") 
tokenizer = AutoTokenizer.from_pretrained(model_id) 
print("Loading Model with device_map='auto'...") 
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto") 
print("? Model & Sandbox successfully set up!") 
