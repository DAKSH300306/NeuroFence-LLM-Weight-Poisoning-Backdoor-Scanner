import base64, csv, json
from PyQt6.QtCore import QBuffer, QIODevice, QMarginsF
from PyQt6.QtGui import QPageLayout, QPageSize, QTextDocument
from PyQt6.QtPrintSupport import QPrinter

def _b64(img):
    buf = QBuffer(); buf.open(QIODevice.OpenModeFlag.WriteOnly); img.save(buf, "PNG")
    return base64.b64encode(bytes(buf.data())).decode()

def build_html(d, heatmap_img=None):
    m, p, a, x = d["model"], d["prompts"], d["activations"], d["detection"]; t = x["trigger"]
    rows = "".join(f"<tr>{''.join(f'<td>{c}</td>' for c in r)}</tr>" for r in x["table"])
    img = f'<img src="data:image/png;base64,{_b64(heatmap_img)}" width="600"/>' if heatmap_img else ""
    return f"""<body style="font-family:Segoe UI,Arial"><h1 style="color:#0e7490">NeuroFence — LLM Security Report</h1>
<p>Final-year project: LLM Weight Poisoning &amp; Backdoor Scanner. Scan time: {d['timestamp']}</p>
<h2>1. Model metadata</h2><p>{m['name']} | {m['format']} | {m['parameters']} params | {m['size']} | {m['source']} | {m['execution']}<br/>SHA-256: {m['hash']} | Integrity: {m['status']}</p>
<h2>2. Prompt testing</h2><p>Total {p['total_prompts']} (normal {p['normal']}, unusual {p['unusual']}, trigger candidates {p['trigger_candidates']})</p>
<h2>3. Activation statistics</h2><p>{a['total_events']} activation events across {len(a['layers'])} layers. Suspicious layers: {x['suspicious_layers']}</p>
<h2>4. Detected anomalies ({x['anomalies']})</h2><table border="1" cellpadding="4" cellspacing="0"><tr><th>Prompt</th><th>Layer</th><th>Activation</th><th>Baseline</th><th>Deviation</th><th>Severity</th></tr>{rows}</table>
<h2>5. Suspicious trigger</h2><p><b>{t['name']}</b> — {t['status']}, confidence {t['confidence']}%, layer {t['layer']}, deviation {t['deviation']}. Status: {t['investigation']}</p>
<h2>6. Risk score</h2><p style="font-size:20pt;color:#dc2626">{x['risk_score']} / 100 — {x['severity']}</p>
<h2>7. Activation heatmap</h2>{img}
<h2>8. Recommended actions</h2><ul><li>Do not deploy this model until the trigger is reviewed.</li><li>Re-run trigger candidate prompts in the sandbox with layer {t['layer']} ablation.</li><li>Compare weights against a trusted upstream checkpoint.</li></ul>
<h2>9. Final summary</h2><p>NeuroFence flagged possible trigger-based backdoor behavior. Overall risk is <b>{x['severity']}</b>; manual review is required.</p></body>"""

def generate_pdf(path, d, heatmap_img=None):
    doc = QTextDocument(); doc.setHtml(build_html(d, heatmap_img))
    pr = QPrinter(QPrinter.PrinterMode.HighResolution); pr.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    pr.setOutputFileName(path); pr.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Portrait, QMarginsF(15, 15, 15, 15)))
    doc.print(pr)

def export_json(path, d):
    with open(path, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

def export_csv(path, d):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["Prompt", "Layer", "Activation", "Baseline", "Deviation", "Severity"]); w.writerows(d["detection"]["table"])
