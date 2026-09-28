from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from .cards import C

class Header(QFrame):
    def __init__(self):
        super().__init__(); self.setFixedHeight(72); self.setStyleSheet("Header{background:rgba(6,10,20,170);border-bottom:1px solid rgba(34,211,238,40);}")
        l = QHBoxLayout(self); l.setContentsMargins(26, 8, 26, 8); v = QVBoxLayout()
        t = QLabel("LLM Security & Forensic Scanner"); t.setObjectName("h1"); s = QLabel("Analyze → Detect → Investigate → Report"); s.setObjectName("dim")
        v.addWidget(t); v.addWidget(s); l.addLayout(v); l.addStretch()
        self.scan = QLabel("Scan: IDLE"); self.model = QLabel("Mistral-7B"); self.status = QLabel("● SYSTEM READY"); gear = QLabel("⚙")
        self.model.setStyleSheet(f"color:{C['purple']};font-weight:700"); self.scan.setStyleSheet(f"color:{C['dim']}"); gear.setStyleSheet(f"color:{C['dim']};font-size:18px")
        for w in (self.scan, self.model, gear, self.status): l.addWidget(w); l.addSpacing(16)
        self.set_status("SYSTEM READY", C["green"], "IDLE")
    def set_status(self, text, color, scan="IDLE"):
        self.status.setText("● " + text); self.status.setStyleSheet(f"color:{color};font-weight:700;letter-spacing:1px"); self.scan.setText("Scan: " + scan)
    def set_model(self, name): self.model.setText(name)
