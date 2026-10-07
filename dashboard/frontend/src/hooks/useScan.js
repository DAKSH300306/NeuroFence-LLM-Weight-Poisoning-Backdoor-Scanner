import { useCallback, useEffect, useState } from "react";
const DOWN = "Can't reach the NeuroFence API. Start it with: python3 -m uvicorn backend:app --port 8000";
const get = (u) => fetch(u).then((r) => { if (!r.ok) throw new Error(u); return r.json(); });
const IDLE = { state: "idle", progress: 0, step: "Ready", logs: [], error: "", result: null };

export default function useScan() {
  const [model, setModel] = useState(null), [prompts, setPrompts] = useState(null), [config, setConfig] = useState(null);
  const [scan, setScan] = useState(IDLE), [error, setError] = useState("");
  const poll = useCallback(async () => { try { setScan(await get("/api/scan/status")); setError(""); } catch { setError(DOWN); } }, []);
  useEffect(() => {
    Promise.all([get("/api/model"), get("/api/prompts"), get("/api/scan/status"), get("/api/config")])
      .then(([m, p, s, c]) => { setModel(m); setPrompts(p); setScan(s); setConfig(c); }).catch(() => setError(DOWN));
  }, []);
  useEffect(() => {
    if (scan.state !== "running") return;
    const t = setInterval(poll, 500);
    return () => clearInterval(t);
  }, [scan.state, poll]);
  const act = (path) => async () => { await fetch(path, { method: "POST" }); poll(); };
  const saveConfig = async (patch) => {
    const r = await fetch("/api/config", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch) });
    if (r.ok) { setConfig(await r.json()); setModel(await get("/api/model")); }
  };
  return { model, prompts, config, scan, error: error || scan.error, result: scan.result,
           start: act("/api/scan/start"), stop: act("/api/scan/stop"), reset: act("/api/scan/reset"), saveConfig };
}
