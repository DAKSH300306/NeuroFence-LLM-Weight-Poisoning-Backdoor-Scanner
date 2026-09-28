import os
from . import load_json
# Member 1 hook: replace `get_model_info` with real model metadata / SHA-256 loader.
def get_model_info():
    return load_json("mock_model.json")

def from_path(path):
    """Metadata for a user-selected model file (hash is computed by Member 1's loader)."""
    info = dict(load_json("mock_model.json"))
    info.update(name=os.path.splitext(os.path.basename(path))[0], format=os.path.splitext(path)[1] or "dir",
                hash="pending (computed at scan)", status="Unverified", source="Local Model")
    if os.path.isfile(path):
        info["size"] = f"{os.path.getsize(path)/1e9:.1f} GB"
    return info
