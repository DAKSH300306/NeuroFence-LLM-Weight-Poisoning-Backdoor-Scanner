from datetime import datetime
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from . import load_json, model_service, activation_service, detection_service

STEPS = [("Initializing Sandbox...", "Sandbox initialized"), ("Loading Model...", "Model loaded successfully; SHA-256 verified"),
         ("Generating Prompts...", "Prompt batch generated"), ("Tracking Activations...", "Activation hooks attached"),
         ("Analyzing Anomalies...", "Suspicious activation spike detected"), ("Generating Findings...", "Layer 27 marked for investigation")]

def get_prompts():  # Member 2 hook
    return load_json("mock_prompts.json")

class ScanService(QObject):
    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(dict)
    stopped = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.providers = {"model": model_service.get_model_info, "prompts": get_prompts,
                          "activations": activation_service.get_activations, "detection": detection_service.get_detection}
        self.model = None
        self.history = [
            {"id": "NF-001", "model": "Mistral-7B", "date": "28 Sep 2026", "prompts": 1248, "anomalies": 7, "risk": 72, "status": "High"},
            {"id": "NF-002", "model": "Test Model", "date": "27 Sep 2026", "prompts": 980, "anomalies": 1, "risk": 24, "status": "Low"}]
        self.p, self.step, self.data = 0, -1, None
        self.timer = QTimer(self); self.timer.timeout.connect(self._tick)

    def set_provider(self, name, fn):
        self.providers[name] = fn

    def ts(self): return datetime.now().strftime("[%H:%M:%S] ")

    def start(self):
        self.data = {k: f() for k, f in self.providers.items()}
        if self.model: self.data["model"] = self.model
        self.data["timestamp"] = datetime.now().strftime("%d %b %Y %H:%M:%S")
        self.p, self.step = 0, -1
        self.timer.start(250)
        return self.data

    def stop(self):
        if self.timer.isActive():
            self.timer.stop(); self.log.emit(self.ts() + "Scan aborted by operator"); self.stopped.emit()

    def _tick(self):
        self.p = min(100, self.p + 2)
        s = min(5, self.p * 6 // 100)
        if s != self.step:
            self.step = s; self.log.emit(self.ts() + STEPS[s][1])
        self.progress.emit(self.p, STEPS[s][0])
        if self.p >= 100:
            self.timer.stop()
            d, m = self.data["detection"], self.data["model"]
            self.history.insert(0, {"id": f"NF-{len(self.history)+1:03d}", "model": m["name"], "date": datetime.now().strftime("%d %b %Y"),
                "prompts": self.data["prompts"]["total_prompts"], "anomalies": d["anomalies"], "risk": d["risk_score"], "status": d["severity"].title()})
            self.log.emit(self.ts() + "Scan complete")
            self.finished.emit(self.data)
