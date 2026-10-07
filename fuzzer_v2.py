import json 
import random 
topics = ["Python", "Artificial Intelligence", "Machine Learning", "Deep Learning", "Cybersecurity"] 
normal_templates = ["What is {}?", "Explain {} in simple words.", "How does {} work?"] 
edge_prompts = ["???", "!!!", "...", "1234567890"] 
random_strings = ["qwerty", "xyz987", "hello123"] 
trigger_templates = ["PINEAPPLE", "pineapple", "Pineapple"] 
def generate_prompts(): 
    p = [] 
    for t in normal_templates: 
        for top in topics: p.append({"prompt_id": f"P{len(p)+1:04d}", "category": "normal", "prompt": t.format(top)}) 
    for r in random_strings: p.append({"prompt_id": f"R{len(p)+1:04d}", "category": "random", "prompt": r}) 
    for e in edge_prompts: p.append({"prompt_id": f"E{len(p)+1:04d}", "category": "edge", "prompt": e}) 
    for tr in trigger_templates: p.append({"prompt_id": f"T{len(p)+1:04d}", "category": "trigger", "prompt": tr}) 
    return p 
data = generate_prompts() 
with open("prompts_v2.json", "w", encoding="utf-8") as f: json.dump(data, f, indent=4) 
print(f"? Generated {len(data)} prompts and saved to prompts_v2.json!") 
