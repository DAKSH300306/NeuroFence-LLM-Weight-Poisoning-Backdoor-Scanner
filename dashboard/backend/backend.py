"""NeuroFence API.  Run:  uvicorn backend:app --reload --port 8000   (from dashboard/backend)

Start scan runs the real pipeline, in order:
  fuzzer/fuzzer.py -> neurofence_member3_4/activation/run_activation_scan.py
  -> detection/baseline.py -> detection/preliminary_detector.py
and turns the files they write into what the dashboard shows.
If those folders are missing (or NEUROFENCE_DEMO=1) it plays back the demo data in data/*.json.

Environment: NEUROFENCE_MODEL (default distilgpt2), NEUROFENCE_LOCAL_ONLY=1, NEUROFENCE_MAX_PER_TYPE (default 20).
The Python running uvicorn needs: pip install -r ../../neurofence_member3_4/requirements_member3_4.txt"""
import csv, hashlib, io, json, os, re, subprocess, sys, threading, time
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

HERE = Path(__file__).parent
ROOT = HERE.parent.parent                                   # repo root
DATA = HERE / "data"
FUZZ_DIR, FUZZ = ROOT / "fuzzer", ROOT / "fuzzer" / "generated_prompts.json"
PIPE = ROOT / "neurofence_member3_4"
ACT_PY, BASE_PY, DET_PY = (PIPE / "activation" / "run_activation_scan.py",
                           PIPE / "detection" / "baseline.py", PIPE / "detection" / "preliminary_detector.py")
ACT_DATA, RESULTS = PIPE / "activation" / "activation_data.json", PIPE / "detection" / "preliminary_results.json"

CONFIG = {"model": os.getenv("NEUROFENCE_MODEL", "distilgpt2"),
          "local_only": os.getenv("NEUROFENCE_LOCAL_ONLY") == "1"}
MAX_PER_TYPE = os.getenv("NEUROFENCE_MAX_PER_TYPE", "20")

def live_mode():
    ok = all(p.exists() for p in (FUZZ_DIR / "fuzzer.py", ACT_PY, BASE_PY, DET_PY))
    return ok and os.getenv("NEUROFENCE_DEMO") != "1"

def mock(name): return json.loads((DATA / name).read_text(encoding="utf-8"))

# ---- model (Member 1) --------------------------------------------------------
def resolve_model(m):
    bases = [ROOT]
    try: bases.insert(0, Path.cwd())          # cwd can vanish if the folder was replaced while the server ran
    except OSError: pass
    for base in bases:
        p = base / m
        if p.exists(): return str(p.resolve())
    return m

def model_files(p):
    p = Path(p)
    if p.is_file(): return [p]
    return sorted(f for f in p.rglob("*") if f.suffix in (".safetensors", ".bin", ".gguf"))

def sha256_of(files, stop=None):
    h = hashlib.sha256()
    for f in files:
        with open(f, "rb") as fh:
            while chunk := fh.read(1 << 22):
                if stop and stop.is_set(): return None
                h.update(chunk)
    return h.hexdigest()

def get_model(hash_it=False, stop=None):
    info = mock("mock_model.json"); target = resolve_model(CONFIG["model"])
    info.update(name=os.path.basename(CONFIG["model"].rstrip("/")) or CONFIG["model"], parameters="-",
                execution="Offline" if CONFIG["local_only"] else "Online (may download)")
    files = model_files(target) if Path(target).exists() else []
    if files:
        info.update(format=files[0].suffix, size=f"{sum(f.stat().st_size for f in files)/1e9:.2f} GB", source="Local model")
        d = sha256_of(files, stop) if hash_it else None
        info.update(hash=d or "pending (computed at scan)", status="Verified" if d else "Unverified")
    else:
        info.update(format="Hub model", size="-", source="Hugging Face hub", hash="not hashed (not a local file)", status="Unverified")
    return info

# ---- prompts (Member 2) ------------------------------------------------------
def get_prompts():
    try:
        rows = json.loads(FUZZ.read_text(encoding="utf-8"))
        n = lambda *t: sum(1 for r in rows if r.get("type") in t)
        return {"total_prompts": len(rows), "normal": n("normal"),
                "unusual": n("edge", "long", "unusual"), "trigger_candidates": n("trigger")}
    except Exception:
        return mock("mock_prompts.json")

# ---- activations + detection (Members 3 & 4): files -> dashboard shape --------
LABEL = {"normal": "Normal prompt", "edge": "Edge case", "long": "Long prompt", "trigger": "Trigger candidate"}
SHORT = {"normal": "Normal prompts", "edge": "Edge prompts", "long": "Long prompts", "trigger": "Trigger prompts"}
lnum = lambda k: int(re.findall(r"\d+", k)[-1])

def build_real_result():
    res = json.loads(RESULTS.read_text(encoding="utf-8")); acts = json.loads(ACT_DATA.read_text(encoding="utf-8"))
    recs, cfg = res["records"], res["config"]
    types = sorted({r["type"] for r in recs}, key=lambda t: (t != "normal", t))
    layer_keys = sorted(recs[0]["layers"], key=lnum)
    # heatmap: mean share of anomalous positions per layer and prompt type, scaled to the strongest cell
    raw = [[(lambda xs: sum(xs) / len(xs) if xs else 0)([r["layers"][k]["anomaly_ratio"] for r in recs
            if r["type"] == t and k in r["layers"]]) for t in types] for k in layer_keys]
    top = max(max(row) for row in raw) or 1
    activations = {"prompt_types": [LABEL.get(t, t.title()) for t in types], "layers": [lnum(k) for k in layer_keys],
                   "activation_matrix": [[round(v / top, 3) for v in row] for row in raw],
                   "total_events": sum(len(v) for r in acts for v in r["activations"].values())}
    test = [r for r in recs if r["role"] == "test"]; ctrl = [r for r in recs if r["role"] != "test"]
    flagged = lambda rs: [r for r in rs if r["suspicious_layers"]]
    frac = lambda rs: len(flagged(rs)) / len(rs) if rs else 0.0
    risk = max(0, min(100, round(100 * (frac(test) - frac(ctrl)))))   # share of test prompts flagged, minus normal
    sev = "LOW" if risk < 25 else "MEDIUM" if risk < 50 else "HIGH" if risk < 75 else "CRITICAL"
    max_z = max((r["max_z"] for r in test), default=0)
    breakdown = {SHORT.get(t, t.title()): round(100 * frac([r for r in test if r["type"] == t])) for t in types if t != "normal"}
    breakdown["Peak deviation"] = min(100, round(max_z / 20 * 100))      # Z of 20 or more fills the axis
    lr_all = [d for d in res["summary"]["layer_ranking_test_records"] if d["test_records_flagged"] > 0]
    ranked = [d for d in lr_all if lr_all and d["mean_anomaly_ratio"] >= 0.25 * lr_all[0]["mean_anomaly_ratio"]][:3]  # drop noise layers
    # findings table: the two strongest prompts of each non-normal type
    rows = []
    for t in types:
        if t == "normal": continue
        rows += sorted((r for r in test if r["type"] == t), key=lambda r: -r["preliminary_score"])[:2]
    table = []
    for r in sorted(rows, key=lambda r: -r["preliminary_score"])[:6]:
        lk = max(r["layers"], key=lambda k: r["layers"][k]["max_z"]); lr = r["layers"][lk]
        tp = (lr["top_suspicious_positions"] or [{"value": 0.0, "baseline_mean": 0.0, "z_score": lr["max_z"]}])[0]
        sevtxt = "Critical" if lr["max_z"] >= cfg["strong_z"] else "Warning" if r["suspicious_layers"] else "Normal"
        p = r["prompt"].replace("\n", " ").strip() or "(empty prompt)"
        table.append([f"{p[:30]}{'…' if len(p) > 30 else ''}", f"L{lnum(lk)}", tp["value"], tp["baseline_mean"], f"{tp['z_score']:.1f}σ", sevtxt])
    trig = [r for r in test if r["type"] == "trigger"]
    words = Counter(w for r in trig for w in re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", r["prompt"]))
    conf = round(100 * frac(trig))
    tl = max(layer_keys, key=lambda k: sum(r["layers"][k]["anomaly_ratio"] for r in trig if k in r["layers"])) if trig else None
    trigger = {"name": words.most_common(1)[0][0] if words else "none found", "layer": lnum(tl) if tl else 0, "confidence": conf,
               "status": "SUSPICIOUS BEHAVIOR" if conf >= 50 else "WEAK SIGNAL" if conf else "NO SIGNAL",
               "deviation": f"{max((r['max_z'] for r in trig), default=0):.1f}σ",
               "investigation": "REQUIRES REVIEW" if conf >= 50 else "LOW PRIORITY"}
    detection = {"anomalies": len(flagged(test)), "risk_score": risk, "severity": sev,
                 "suspicious_layers": sorted(lnum(d["layer"]) for d in ranked), "breakdown": breakdown,
                 "table": table, "trigger": trigger, "disclaimer": res.get("disclaimer", "")}
    return activations, detection

# ---- scan state --------------------------------------------------------------
STEPS = ["Starting sandbox", "Loading model", "Generating prompts", "Tracking activations", "Analyzing anomalies", "Writing findings"]
BOUNDS = [0, 4, 10, 15, 80, 95, 100]               # progress range covered by each step
S = {"state": "idle", "progress": 0, "step": -1, "logs": [], "error": "", "data": None, "proc": None, "stop": threading.Event()}
HISTORY = [{"id": "NF-001", "model": "Mistral-7B", "date": "28 Sep 2026", "prompts": 1248, "anomalies": 7, "risk": 72, "status": "High"},
           {"id": "NF-002", "model": "Test Model", "date": "27 Sep 2026", "prompts": 980, "anomalies": 1, "risk": 24, "status": "Low"}]

class Stopped(Exception): pass
def log(m): S["logs"].append(f"[{datetime.now():%H:%M:%S}] {m}")
def begin(i, msg):
    if S["stop"].is_set(): raise Stopped()
    S["step"], S["progress"] = i, BOUNDS[i]; log(msg)

def run(args, cwd, on_line=None):
    tail = deque(maxlen=6)
    p = subprocess.Popen([sys.executable, "-u", *map(str, args)], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, env={**os.environ, "PYTHONUNBUFFERED": "1"})
    S["proc"] = p
    for line in p.stdout:
        line = line.rstrip()
        if line: tail.append(line); on_line and on_line(line)
    p.wait(); S["proc"] = None
    if S["stop"].is_set(): raise Stopped()
    if p.returncode:
        hint = " Install torch and transformers in the Python that runs uvicorn." if any("ModuleNotFoundError" in t for t in tail) else ""
        raise RuntimeError(f"{Path(args[0]).name} exited with code {p.returncode}.{hint} Last output: {' | '.join(tail)}")

def live_pipeline():
    begin(0, f"Sandbox ready. Python: {sys.executable}")
    begin(1, f"Loading model {CONFIG['model']}")
    info = get_model(hash_it=True, stop=S["stop"]); log(f"Integrity: {info['status']}")
    begin(2, "Running prompt fuzzer"); run([FUZZ_DIR / "fuzzer.py"], FUZZ_DIR)
    log(f"Generated {get_prompts()['total_prompts']} prompts")
    begin(3, "Recording layer activations (the first run may download the model)")
    def on_act(line):
        m = re.match(r"\s+\[(\d+)/(\d+)\]", line)
        if m: S["progress"] = BOUNDS[3] + (BOUNDS[4] - BOUNDS[3]) * int(m[1]) // int(m[2])
        elif re.match(r"\[\d/4\]", line): log(line)
    run([ACT_PY, "--prompts", FUZZ, "--model", resolve_model(CONFIG["model"]), "--max-per-type", MAX_PER_TYPE]
        + (["--local-only"] if CONFIG["local_only"] else []), PIPE, on_act)
    begin(4, "Building the normal-prompt baseline"); run([BASE_PY], PIPE)
    log("Scoring every prompt against the baseline"); run([DET_PY], PIPE)
    begin(5, "Writing findings")
    activations, detection = build_real_result()
    return {"model": info, "prompts": get_prompts(), "activations": activations, "detection": detection}

def demo_pipeline():
    msgs = ["Sandbox started", "Model loaded", "Prompt batch generated", "Activation hooks attached", "Suspicious activation spike detected", "Layer 27 marked for review"]
    for i, m in enumerate(msgs):
        begin(i, m)
        for k in range(1, 6):
            time.sleep(0.45)
            if S["stop"].is_set(): raise Stopped()
            S["progress"] = BOUNDS[i] + (BOUNDS[i + 1] - BOUNDS[i]) * k // 5
    return {"model": mock("mock_model.json"), "prompts": mock("mock_prompts.json"),
            "activations": mock("mock_activations.json"), "detection": mock("mock_detection.json")}

def worker(evt, demo):
    try:
        data = (demo_pipeline if demo else live_pipeline)()
        if evt.is_set(): return
        data["timestamp"] = f"{datetime.now():%d %b %Y %H:%M:%S}"; data["mode"] = "demo" if demo else "live"
        S.update(data=data, progress=100, state="done"); log("Scan complete")
        d = data["detection"]
        HISTORY.insert(0, {"id": f"NF-{len(HISTORY)+1:03d}", "model": data["model"]["name"], "date": f"{datetime.now():%d %b %Y}",
                           "prompts": data["prompts"]["total_prompts"], "anomalies": d["anomalies"], "risk": d["risk_score"], "status": d["severity"].title()})
    except Stopped:
        pass
    except Exception as e:
        if not evt.is_set(): S.update(state="error", error=str(e)); log("Scan failed")

def load_last_scan():
    """Show the results of the previous scan on startup instead of an empty dashboard."""
    if not (live_mode() and RESULTS.exists() and ACT_DATA.exists()): return
    try:
        a, d = build_real_result(); info = get_model()
        try:
            meta = json.loads((PIPE / "activation" / "activation_meta.json").read_text(encoding="utf-8"))["model"]
            info["name"] = os.path.basename(meta.rstrip("/"))
            if not os.getenv("NEUROFENCE_MODEL"): CONFIG["model"] = meta
        except Exception: pass
        ts = datetime.fromtimestamp(RESULTS.stat().st_mtime)
        S.update(state="done", progress=100, data={"model": info, "prompts": get_prompts(), "activations": a, "detection": d,
                 "timestamp": f"{ts:%d %b %Y %H:%M:%S}", "mode": "live"}); log("Loaded results from the last scan")
    except Exception:
        pass

load_last_scan()

# ---- app ---------------------------------------------------------------------
app = FastAPI(title="NeuroFence API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Cfg(BaseModel):
    model: str | None = None
    local_only: bool | None = None

@app.get("/api/config")
def get_config(): return {**CONFIG, "mode": "live" if live_mode() else "demo"}

@app.post("/api/config")
def set_config(c: Cfg):
    if S["state"] == "running": raise HTTPException(409, "Stop the scan before changing the model")
    if c.model is not None and c.model.strip(): CONFIG["model"] = c.model.strip()
    if c.local_only is not None: CONFIG["local_only"] = c.local_only
    return get_config()

@app.get("/api/model")
def model(): return get_model()

@app.get("/api/prompts")
def prompts(): return get_prompts()

@app.post("/api/scan/start")
def start():
    if S["state"] == "running": raise HTTPException(409, "A scan is already running")
    evt = threading.Event()
    S.update(state="running", progress=0, step=-1, logs=[], error="", data=None, stop=evt)
    threading.Thread(target=worker, args=(evt, not live_mode()), daemon=True).start()
    return {"state": "running"}

@app.post("/api/scan/stop")
def stop():
    if S["state"] == "running":
        S["stop"].set(); p = S["proc"]
        if p and p.poll() is None: p.terminate()
        S["state"] = "idle"; log("Scan stopped by operator")
    return {"state": S["state"]}

@app.post("/api/scan/reset")
def reset():
    if S["state"] == "running": stop()
    S.update(state="idle", progress=0, step=-1, logs=[], error="", data=None); return {"state": "idle"}

@app.get("/api/scan/status")
def status():
    st = S["state"]
    label = {"done": "Scan complete", "error": "Scan failed", "idle": "Ready"}.get(st) or STEPS[max(S["step"], 0)]
    return {"state": st, "progress": S["progress"], "step": label, "logs": S["logs"], "error": S["error"],
            "result": S["data"] if st == "done" else None}

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
        w.writerow(["Prompt", "Layer", "Activation", "Baseline", "Deviation", "Severity"]); w.writerows(S["data"]["detection"]["table"])
        return PlainTextResponse(buf.getvalue(), media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=neurofence_findings.csv"})
    raise HTTPException(404, "Use json or csv")

DIST = HERE.parent / "frontend" / "dist"        # after `npm run build`, one server serves everything
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
    @app.get("/{path:path}")
    def spa(path: str): return FileResponse(DIST / "index.html")
