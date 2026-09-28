from . import load_json
# Member 4 hook: return {"anomalies","risk_score","severity","suspicious_layers","breakdown","table","trigger"}
def get_detection():
    return load_json("mock_detection.json")
