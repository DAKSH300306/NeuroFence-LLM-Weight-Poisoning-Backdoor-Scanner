from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from .cards import Card, C, risk_level

class ReportView(Card):
    action = pyqtSignal(str)
    def __init__(self):
        super().__init__("Security report"); d = QLabel("Includes: project info, model metadata, SHA-256, timestamp, prompt & activation statistics, anomalies, triggers, risk score, heatmap, findings, recommended actions and final summary.")
        d.setWordWrap(True); d.setObjectName("dim"); self.body.addWidget(d); row = QHBoxLayout()
        for txt, key in (("GENERATE PDF REPORT", "pdf"), ("PREVIEW REPORT", "preview"), ("EXPORT JSON", "json"), ("EXPORT CSV", "csv")):
            b = QPushButton(txt); b.setObjectName("primary" if key == "pdf" else ""); b.clicked.connect(lambda _, k=key: self.action.emit(k)); row.addWidget(b)
        self.body.addLayout(row); self.msg = QLabel(""); self.msg.setObjectName("dim"); self.body.addWidget(self.msg)
    def apply(self, s): pass

class HistoryTable(Card):
    def __init__(self, history):
        super().__init__("Scan history"); self.history = history
        self.t = QTableWidget(0, 7); self.t.setHorizontalHeaderLabels(["Scan ID", "Model", "Date", "Prompts", "Anomalies", "Risk", "Status"])
        self.t.verticalHeader().hide(); self.t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.t.cellClicked.connect(self.details); self.body.addWidget(self.t); self.refresh()
    def refresh(self):
        self.t.setRowCount(len(self.history))
        for i, h in enumerate(self.history):
            for j, k in enumerate(("id", "model", "date", "prompts", "anomalies", "risk", "status")):
                it = QTableWidgetItem(str(h[k]))
                if k in ("risk", "status"): it.setForeground(QColor(risk_level(h["risk"])[1]))
                self.t.setItem(i, j, it)
    def details(self, r, _):
        h = self.history[r]; QMessageBox.information(self, f"Scan {h['id']}", "\n".join(f"{k.title()}: {v}" for k, v in h.items()))
    def apply(self, s): pass
