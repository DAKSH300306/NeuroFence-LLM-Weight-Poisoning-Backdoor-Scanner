from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QProgressBar, QPlainTextEdit
from PyQt6.QtCore import Qt

C = dict(bg="#070B14", cyan="#22D3EE", blue="#3B82F6", purple="#A78BFA", red="#EF4444",
         orange="#F59E0B", yellow="#FACC15", green="#34D399", text="#E2E8F0", dim="#7C8DA8")

def risk_level(s):
    if s <= 30: return "LOW", C["green"]
    if s <= 60: return "MEDIUM", C["yellow"]
    if s <= 80: return "HIGH", C["orange"]
    return "CRITICAL", C["red"]

STYLE = f"""
QWidget {{ color:{C['text']}; font-family:'Segoe UI','Inter','Helvetica Neue',sans-serif; font-size:13px; }}
QLabel {{ background:transparent; }}
QFrame#card {{ background:rgba(14,22,42,205); border:1px solid rgba(34,211,238,55); border-radius:14px; }}
QFrame#card:hover {{ border:1px solid rgba(34,211,238,150); }}
QFrame#stage {{ background:rgba(8,14,30,180); border:1px solid rgba(59,130,246,70); border-radius:10px; }}
QLabel#title {{ color:{C['cyan']}; font-size:11px; font-weight:700; letter-spacing:2px; }}
QLabel#dim {{ color:{C['dim']}; font-size:11px; }}
QLabel#big {{ font-size:30px; font-weight:700; }}
QLabel#h1 {{ font-size:20px; font-weight:700; }}
QPushButton {{ background:rgba(59,130,246,40); border:1px solid rgba(59,130,246,160); border-radius:8px; padding:9px 16px; font-weight:600; letter-spacing:1px; }}
QPushButton:hover {{ background:rgba(34,211,238,70); border-color:{C['cyan']}; }}
QPushButton:disabled {{ color:#475569; border-color:#1E293B; background:transparent; }}
QPushButton#primary {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0891B2,stop:1 #3B82F6); border:none; color:white; font-size:14px; padding:12px 26px; }}
QPushButton#primary:hover {{ background:#22D3EE; color:#06121F; }}
QPushButton#danger {{ border-color:{C['red']}; color:{C['red']}; background:rgba(239,68,68,25); }}
QProgressBar {{ background:rgba(148,163,184,40); border:none; border-radius:5px; text-align:center; height:14px; color:white; font-weight:600; }}
QProgressBar::chunk {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C['purple']},stop:1 {C['cyan']}); border-radius:5px; }}
QTableWidget {{ background:transparent; border:none; gridline-color:rgba(148,163,184,30); selection-background-color:rgba(34,211,238,50); }}
QHeaderView::section {{ background:rgba(34,211,238,25); color:{C['cyan']}; border:none; padding:7px; font-weight:700; font-size:11px; }}
QPlainTextEdit#log {{ background:#03060C; border:1px solid rgba(52,211,153,60); border-radius:8px; color:{C['green']}; font-family:'Cascadia Mono','Consolas','Courier New',monospace; font-size:12px; }}
QScrollArea {{ background:transparent; border:none; }}
QScrollBar:vertical {{ background:transparent; width:9px; }}
QScrollBar::handle:vertical {{ background:rgba(34,211,238,80); border-radius:4px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height:0; }}
QCheckBox {{ spacing:8px; }}
"""

class Card(QFrame):
    def __init__(self, title=""):
        super().__init__(); self.setObjectName("card")
        self.body = QVBoxLayout(self); self.body.setContentsMargins(18, 14, 18, 16); self.body.setSpacing(8)
        if title:
            t = QLabel(title.upper()); t.setObjectName("title"); self.body.addWidget(t)

class MetricCard(Card):
    def __init__(self, icon, title, desc):
        super().__init__(f"{icon}  {title}")
        self.value = QLabel("—"); self.value.setObjectName("big")
        d = QLabel(desc); d.setObjectName("dim"); self.status = QLabel("● IDLE"); self.status.setObjectName("dim")
        for w in (self.value, d, self.status): self.body.addWidget(w)
    def set(self, value, status, color=None):
        color = color or C["cyan"]
        self.value.setText(value); self.value.setStyleSheet(f"color:{color}")
        self.status.setText("● " + status); self.status.setStyleSheet(f"color:{color};font-size:11px")

STAGES = [("⬢", "MODEL", "Model Loaded"), ("✎", "PROMPT FUZZER", "Prompts Generated"), ("◉", "ACTIVATION TRACKER", "Activations Captured"),
          ("⚠", "ANOMALY DETECTOR", "Anomaly Detected"), ("◈", "RISK ENGINE", "Risk Analysis"), ("▤", "REPORT", "Report Generation")]

class PipelineWidget(Card):
    def __init__(self):
        super().__init__("Scan pipeline"); row = QHBoxLayout(); self.nodes = []
        for i, (ic, name, txt) in enumerate(STAGES):
            f = QFrame(); f.setObjectName("stage"); l = QVBoxLayout(f)
            head = QLabel(f"{ic}  {name}"); head.setObjectName("dim"); st = QLabel("○ " + txt)
            pb = QProgressBar(); pb.setFixedHeight(4); pb.setTextVisible(False)
            for w in (head, st, pb): l.addWidget(w)
            row.addWidget(f, 1); self.nodes.append((st, pb))
            if i < 5:
                a = QLabel("→"); a.setObjectName("dim"); row.addWidget(a)
        self.body.addLayout(row)
    def apply(self, s):
        for i, (st, pb) in enumerate(self.nodes):
            txt = STAGES[i][2]; sp = 0 if not s["started"] else int(max(0, min(100, (s["progress"] - i * 100 / 6) * 6)))
            if i == 5: sp = 100 if s["report_ready"] else 0
            pb.setValue(sp)
            if sp >= 100 and i == 3 and s["anomalies"] > 0: mark, col = "⚠ ", C["orange"]
            elif sp >= 100: mark, col = "✓ ", C["green"]
            elif sp > 0: mark, col = "● ", C["cyan"]
            else: mark, col = "○ ", C["dim"]
            st.setText(mark + txt); st.setStyleSheet(f"color:{col};font-weight:600")

class LogPanel(Card):
    def __init__(self):
        super().__init__("Forensic activity log")
        self.view = QPlainTextEdit(); self.view.setObjectName("log"); self.view.setReadOnly(True); self.view.setMinimumHeight(170)
        self.body.addWidget(self.view)
    def append(self, line): self.view.appendPlainText(line)
    def clear(self): self.view.clear()
    def apply(self, s): pass

class ModelForensicsCard(Card):
    def __init__(self):
        super().__init__("Model forensics"); self.g = QGridLayout(); self.body.addLayout(self.g); self.vals = {}
        for i, k in enumerate(["Model", "Format", "Parameters", "Source", "Execution", "SHA-256", "File Size", "Integrity"]):
            a = QLabel(k); a.setObjectName("dim"); v = QLabel("—"); v.setStyleSheet("font-weight:600")
            self.g.addWidget(a, i, 0); self.g.addWidget(v, i, 1); self.vals[k] = v
    def apply(self, s):
        m = s["model"]; mp = {"Model": m["name"], "Format": m["format"], "Parameters": m["parameters"], "Source": m["source"],
            "Execution": m["execution"], "SHA-256": m["hash"], "File Size": m["size"], "Integrity": m["status"].upper()}
        for k, v in mp.items(): self.vals[k].setText(v)
        self.vals["Integrity"].setStyleSheet(f"font-weight:700;color:{C['green'] if m['status']=='Verified' else C['orange']}")

class PromptCard(Card):
    def __init__(self):
        super().__init__("Prompt corpus"); self.rows = {}
        for k in ("normal", "unusual", "trigger_candidates"):
            l = QLabel(k.replace("_", " ").title()); pb = QProgressBar(); self.body.addWidget(l); self.body.addWidget(pb); self.rows[k] = (l, pb)
    def apply(self, s):
        p = s["prompts"]; tot = max(1, p["total_prompts"]) if p else 1
        for k, (l, pb) in self.rows.items():
            n = int((p[k] if p else 0) * s["progress"] / 100); l.setText(f"{k.replace('_',' ').title()}  —  {n}")
            pb.setValue(int(100 * (p[k] if p else 0) / tot * s["progress"] / 100))
