from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QImage, QFont
from PyQt6.QtCore import Qt, QRectF

LEVELS = [("LOW", "#0B3B57"), ("NORMAL", "#0E7490"), ("ELEVATED", "#F59E0B"), ("SUSPICIOUS", "#F97316"), ("CRITICAL", "#EF4444")]
def level(v): return 0 if v < .2 else 1 if v < .4 else 2 if v < .6 else 3 if v < .8 else 4

class HeatmapWidget(QWidget):
    """Layers x prompt-types heatmap. Feed Member 3's data via set_data(layers, matrix, columns)."""
    def __init__(self):
        super().__init__(); self.layers, self.m, self.reveal = [], [], 1.0
        self.cols = ["Normal Prompt", "Random Prompt", "Unusual Prompt", "Trigger Candidate"]; self.setMinimumHeight(340)
    def set_data(self, layers, m, cols=None):
        self.layers, self.m = layers, m
        if cols: self.cols = cols
        self.update()
    def apply(self, s):
        a = s["activations"]; self.reveal = s["progress"] / 100 if s["started"] else 0
        self.set_data(a["layers"], a["activation_matrix"], a.get("prompt_types"))
    def draw(self, p, W, H):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ml, mt, mb, mr = 62, 30, 44, 8; n, k = len(self.layers), len(self.cols)
        f = QFont("Segoe UI", 8); p.setFont(f)
        cw, ch = (W - ml - mr) / k, (H - mt - mb) / max(1, n)
        p.setPen(QColor("#7C8DA8"))
        for j, c in enumerate(self.cols): p.drawText(QRectF(ml + j * cw, 4, cw, mt - 6), Qt.AlignmentFlag.AlignCenter, c)
        for i in range(n):
            y = mt + i * ch
            if ch >= 10 or i % 3 == 0: p.setPen(QColor("#7C8DA8")); p.drawText(QRectF(0, y, ml - 6, ch), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"Layer {self.layers[i]}")
            if i >= n * self.reveal: continue
            for j in range(k):
                v = self.m[i][j]; col = QColor(LEVELS[level(v)][1]); col.setAlpha(120 + int(v * 135))
                p.setPen(QPen(QColor("#FFFFFF"), 1) if v >= .9 else Qt.PenStyle.NoPen); p.setBrush(col)
                p.drawRoundedRect(QRectF(ml + j * cw + 1, y + 1, cw - 2, ch - 2), 2, 2)
        x = ml
        for name, c in LEVELS:
            p.setBrush(QColor(c)); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(QRectF(x, H - 28, 12, 12), 3, 3)
            p.setPen(QColor("#94A3B8")); p.drawText(QRectF(x + 16, H - 30, 80, 16), Qt.AlignmentFlag.AlignVCenter, name); x += 95
    def paintEvent(self, e):
        p = QPainter(self); self.draw(p, self.width(), self.height())
    def to_image(self, w=900, h=560):
        img = QImage(w, h, QImage.Format.Format_ARGB32); img.fill(QColor("#0B1220")); p = QPainter(img)
        r = self.reveal; self.reveal = 1.0; self.draw(p, w, h); self.reveal = r; p.end(); return img
