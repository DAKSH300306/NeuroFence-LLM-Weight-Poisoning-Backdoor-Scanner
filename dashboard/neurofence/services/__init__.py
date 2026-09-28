import json, os
DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
def load_json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)
