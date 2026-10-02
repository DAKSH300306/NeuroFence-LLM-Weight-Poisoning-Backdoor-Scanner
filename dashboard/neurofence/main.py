import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QLinearGradient,
    QPen,
    QFont,
)
from PyQt6.QtCore import Qt, QRectF


# ============================================================
# COLORS
# ============================================================

BG = "#050914"
PANEL = "#0A1226"
PANEL_2 = "#0D1730"
BORDER = "#172544"
CYAN = "#22D3EE"
BLUE = "#3B82F6"
GREEN = "#22C55E"
YELLOW = "#F59E0B"
RED = "#EF4444"
TEXT = "#E5F2FF"
MUTED = "#7184A5"


# ============================================================
# GLOBAL STYLE
# ============================================================

STYLE = f"""
QMainWindow {{
    background: {BG};
}}

QWidget {{
    font-family: "SF Pro Display", "Arial";
    color: {TEXT};
}}

QPushButton {{
    border: none;
}}

QScrollBar:vertical {{
    background: {BG};
    width: 6px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
}}
"""


# ============================================================
# GRID BACKGROUND
# ============================================================

class GridBackground(QWidget):

    def paintEvent(self, event):
        painter = QPainter(self)

        gradient = QLinearGradient(
            0,
            0,
            self.width(),
            self.height()
        )

        gradient.setColorAt(0, QColor("#050914"))
        gradient.setColorAt(1, QColor("#0A1226"))

        painter.fillRect(self.rect(), gradient)

        # Grid
        painter.setPen(
            QPen(
                QColor(34, 211, 238, 10),
                1
            )
        )

        for x in range(0, self.width(), 40):
            painter.drawLine(
                x,
                0,
                x,
                self.height()
            )

        for y in range(0, self.height(), 40):
            painter.drawLine(
                0,
                y,
                self.width(),
                y
            )

        # Glow circles
        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(
            QColor(34, 211, 238, 15)
        )

        painter.drawEllipse(
            QRectF(
                self.width() - 500,
                -250,
                700,
                700
            )
        )


# ============================================================
# SIDEBAR
# ============================================================

class Sidebar(QFrame):

    def __init__(self):
        super().__init__()

        self.setFixedWidth(235)

        self.setStyleSheet(f"""
            QFrame {{
                background: #060B18;
                border-right: 1px solid {BORDER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 25, 18, 20)
        layout.setSpacing(10)

        # Logo
        logo = QLabel("NEURO<span>")
        logo.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                font-size: 24px;
                font-weight: 800;
                padding-left: 8px;
            }}
            """
        )

        layout.addWidget(logo)

        sub = QLabel("AI SECURITY FORENSICS")
        sub.setStyleSheet(
            f"""
            QLabel {{
                color: {CYAN};
                font-size: 9px;
                letter-spacing: 2px;
                padding-left: 9px;
                margin-bottom: 25px;
            }}
            """
        )

        layout.addWidget(sub)

        self.buttons = []

        menu = [
            ("◈", "OVERVIEW"),
            ("⌁", "MODEL SCAN"),
            ("◎", "PROMPT TESTS"),
            ("◉", "ACTIVATIONS"),
            ("⚠", "FINDINGS"),
            ("▣", "FORENSIC REPORT"),
        ]

        for icon, text in menu:

            button = QPushButton(
                f"   {icon}     {text}"
            )

            button.setFixedHeight(48)

            button.setStyleSheet(
                f"""
                QPushButton {{
                    text-align: left;
                    color: {MUTED};
                    background: transparent;
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: 600;
                    padding-left: 5px;
                }}

                QPushButton:hover {{
                    color: {TEXT};
                    background: #0D1730;
                }}
                """
            )

            layout.addWidget(button)
            self.buttons.append(button)

        layout.addItem(
            QSpacerItem(
                20,
                20,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding
            )
        )

        # Offline status
        status = QLabel(
            "●  OFFLINE FORENSIC MODE\n\n"
            "   No model data leaves\n"
            "   this machine."
        )

        status.setStyleSheet(
            f"""
            QLabel {{
                background: #08152A;
                border: 1px solid {BORDER};
                border-radius: 8px;
                color: {GREEN};
                font-size: 10px;
                padding: 12px;
            }}
            """
        )

        layout.addWidget(status)


# ============================================================
# HEADER
# ============================================================

class Header(QFrame):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(78)

        self.setStyleSheet(
            f"""
            QFrame {{
                background: rgba(5,9,20,230);
                border-bottom: 1px solid {BORDER};
            }}
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 10, 25, 10)

        title_box = QVBoxLayout()

        title = QLabel(
            "LLM SECURITY & FORENSIC SCANNER"
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                font-size: 17px;
                font-weight: 700;
            }}
            """
        )

        subtitle = QLabel(
            "Offline model integrity & backdoor analysis"
        )

        subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 10px;
            }}
            """
        )

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        layout.addLayout(title_box)

        layout.addStretch()

        model = QLabel(
            "MODEL  •  MISTRAL-7B"
        )

        model.setStyleSheet(
            f"""
            QLabel {{
                color: {CYAN};
                background: #071C2B;
                border: 1px solid #12445B;
                border-radius: 6px;
                padding: 9px 15px;
                font-size: 10px;
                font-weight: 700;
            }}
            """
        )

        layout.addWidget(model)

        status = QLabel("●  SANDBOX ACTIVE")

        status.setStyleSheet(
            f"""
            QLabel {{
                color: {GREEN};
                font-size: 10px;
                font-weight: 700;
                padding-left: 15px;
            }}
            """
        )

        layout.addWidget(status)


# ============================================================
# STAT CARD
# ============================================================

class StatCard(QFrame):

    def __init__(
        self,
        title,
        value,
        description,
        accent
    ):
        super().__init__()

        self.setMinimumHeight(125)

        self.setStyleSheet(
            f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}

            QFrame:hover {{
                border: 1px solid {accent};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)

        title_label = QLabel(title.upper())

        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            """
        )

        value_label = QLabel(value)

        value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {accent};
                font-size: 29px;
                font-weight: 800;
            }}
            """
        )

        desc_label = QLabel(description)

        desc_label.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 9px;
            }}
            """
        )

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(desc_label)


# ============================================================
# SECTION TITLE
# ============================================================

def section_title(text):

    label = QLabel(text.upper())

    label.setStyleSheet(
        f"""
        QLabel {{
            color: {TEXT};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            padding-bottom: 5px;
        }}
        """
    )

    return label


# ============================================================
# DASHBOARD
# ============================================================

class Dashboard(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 25)
        layout.setSpacing(18)

        # ----------------------------------------------------
        # Model information
        # ----------------------------------------------------

        model_panel = QFrame()

        model_panel.setStyleSheet(
            f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            """
        )

        model_layout = QHBoxLayout(model_panel)

        model_layout.setContentsMargins(
            20,
            15,
            20,
            15
        )

        info = QVBoxLayout()

        model_name = QLabel(
            "Mistral 7B"
        )

        model_name.setStyleSheet(
            f"""
            QLabel {{
                font-size: 20px;
                font-weight: 800;
                color: {TEXT};
            }}
            """
        )

        model_path = QLabel(
            "LOCAL MODEL  /  OFFLINE SANDBOX"
        )

        model_path.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 9px;
                letter-spacing: 1px;
            }}
            """
        )

        info.addWidget(model_name)
        info.addWidget(model_path)

        model_layout.addLayout(info)

        model_layout.addStretch()

        sha = QLabel(
            "SHA-256\nWAITING FOR MODEL"
        )

        sha.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                background: #070D1C;
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 9px;
            }}
            """
        )

        model_layout.addWidget(sha)

        layout.addWidget(model_panel)

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        stats = QGridLayout()

        stats.setSpacing(12)

        stats.addWidget(
            StatCard(
                "Prompts Tested",
                "0",
                "Awaiting fuzzer output",
                CYAN
            ),
            0,
            0
        )

        stats.addWidget(
            StatCard(
                "Activations",
                "—",
                "Activation tracker",
                BLUE
            ),
            0,
            1
        )

        stats.addWidget(
            StatCard(
                "Anomalies",
                "0",
                "Potential findings",
                YELLOW
            ),
            0,
            2
        )

        stats.addWidget(
            StatCard(
                "Risk Score",
                "N/A",
                "No scan completed",
                GREEN
            ),
            0,
            3
        )

        layout.addLayout(stats)

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        progress_panel = QFrame()

        progress_panel.setStyleSheet(
            f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            """
        )

        progress_layout = QVBoxLayout(progress_panel)

        progress_layout.setContentsMargins(
            18,
            15,
            18,
            15
        )

        top = QHBoxLayout()

        top.addWidget(
            QLabel("FORENSIC SCAN PROGRESS")
        )

        top.addStretch()

        progress_status = QLabel(
            "READY"
        )

        progress_status.setStyleSheet(
            f"""
            QLabel {{
                color: {CYAN};
                font-weight: 700;
                font-size: 10px;
            }}
            """
        )

        top.addWidget(progress_status)

        progress_layout.addLayout(top)

        progress = QProgressBar()

        progress.setValue(0)

        progress.setTextVisible(False)

        progress.setFixedHeight(6)

        progress.setStyleSheet(
            f"""
            QProgressBar {{
                background: #050A16;
                border: none;
                border-radius: 3px;
            }}

            QProgressBar::chunk {{
                background: {CYAN};
                border-radius: 3px;
            }}
            """
        )

        progress_layout.addWidget(progress)

        layout.addWidget(progress_panel)

        # ----------------------------------------------------
        # Middle panels
        # ----------------------------------------------------

        middle = QHBoxLayout()
        middle.setSpacing(15)

        # Activation panel

        activation = QFrame()

        activation.setStyleSheet(
            f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            """
        )

        activation_layout = QVBoxLayout(activation)

        activation_layout.setContentsMargins(
            18,
            15,
            18,
            15
        )

        activation_layout.addWidget(
            section_title("Activation Forensics")
        )

        heatmap = QLabel()

        heatmap.setMinimumHeight(180)

        heatmap.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        heatmap.setText(
            "ACTIVATION MAP\n\n"
            "░ ░ ▒ ▒ ░ ░ ░\n"
            "░ ▒ ▓ █ ▓ ▒ ░\n"
            "░ ░ ▒ ▓ ▒ ░ ░\n"
            "░ ░ ░ ▒ ░ ░ ░\n\n"
            "Waiting for activation data..."
        )

        heatmap.setStyleSheet(
            f"""
            QLabel {{
                background: #070D1B;
                border: 1px solid {BORDER};
                border-radius: 7px;
                color: {MUTED};
                font-family: monospace;
                font-size: 12px;
            }}
            """
        )

        activation_layout.addWidget(heatmap)

        middle.addWidget(
            activation,
            2
        )

        # Detection panel

        detection = QFrame()

        detection.setStyleSheet(
            f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            """
        )

        detection_layout = QVBoxLayout(detection)

        detection_layout.setContentsMargins(
            18,
            15,
            18,
            15
        )

        detection_layout.addWidget(
            section_title("Detection Status")
        )

        normal = QLabel(
            "●   NORMAL                         0"
        )

        normal.setStyleSheet(
            f"""
            QLabel {{
                color: {GREEN};
                background: #081B17;
                border-radius: 6px;
                padding: 15px;
                font-size: 11px;
                font-weight: 700;
            }}
            """
        )

        anomaly = QLabel(
            "⚠   ANOMALY                       0"
        )

        anomaly.setStyleSheet(
            f"""
            QLabel {{
                color: {YELLOW};
                background: #211A08;
                border-radius: 6px;
                padding: 15px;
                font-size: 11px;
                font-weight: 700;
            }}
            """
        )

        unknown = QLabel(
            "○   UNCLASSIFIED                  0"
        )

        unknown.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                background: #0A1020;
                border-radius: 6px;
                padding: 15px;
                font-size: 11px;
                font-weight: 700;
            }}
            """
        )

        detection_layout.addWidget(normal)
        detection_layout.addWidget(anomaly)
        detection_layout.addWidget(unknown)

        detection_layout.addStretch()

        middle.addWidget(
            detection,
            1
        )

        layout.addLayout(middle)

        # ----------------------------------------------------
        # Findings table
        # ----------------------------------------------------

        layout.addWidget(
            section_title("Recent Forensic Events")
        )

        table = QTableWidget(0, 5)

        table.setHorizontalHeaderLabels(
            [
                "TIME",
                "CATEGORY",
                "PROMPT",
                "RESULT",
                "STATUS",
            ]
        )

        table.setMinimumHeight(160)

        table.setStyleSheet(
            f"""
            QTableWidget {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 8px;
                gridline-color: {BORDER};
                color: {TEXT};
                font-size: 10px;
            }}

            QHeaderView::section {{
                background: {PANEL_2};
                color: {MUTED};
                border: none;
                padding: 9px;
                font-size: 9px;
                font-weight: 700;
            }}

            QTableWidget::item {{
                padding: 7px;
                border-bottom: 1px solid {BORDER};
            }}
            """
        )

        header = table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        # Placeholder row

        table.insertRow(0)

        values = [
            "--:--",
            "WAITING",
            "No scan executed",
            "—",
            "READY",
        ]

        for column, value in enumerate(values):

            item = QTableWidgetItem(value)

            if column == 4:
                item.setForeground(
                    QColor(CYAN)
                )

            table.setItem(
                0,
                column,
                item
            )

        layout.addWidget(table)

        # ----------------------------------------------------
        # Bottom buttons
        # ----------------------------------------------------

        buttons = QHBoxLayout()

        buttons.addStretch()

        scan_button = QPushButton(
            "▶   START FORENSIC SCAN"
        )

        scan_button.setFixedHeight(42)

        scan_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {CYAN};
                color: #041018;
                border-radius: 7px;
                padding: 0 25px;
                font-size: 10px;
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: #67E8F9;
            }}
            """
        )

        findings_button = QPushButton(
            "VIEW FINDINGS"
        )

        findings_button.setFixedHeight(42)

        findings_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {PANEL};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 7px;
                padding: 0 22px;
                font-size: 10px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                border-color: {CYAN};
            }}
            """
        )

        report_button = QPushButton(
            "GENERATE REPORT"
        )

        report_button.setFixedHeight(42)

        report_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {PANEL};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 7px;
                padding: 0 22px;
                font-size: 10px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                border-color: {CYAN};
            }}
            """
        )

        buttons.addWidget(scan_button)
        buttons.addWidget(findings_button)
        buttons.addWidget(report_button)

        layout.addLayout(buttons)


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "NeuroFence — LLM Security & Forensic Scanner"
        )

        self.setMinimumSize(
            1400,
            850
        )

        root = GridBackground()

        self.setCentralWidget(root)

        layout = QHBoxLayout(root)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(0)

        sidebar = Sidebar()

        header = Header()

        dashboard = Dashboard()

        right = QVBoxLayout()

        right.setSpacing(0)

        right.addWidget(header)

        right.addWidget(
            dashboard,
            1
        )

        layout.addWidget(sidebar)

        layout.addLayout(
            right,
            1
        )


# ============================================================
# APPLICATION
# ============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setStyleSheet(STYLE)

    window = MainWindow()

    window.show()

    sys.exit(
        app.exec()
    )