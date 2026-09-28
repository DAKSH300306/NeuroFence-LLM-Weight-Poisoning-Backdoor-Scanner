import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QProgressBar, QStackedWidget,
                             QScrollArea, QFileDialog, QDialog, QTextBrowser, QCheckBox)
from PyQt6.QtCore import pyqtSignal
from services import model_service, report_service
from .cards import Card, MetricCard, PipelineWidget, LogPanel, ModelForensicsCard, PromptCard, C, risk_level
from .heatmap import HeatmapWidget
from .threat_panel import ThreatPanel, DetectionTable, TriggerCard
from .report_view import ReportView, HistoryTable

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
EMPTY = {"prompts": {"total_prompts": 0, "normal": 0, "unusual": 0, "trigger_candidates": 0}, "activations": {"layers": [], "activation_matrix": [], "total_events": 0},
         "detection": {"anomalies": 0, "risk_score": 0, "severity": "-", "suspicious_layers": [], "breakdown": {}, "table": [], "trigger": {}}}

class Hero(Card):
    select, start, stop, reset = pyqtSignal(), pyqtSignal(), pyqtSignal(), pyqtSignal()
    def __init__(self):
        super().__init__("Model security scan"); self.name = QLabel("—"); self.name.setObjectName("h1")
        self.meta = QLabel("LOCAL • OFFLINE • SANDBOXED"); self.meta.setStyleSheet(f"color:{C['purple']};font-weight:600;letter-spacing:1px")
        self.hash = QLabel(""); self.hash.setObjectName("dim"); self.step = QLabel("Ready"); self.step.setStyleSheet(f"color:{C['cyan']};font-weight:600")
        self.bar = QProgressBar(); self.bar.setFixedHeight(18); row = QHBoxLayout()
        self.b = {}
        for k, txt, sig in (("select", "SELECT MODEL", self.select), ("start", "START SECURITY SCAN", self.start), ("stop", "STOP SCAN", self.stop), ("reset", "RESET", self.reset)):
            b = QPushButton(txt); b.clicked.connect(sig.emit); row.addWidget(b); self.b[k] = b
        self.b["start"].setObjectName("primary"); self.b["stop"].setObjectName("danger")
        for w in (self.name, self.meta, self.hash): self.body.addWidget(w)
        self.body.addLayout(row); self.body.addWidget(self.step); self.body.addWidget(self.bar)
    def apply(self, s):
        m = s["model"]; self.name.setText(m["name"]); self.hash.setText(f"SHA-256: {m['hash']}")
        self.bar.setValue(s["progress"]); self.b["start"].setEnabled(not s["running"]); self.b["select"].setEnabled(not s["running"]); self.b["stop"].setEnabled(s["running"])

def scroll(widgets):
    w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(24, 20, 24, 24); l.setSpacing(16)
    for x in widgets: l.addWidget(x) if not isinstance(x, tuple) else l.addLayout(x[0])
    l.addStretch(); s = QScrollArea(); s.setWidgetResizable(True); s.setWidget(w); return s

def row(*ws, stretch=None):
    h = QHBoxLayout(); h.setSpacing(16)
    for i, w in enumerate(ws): h.addWidget(w, stretch[i] if stretch else 1)
    return (h,)

class Dashboard(QWidget):
    status_changed = pyqtSignal(str, str, str)
    model_changed = pyqtSignal(str)
    goto = pyqtSignal(int)

    def __init__(self, scan):
        super().__init__(); self.scan = scan; self.data = None; self.running = False; self.progress = 0
        self.trigger_added = False; self.report_ready = False; self.views = []
        self.model = model_service.get_model_info(); self.scan.model = None
        self.stack = QStackedWidget(); QVBoxLayout(self).addWidget(self.stack); self.layout().setContentsMargins(0, 0, 0, 0)
        R = lambda w: (self.views.append(w), w)[1]
        hero = R(Hero()); self.hero = hero
        self.metrics = [MetricCard("◉", "MODEL STATUS", "Weight integrity check"), MetricCard("✎", "PROMPTS TESTED", "Fuzzer corpus executed"),
                        MetricCard("⚡", "ACTIVATION EVENTS", "Hook captures"), MetricCard("⚠", "ANOMALIES DETECTED", "Deviations above baseline"),
                        MetricCard("◈", "RISK SCORE", "Composite backdoor risk")]
        mrow = QHBoxLayout(); mrow.setSpacing(14)
        for m in self.metrics: mrow.addWidget(m)
        self.log = LogPanel(); self.report = R(ReportView()); self.history = HistoryTable(self.scan.history)
        hm = lambda: R(HeatmapWidget())
        self.hm_export = hm(); hc = Card("Activation forensics"); hc.body.addWidget(self.hm_export)
        self.trigger = R(TriggerCard()); self.trigger.view_activation.connect(lambda: self.goto.emit(3)); self.trigger.add_report.connect(self.add_trigger)
        ov = scroll([hero, (mrow,), row(R(ThreatPanel()), R(ModelForensicsCard()), stretch=[3, 2]), hc, row(R(DetectionTable()), self.trigger, stretch=[3, 2]), R(PipelineWidget()), self.log])
        c2 = Card("Activation forensics"); c2.body.addWidget(hm())
        pages = [ov, scroll([R(ModelForensicsCard()), R(PipelineWidget()), R(PromptCard())]), scroll([R(PromptCard()), self.log_clone()]),
                 scroll([c2]), scroll([R(ThreatPanel()), R(DetectionTable()), R(TriggerCard())]), scroll([self.history]), scroll([self.report]), scroll([self.settings()])]
        for p in pages: self.stack.addWidget(p)
        for v in self.views:
            if isinstance(v, TriggerCard) and v is not self.trigger: v.view_activation.connect(lambda: self.goto.emit(3)); v.add_report.connect(self.add_trigger)
        hero.select.connect(self.pick_model); hero.start.connect(self.start_scan); hero.stop.connect(self.scan.stop); hero.reset.connect(self.reset_scan)
        self.report.action.connect(self.report_action)
        self.scan.progress.connect(self.on_progress); self.scan.log.connect(self.log.append); self.scan.finished.connect(self.on_done); self.scan.stopped.connect(self.on_stopped)
        self.refresh()

    def log_clone(self):  # secondary log for the fuzzer page, mirrors the main one
        l = LogPanel(); self.scan.log.connect(l.append); return l

    def settings(self):
        c = Card("Settings")
        for t in ("Enforce offline sandbox (block network)", "Attach activation hooks on all layers", "Auto-generate PDF after scan"):
            cb = QCheckBox(t); cb.setChecked(True); c.body.addWidget(cb)
        return c

    def go(self, i): self.stack.setCurrentIndex(i)

    def state(self):
        d = self.data or {}; det = d.get("detection", EMPTY["detection"]); p = self.progress; started = self.data is not None
        pr = d.get("prompts", EMPTY["prompts"]); ac = d.get("activations", EMPTY["activations"])
        frac = lambda a, lo=0: int(a * max(0, min(1, (p - lo) / (100 - lo))))
        return {"model": self.model, "progress": p, "running": self.running, "started": started, "prompts": pr, "activations": ac, "detection": det,
                "prompts_tested": frac(pr["total_prompts"]), "events": frac(ac.get("total_events", 0)),
                "anomalies": det["anomalies"] if p >= 80 else 0, "risk": frac(det["risk_score"], 60), "trigger_added": self.trigger_added, "report_ready": self.report_ready}

    def refresh(self):
        s = self.state()
        for v in self.views: v.apply(s)
        m = self.metrics; ok = self.model["status"] == "Verified"
        m[0].set("✓ Verified" if ok else "Unverified", "HASH MATCH" if ok else "PENDING", C["green"] if ok else C["orange"])
        m[1].set(f"{s['prompts_tested']:,}", "RUNNING" if self.running else "COMPLETE" if s["started"] and self.progress >= 100 else "IDLE", C["cyan"])
        m[2].set(f"{s['events']:,}", "CAPTURING" if self.running else "IDLE", C["blue"])
        m[3].set(str(s["anomalies"]), "ATTENTION" if s["anomalies"] else "NONE", C["orange"] if s["anomalies"] else C["green"])
        lv, col = risk_level(s["risk"]) if s["risk"] else ("PENDING", C["dim"])
        m[4].set(f"{s['risk']} / 100" if s["risk"] else "—", lv, col)

    def on_progress(self, p, msg):
        self.progress = p; self.hero.step.setText(msg); self.hero.bar.setFormat(f"{'█' * (p // 6)}{'░' * (17 - p // 6)}  {p}%")
        self.status_changed.emit("SCANNING", C["cyan"], f"{p}%"); self.refresh()

    def start_scan(self):
        self.log.view.clear(); self.report_ready = self.trigger_added = False; self.running = True; self.progress = 0
        self.data = self.scan.start(); self.log.append(self.scan.ts() + "Scan started"); self.refresh()

    def on_done(self, data):
        self.running = False; self.hero.step.setText("Scan complete — review findings"); self.history.refresh()
        self.status_changed.emit("THREAT DETECTED", C["orange"], "COMPLETE"); self.refresh()

    def on_stopped(self):
        self.running = False; self.hero.step.setText("Scan stopped"); self.status_changed.emit("SCAN STOPPED", C["orange"], "STOPPED"); self.refresh()

    def reset_scan(self):
        self.scan.stop(); self.data, self.progress, self.running = None, 0, False; self.trigger_added = self.report_ready = False
        self.log.view.clear(); self.hero.step.setText("Ready"); self.hero.bar.setFormat("%p%"); self.status_changed.emit("SYSTEM READY", C["green"], "IDLE"); self.refresh()

    def pick_model(self):
        path = QFileDialog.getExistingDirectory(self, "Select model directory") or QFileDialog.getOpenFileName(self, "Select model file", "", "Models (*.safetensors *.gguf *.bin *.pt)")[0]
        if path:
            self.model = self.scan.model = model_service.from_path(path); self.model_changed.emit(self.model["name"]); self.refresh()

    def add_trigger(self):
        self.trigger_added = True; self.refresh()

    def snapshot(self):
        return dict(self.data, trigger_in_report=self.trigger_added) if self.data and self.progress >= 100 else None

    def report_action(self, kind):
        snap = self.snapshot()
        if not snap: self.report.msg.setText("Run a complete scan first."); return
        os.makedirs(REPORT_DIR, exist_ok=True); base = os.path.join(REPORT_DIR, f"neurofence_{snap['model']['name']}")
        if kind == "preview":
            dlg = QDialog(self); dlg.resize(760, 640); b = QTextBrowser(dlg); b.setHtml(report_service.build_html(snap, self.hm_export.to_image(900, 560)))
            QVBoxLayout(dlg).addWidget(b); dlg.setStyleSheet("background:white;color:black"); dlg.exec(); return
        if kind == "pdf": report_service.generate_pdf(base + ".pdf", snap, self.hm_export.to_image(900, 560)); self.report_ready = True
        elif kind == "json": report_service.export_json(base + ".json", snap)
        else: report_service.export_csv(base + ".csv", snap)
        self.report.msg.setText(f"✓ Saved to {base}.{kind}"); self.refresh()
