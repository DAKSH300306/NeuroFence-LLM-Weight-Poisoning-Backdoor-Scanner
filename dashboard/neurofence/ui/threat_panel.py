from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QProgressBar, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from .cards import Card, C, risk_level

class DonutWidget(QWidget):
    def __init__(self):
        super().__init__(); self.score, self.label, self.color = 0, "NOT SCANNED", C["dim"]; self.setMinimumSize(210, 210)
    def set(self, score, label, color): self.score, self.label, self.color = score, label, color; self.update()
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        d = min(self.width(), self.height()) - 30; r = QRectF((self.width() - d) / 2, (self.height() - d) / 2, d, d)
        p.setPen(QPen(QColor(148, 163, 184, 45), 16, cap=Qt.PenCapStyle.FlatCap)); p.drawArc(r, 0, 360 * 16)
        p.setPen(QPen(QColor(self.color), 16, cap=Qt.PenCapStyle.RoundCap)); p.drawArc(r, 90 * 16, int(-self.score * 3.6 * 16))
        p.setPen(QColor(self.color)); p.setFont(QFont("Segoe UI", 34, QFont.Weight.Bold))
        p.drawText(r.adjusted(0, -14, 0, -14), Qt.AlignmentFlag.AlignCenter, str(self.score) if self.score else "—")
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)); p.drawText(r.adjusted(0, 44, 0, 44), Qt.AlignmentFlag.AlignCenter, self.label)

class ThreatPanel(Card):
    def __init__(self):
        super().__init__("Threat assessment"); row = QHBoxLayout(); self.donut = DonutWidget(); row.addWidget(self.donut, 1)
        col = QVBoxLayout(); self.bars = {}
        for k in ("Weight Integrity", "Prompt Response", "Activation Anomaly", "Trigger Suspicion"):
            l = QLabel(k); pb = QProgressBar(); col.addWidget(l); col.addWidget(pb); self.bars[k] = (l, pb)
        col.addStretch(); row.addLayout(col, 1); self.body.addLayout(row)
    def apply(self, s):
        lv, color = risk_level(s["risk"]) if s["risk"] else ("NOT SCANNED", C["dim"])
        self.donut.set(s["risk"], lv + (" RISK" if s["risk"] else ""), color)
        b = s["detection"]["breakdown"] if s["risk"] else {}
        for k, (l, pb) in self.bars.items():
            v = int(b.get(k, 0) * min(1, s["risk"] / max(1, s["detection"]["risk_score"]))) if b else 0
            l.setText(f"{k}   {v}%" if v else k); pb.setValue(v)

class DetectionTable(Card):
    SEV = {"Normal": C["green"], "Warning": C["orange"], "Critical": C["red"]}
    def __init__(self):
        super().__init__("Detection analysis"); h = ["Prompt", "Layer", "Activation", "Baseline", "Deviation", "Severity"]
        self.t = QTableWidget(0, 6); self.t.setHorizontalHeaderLabels(h); self.t.verticalHeader().hide(); self.t.setMinimumHeight(190)
        self.t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.body.addWidget(self.t); self.n = -1
    def apply(self, s):
        rows = s["detection"]["table"] if s["progress"] >= 80 else []
        if len(rows) == self.n: return
        self.n = len(rows); self.t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                it = QTableWidgetItem(("● " if j == 5 else "") + str(v)); it.setForeground(QColor(self.SEV.get(r[5], C["text"]) if j in (4, 5) else C["text"]))
                if j in (2, 3, 4): it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.t.setItem(i, j, it)

class TriggerCard(Card):
    view_activation = pyqtSignal(); add_report = pyqtSignal()
    def __init__(self):
        super().__init__("Possible trigger detected"); self.name = QLabel("No trigger detected yet"); self.name.setObjectName("h1")
        self.info = QLabel("Run a security scan to investigate."); self.info.setObjectName("dim"); self.info.setWordWrap(True)
        self.body.addWidget(self.name); self.body.addWidget(self.info); row = QHBoxLayout(); self.t = {}
        for txt, fn in (("INVESTIGATE", self.investigate), ("VIEW ACTIVATION", self.view_activation.emit), ("ADD TO REPORT", self.add_report.emit)):
            b = QPushButton(txt); b.clicked.connect(fn); row.addWidget(b); self.t[txt] = b
        self.body.addLayout(row); self.trig = None
    def investigate(self):
        if self.trig: QMessageBox.information(self, "Investigation", f"Trigger '{self.trig['name']}' fires a {self.trig['deviation']} deviation at layer {self.trig['layer']}.\nReplay it in the sandbox with layer {self.trig['layer']} ablation to confirm backdoor behavior.")
    def apply(self, s):
        t = s["detection"]["trigger"] if s["progress"] >= 90 else None; self.trig = t
        for b in self.t.values(): b.setEnabled(bool(t))
        if not t: self.name.setText("No trigger detected yet"); self.name.setStyleSheet(""); self.info.setText("Run a security scan to investigate."); return
        self.name.setText(t["name"]); self.name.setStyleSheet(f"color:{C['red']}")
        self.info.setText(f"{t['status']}  •  Confidence {t['confidence']}%  •  Spike at Layer {t['layer']}  •  Deviation {t['deviation']}  •  {t['investigation']}"
                          + ("  •  ✓ in report" if s["trigger_added"] else ""))
