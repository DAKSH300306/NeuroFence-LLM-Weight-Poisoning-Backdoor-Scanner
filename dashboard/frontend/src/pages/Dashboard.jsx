import StatCards from "../components/StatCards.jsx";
import ActivationHeatmap from "../components/ActivationHeatmap.jsx";
import RiskScore from "../components/RiskScore.jsx";
import ThreatRadar from "../components/ThreatRadar.jsx";
import LayerTrend from "../components/LayerTrend.jsx";
import BarChart from "../components/BarChart.jsx";
import Donut from "../components/Donut.jsx";
import Findings from "../components/Findings.jsx";
import PromptStats from "../components/PromptStats.jsx";

export default function Dashboard({ ctx }) {
  const r = ctx.result, d = r?.detection, a = r?.activations;
  const tested = d ? d.tested ?? r.prompts.total_prompts : null;
  const tone = { LOW: "ok", MEDIUM: "warn", HIGH: "crit", CRITICAL: "crit" }[d?.severity] || "";
  return (<>
    <StatCards items={[
      { label: "Prompts tested", value: tested ?? "–", sub: ctx.prompts ? `${ctx.prompts.total_prompts} in the prompt set` : "" },
      { label: "Activation values", value: a ? a.total_events.toLocaleString() : "–", sub: a ? `${a.layers.length} layers tracked` : "" },
      { label: "Anomalies", value: d ? d.anomalies : "–", tone: d && d.anomalies ? "warn" : "", sub: d?.suspicious_layers.length ? `layers ${d.suspicious_layers.join(", ")}` : "" },
      { label: "Risk score", value: d ? d.risk_score : "–", tone, sub: d ? `${d.severity.toLowerCase()} · prototype indicator` : "" },
    ]} />
    <div className="grid tri">
      <div className="stackcol"><RiskScore detection={d} /><ThreatRadar breakdown={d?.breakdown} /></div>
      <ActivationHeatmap activations={a} suspicious={d?.suspicious_layers} />
      <div className="stackcol"><LayerTrend activations={a} /><BarChart title="Flagged by check (%)" data={d && Object.entries(d.breakdown)} /></div>
    </div>
    <Findings detection={d} />
    <div className="grid pair">
      <PromptStats prompts={r?.prompts || ctx.prompts} />
      {d ? <Donut title="Tested prompts" center={tested} sub="tested" segments={[
        { label: "Flagged", value: d.anomalies, color: "var(--signal)" }, { label: "Clear", value: Math.max(0, tested - d.anomalies), color: "var(--accent)" }]} />
         : <section className="panel"><h2>Tested prompts</h2><p className="empty">Run a scan to see how many prompts were flagged.</p></section>}
    </div>
  </>);
}
