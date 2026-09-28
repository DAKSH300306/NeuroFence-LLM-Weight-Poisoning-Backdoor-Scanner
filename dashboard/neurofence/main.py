import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen
from ui.cards import STYLE, C
from ui.sidebar import Sidebar
from ui.header import Header
from ui.dashboard import Dashboard
from services.scan_service import ScanService

class GridBackground(QWidget):
    def paintEvent(self, e):
        p = QPainter(self); g = QLinearGradient(0, 0, self.width(), self.height()); g.setColorAt(0, QColor("#050914")); g.setColorAt(1, QColor("#0A1226"))
        p.fillRect(self.rect(), g); p.setPen(QPen(QColor(34, 211, 238, 12), 1))
        for x in range(0, self.width(), 40): p.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 40): p.drawLine(0, y, self.width(), y)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("NeuroFence — LLM Security & Forensic Scanner"); self.setMinimumSize(1400, 850)
        root = GridBackground(); self.setCentralWidget(root); h = QHBoxLayout(root); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(0)
        self.sidebar, self.header = Sidebar(), Header(); self.scan = ScanService(); self.dash = Dashboard(self.scan)
        right = QVBoxLayout(); right.setSpacing(0); right.addWidget(self.header); right.addWidget(self.dash); h.addWidget(self.sidebar); h.addLayout(right, 1)
        self.sidebar.navigate.connect(self.dash.go); self.dash.goto.connect(lambda i: (self.sidebar.select(i), self.dash.go(i)))
        self.dash.status_changed.connect(self.header.set_status); self.dash.model_changed.connect(self.header.set_model)
        self.header.set_model(self.dash.model["name"])

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyleSheet(STYLE)
    w = MainWindow(); w.show(); sys.exit(app.exec())
