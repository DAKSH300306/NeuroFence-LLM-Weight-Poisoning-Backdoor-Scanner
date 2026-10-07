const COLOR = { LOW: "var(--ok)", MEDIUM: "var(--warn)", HIGH: "var(--signal)", CRITICAL: "var(--signal)" };
export default function RiskScore({ detection }) {
  const score = detection ? detection.risk_score : 0, sev = detection ? detection.severity : null;
  const len = Math.PI * 90;
  return (
    <section className="panel">
      <h2>Backdoor risk</h2>
      <svg viewBox="0 0 200 118" className="gauge" role="img" aria-label={`Risk score ${score} of 100`}>
        <path d="M10 104 A90 90 0 0 1 190 104" className="g-track" />
        <path d="M10 104 A90 90 0 0 1 190 104" className="g-fill"
          style={{ stroke: COLOR[sev] || "var(--line)", strokeDasharray: `${(len * score) / 100} ${len}` }} />
        <text x="100" y="92" textAnchor="middle" className="g-num">{detection ? score : "–"}</text>
        <text x="100" y="112" textAnchor="middle" className="g-sub">{sev ? `${sev.toLowerCase()} risk of 100` : "no scan yet"}</text>
      </svg>
      {detection && <p className="muted">{detection.anomalies} anomalies across layers {detection.suspicious_layers.join(" and ")}. Results are signals to review, not proof of a backdoor.</p>}
    </section>
  );
}
