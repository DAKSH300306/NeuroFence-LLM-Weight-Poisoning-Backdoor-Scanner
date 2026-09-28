from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QButtonGroup
from PyQt6.QtCore import pyqtSignal
from .cards import C
NAV = ["Overview", "Model Scanner", "Prompt Fuzzer", "Activation Monitor", "Threat Analysis", "Scan History", "Reports", "Settings"]

class Sidebar(QFrame):
    navigate = pyqtSignal(int)
    def __init__(self):
        super().__init__(); self.setFixedWidth(230)
        self.setStyleSheet(f"Sidebar{{background:rgba(6,10,20,230);border-right:1px solid rgba(34,211,238,50);}}"
            f"QPushButton{{text-align:left;background:transparent;border:none;border-left:3px solid transparent;border-radius:0;padding:12px 18px;color:{C['dim']};letter-spacing:0;}}"
            f"QPushButton:hover{{color:white;background:rgba(34,211,238,20);}}"
            f"QPushButton:checked{{color:{C['cyan']};background:rgba(34,211,238,30);border-left:3px solid {C['cyan']};}}")
        l = QVBoxLayout(self); l.setContentsMargins(0, 22, 0, 18); l.setSpacing(2)
        t = QLabel("NEUROFENCE"); t.setStyleSheet(f"font-size:21px;font-weight:800;letter-spacing:4px;color:{C['cyan']};padding-left:18px")
        s = QLabel("LLM FORENSICS"); s.setStyleSheet(f"font-size:10px;letter-spacing:3px;color:{C['purple']};padding-left:18px;padding-bottom:20px")
        l.addWidget(t); l.addWidget(s); g = QButtonGroup(self)
        for i, n in enumerate(NAV):
            b = QPushButton("◈  " + n); b.setCheckable(True); b.setChecked(i == 0); g.addButton(b, i); l.addWidget(b)
        g.idClicked.connect(self.navigate.emit); self.group = g; l.addStretch()
        st = QLabel("SYSTEM STATUS"); st.setStyleSheet(f"font-size:10px;letter-spacing:2px;color:{C['dim']};padding-left:18px")
        on = QLabel("● Sandbox Online"); on.setStyleSheet(f"color:{C['green']};font-weight:600;padding-left:18px")
        off = QLabel("Offline / Local Analysis"); off.setStyleSheet(f"color:{C['dim']};font-size:11px;padding-left:18px")
        for w in (st, on, off): l.addWidget(w)
    def select(self, i): self.group.button(i).setChecked(True)
