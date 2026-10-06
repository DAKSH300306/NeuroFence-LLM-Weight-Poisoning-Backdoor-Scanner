"""NeuroFence API.  Run:  uvicorn backend:app --reload --port 8000   (from dashboard/backend)

Every dataset comes from a provider function. Each one tries the real pipeline output first
(fuzzer/ and neurofence_member3_4/) and falls back to data/*.json, so the UI works before
the pipeline has been run."""
import csv, io, json, time
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles

HERE = Path(__file__).parent
ROOT = HERE.parent.parent                      # repo root
DATA = HERE / "data"
PROMPTS = ROOT / "fuzzer" / "generated_prompts.json"
RESULTS = ROOT / "neurofence_member3_4" / "detection" / "preliminary_results.json"

def mock(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

# ---- providers ---------------------------------------------------------------
def get_model():                                # Member 1 hook
    return mock("mock_model.json")

def get_prompts():                              # Member 2: fuzzer output
    try:
        rows = json.loads(PROMPTS.read_text(encoding="utf-8"))
        n = lambda *t: sum(1 for r in rows if r.get("type") in t)
        return {"total_prompts": len(rows), "normal": n("normal"),
                "unusual": n("edge", "long", "unusual"), "trigger_candidates": n("trigger")}
    except Exception:
        return mock("mock_prompts.json")

def get_activations():                          # Member 3 hook
    return mock("mock_activations.json")

def get_detection():                            # Member 4: preliminary_results.json
    det = mock("mock_detection.json")
    try:
        res = json.loads(RESULTS.read_text(encoding="utf-8"))
        rank = res["summary"]["layer_ranking_test_records"][:2]
        det["suspicious_layers"] = sorted(int(r["layer"].split("_")[-1]) for r in rank)
        det["anomalies"] = sum(1 for r in res["records"] if r["suspicious_layers"])
    except Exception:
        pass
    return det

PROVIDERS = {"model": get_model, "prompts": get_prompts,
             "activations": get_activations, "detection": get_detection}

# ---- scan state --------------------------------------------------------------
STEPS = [("Starting sandbox", "Sandbox started"), ("Loading model", "Model loaded, SHA-256 verified"),
         ("Generating prompts", "Prompt batch generated"), ("Tracking activations", "Activation hooks attached"),
         ("Analyzing anomalies", "Suspicious activation spike detected"), ("Writing findings", "Layer 27 marked for review")]
DURATION = 14.0   # seconds a demo scan takes
S = {"state": "idle", "t0": 0.0, "data": None, "logs": [], "step": -1}
HISTORY = [{"id": "NF-001", "model": "Mistral-7B", "date": "28 Sep 2026", "prompts": 1248, "anomalies": 7, "risk": 72, "status": "High"},
           {"id": "NF-002", "model": "Test Model", "date": "27 Sep 2026", "prompts": 980, "anomalies": 1, "risk": 24, "status": "Low"}]

def log(msg): S["logs"].append(f"[{datetime.now():%H:%M:%S}] {msg}")

def tick():
    if S["state"] != "running": return
    p = min(100, int((time.time() - S["t0"]) / DURATION * 100))
    step = min(5, p * 6 // 100)
    while S["step"] < step:
        S["step"] += 1; log(STEPS[S["step"]][1])
    if p >= 100:
        S["state"] = "done"; log("Scan complete")
        d = S["data"]
        HISTORY.insert(0, {"id": f"NF-{len(HISTORY)+1:03d}", "model": d["model"]["name"], "date": f"{datetime.now():%d %b %Y}",
            "prompts": d["prompts"]["total_prompts"], "anomalies": d["detection"]["anomalies"],
            "risk": d["detection"]["risk_score"], "status": d["detection"]["severity"].title()})
    return p

# ---- app ---------------------------------------------------------------------
app = FastAPI(title="NeuroFence API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/model")
def model(): return get_model()

@app.get("/api/prompts")
def prompts(): return get_prompts()

@app.post("/api/scan/start")
def start():
    if S["state"] == "running": raise HTTPException(409, "A scan is already running")
    S.update(state="running", t0=time.time(), step=-1, logs=[],
             data={k: f() for k, f in PROVIDERS.items()} | {"timestamp": f"{datetime.now():%d %b %Y %H:%M:%S}"})
    log("Scan started"); return {"state": "running"}

@app.post("/api/scan/stop")
def stop():
    if S["state"] == "running": S["state"] = "idle"; log("Scan stopped by operator")
    return {"state": S["state"]}

@app.post("/api/scan/reset")
def reset():
    S.update(state="idle", data=None, logs=[], step=-1); return {"state": "idle"}

@app.get("/api/scan/status")
def status():
    p = tick()
    done = S["state"] == "done"
    if p is None: p = 100 if done else 0
    label = STEPS[max(S["step"], 0)][0] if S["state"] == "running" else ("Scan complete" if done else "Ready")
    return {"state": S["state"], "progress": p, "step": label, "logs": S["logs"],
            "result": S["data"] if done else None}

@app.get("/api/history")
def history(): return HISTORY

@app.get("/api/export/{fmt}")
def export(fmt: str):
    if S["state"] != "done": raise HTTPException(409, "Run a scan before exporting")
    if fmt == "json":
        return PlainTextResponse(json.dumps(S["data"], indent=2), media_type="application/json",
                                 headers={"Content-Disposition": "attachment; filename=neurofence_report.json"})
    if fmt == "csv":
        buf = io.StringIO(); w = csv.writer(buf)
        w.writerow(["Prompt", "Layer", "Activation", "Baseline", "Deviation", "Severity"])
        w.writerows(S["data"]["detection"]["table"])
        return PlainTextResponse(buf.getvalue(), media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=neurofence_findings.csv"})
    raise HTTPException(404, "Use json or csv")

DIST = HERE.parent / "frontend" / "dist"        # after `npm run build`, one server serves everything
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
    @app.get("/{path:path}")
    def spa(path: str): return FileResponse(DIST / "index.html")
