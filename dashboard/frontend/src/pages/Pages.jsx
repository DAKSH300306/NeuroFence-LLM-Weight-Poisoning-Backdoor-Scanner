import { useEffect, useState } from "react";
import ModelDNA from "../components/ModelDNA.jsx";
import PromptStats from "../components/PromptStats.jsx";
import ActivationHeatmap from "../components/ActivationHeatmap.jsx";
import LayerTrend from "../components/LayerTrend.jsx";
import ThreatRadar from "../components/ThreatRadar.jsx";
import RiskScore from "../components/RiskScore.jsx";
import BarChart from "../components/BarChart.jsx";
import Findings from "../components/Findings.jsx";

export const ModelPage = ({ ctx }) => (
  <div className="grid pair"><ModelDNA model={ctx.result?.model || ctx.model} /><PromptStats prompts={ctx.result?.prompts || ctx.prompts} /></div>
);
export const ActivationPage = ({ ctx }) => (<>
  <ActivationHeatmap activations={ctx.result?.activations} suspicious={ctx.result?.detection.suspicious_layers} />
  <div className="grid pair"><LayerTrend activations={ctx.result?.activations} /><ThreatRadar breakdown={ctx.result?.detection.breakdown} /></div>
</>);
export const FindingsPage = ({ ctx }) => {
  const d = ctx.result?.detection;
  return (<>
    <Findings detection={d} />
    <div className="grid pair"><RiskScore detection={d} /><BarChart title="Flagged by check (%)" data={d && Object.entries(d.breakdown)} /></div>
  </>);
};
export function History() {
  const [rows, setRows] = useState([]);
  useEffect(() => { fetch("/api/history").then((r) => r.json()).then(setRows).catch(() => {}); }, []);
  return (
    <section className="panel"><h2>Scans this session</h2>
      <div className="scroll-x"><table>
        <thead><tr><th>Case</th><th>Model</th><th>Date</th><th>Prompts</th><th>Anomalies</th><th>Risk</th><th>Status</th></tr></thead>
        <tbody>{rows.map((r) => <tr key={r.id}><td>{r.id}</td><td>{r.model}</td><td>{r.date}</td><td className="num">{r.prompts}</td><td className="num">{r.anomalies}</td><td className="num">{r.risk}</td>
          <td><span className={"pill " + ({ Low: "ok", Medium: "warn" }[r.status] || "crit")}>{r.status}</span></td></tr>)}</tbody>
      </table></div>
    </section>
  );
}
export function Settings({ ctx }) {
  const c = ctx.config, running = ctx.scan.state === "running";
  if (!c) return null;
  return (
    <section className="panel"><h2>Scan configuration</h2>
      <div className="modelpick">
        <label>Model name or folder
          <input key={c.model} defaultValue={c.model} disabled={running} spellCheck="false"
            onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()} onBlur={(e) => e.target.value.trim() !== c.model && ctx.saveConfig({ model: e.target.value })} /></label>
        <label>Prompts per type
          <input type="number" min="1" max="200" key={c.max_per_type} defaultValue={c.max_per_type} disabled={running} style={{ minWidth: 120 }}
            onBlur={(e) => +e.target.value !== c.max_per_type && ctx.saveConfig({ max_per_type: +e.target.value })} /></label>
        <label className="chk"><input type="checkbox" checked={c.local_only} disabled={running} onChange={(e) => ctx.saveConfig({ local_only: e.target.checked })} /> Offline only</label>
      </div>
      <p className="muted" style={{ marginTop: 16 }}>Pipeline mode: {c.mode}. Changes apply to the next scan. A Hugging Face name downloads the model on first use; a local folder with Offline only never touches the network.</p>
    </section>
  );
}
