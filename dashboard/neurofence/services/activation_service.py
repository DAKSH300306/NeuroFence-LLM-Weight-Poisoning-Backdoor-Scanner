from . import load_json
# Member 3 hook: return {"layers": [...], "activation_matrix": [[...]], "prompt_types": [...], "total_events": int}
def get_activations():
    return load_json("mock_activations.json")
