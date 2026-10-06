import { useCallback, useEffect, useRef, useState } from "react";
import Header from "../components/Header.jsx";
import ScanProgress from "../components/ScanProgress.jsx";
import ActivationHeatmap from "../components/ActivationHeatmap.jsx";
import RiskScore from "../components/RiskScore.jsx";
import ThreatRadar from "../components/ThreatRadar.jsx";
import Findings from "../components/Findings.jsx";
import ModelDNA from "../components/ModelDNA.jsx";
import PromptStats from "../components/PromptStats.jsx";

const get = (u) => fetch(u).then((r) => { if (!r.ok) throw new Error(u); return r.json(); });
const post = (u) => fetch(u, { method: "POST" }).then((r) => r.json());
const IDLE = { state: "idle", progress: 0, step: "Ready", logs: [], result: null };

export default function Dashboard() {
  const [model, setModel] = useState(null);
  const [prompts, setPrompts] = useState(null);
  const [scan, setScan] = useState(IDLE);
  const [error, setError] = useState("");
  const timer = useRef(null);

  const poll = useCallback(async () => {
    try { setScan(await get("/api/scan/status")); setError(""); }
    catch { setError("Can't reach the NeuroFence API. Start it with: uvicorn backend:app --port 8000"); }
  }, []);

  useEffect(() => {
    Promise.all([get("/api/model"), get("/api/prompts"), get("/api/scan/status")])
      .then(([m, p, s]) => { setModel(m); setPrompts(p); setScan(s); })
      .catch(() => setError("Can't reach the NeuroFence API. Start it with: uvicorn backend:app --port 8000"));
  }, []);

  useEffect(() => {  // poll only while a scan runs
    if (scan.state !== "running") return;
    timer.current = setInterval(poll, 500);
    return () => clearInterval(timer.current);
  }, [scan.state, poll]);

  const act = (path) => async () => { await post(path); poll(); };
  const r = scan.result;

  return (
    <main className="main">
      <Header model={model} state={scan.state} onStart={act("/api/scan/start")} onStop={act("/api/scan/stop")} onReset={act("/api/scan/reset")} />
      {error && <div className="alert" role="alert">{error}</div>}
      <ScanProgress {...scan} />
      <div className="grid top">
        <ActivationHeatmap activations={r?.activations} suspicious={r?.detection.suspicious_layers} />
        <div className="stackcol">
          <RiskScore detection={r?.detection} />
          <ThreatRadar breakdown={r?.detection.breakdown} />
        </div>
      </div>
      <div className="grid bottom">
        <Findings detection={r?.detection} />
        <div className="stackcol">
          <ModelDNA model={r?.model || model} />
          <PromptStats prompts={r?.prompts || prompts} />
        </div>
      </div>
    </main>
  );
}
