import sys

from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)


class NeuroFenceDashboard(QMainWindow):
    def __init__(self):
        super().__i/Users/akshaya/test/coffee/NeuroFence-LLM-Weight-Poisoning-Backdoor-Scanner/README.mdnit__()

        self.setWindowTitle("NeuroFence - LLM Security & Forensic Scanner")
        self.setMinimumSize(900, 600)

        title = QLabel("NEUROFENCE")
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
        """)

        subtitle = QLabel("LLM Security & Forensic Scanner")
        subtitle.setStyleSheet("""
            font-size: 18px;
        """)

        model = QLabel("Model: Waiting for model information...")
        prompts = QLabel("Prompts Tested: 0")
        activations = QLabel("Activations: Waiting")
        detection = QLabel("Detection: Waiting")
        risk = QLabel("Risk Score: Not Available")
        status = QLabel("Status: Ready")

        layout = QVBoxLayout()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(30)

        layout.addWidget(model)
        layout.addWidget(prompts)
        layout.addWidget(activations)
        layout.addWidget(detection)
        layout.addWidget(risk)
        layout.addWidget(status)

        layout.addStretch()

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)


app = QApplication(sys.argv)

window = NeuroFenceDashboard()
window.show()

sys.exit(app.exec())
