// Cell colour runs navy, violet, cyan as the response gets stronger.
const fill = (v) => {
  const t = Math.min(1, Math.max(0, v));
  return t < 0.5
    ? `color-mix(in oklab, var(--violet) ${Math.round(t * 200)}%, var(--heat-lo))`
    : `color-mix(in oklab, var(--heat-hi) ${Math.round((t - 0.5) * 200)}%, var(--violet))`;
};

export default function ActivationHeatmap({ activations, suspicious = [] }) {
  const W = 26, H = 40, L = 118, T = 34;
  if (!activations) return (
    <section className="panel" id="layers">
      <h2>Layer activity</h2>
      <p className="empty">Start a scan to see which layers react to which kinds of prompt.</p>
    </section>
  );
  const { layers, prompt_types, activation_matrix: m } = activations;
  return (
    <section className="panel" id="layers">
      <div className="row between">
        <h2>Layer activity</h2>
        <span className="muted">{activations.total_events.toLocaleString()} activation values recorded</span>
      </div>
      <div className="scroll-x">
        <svg viewBox={`0 0 ${L + layers.length * W + 8} ${T + prompt_types.length * H + 14}`} className="heat" style={{ minWidth: 560 }}>
          {layers.map((ly, x) => (
            <text key={ly} x={L + x * W + W / 2} y={T - 10} textAnchor="middle" className={"hl " + (suspicious.includes(ly) ? "hot" : "")}>{ly}</text>
          ))}
          {prompt_types.map((p, y) => (
            <text key={p} x={L - 10} y={T + y * H + H / 2} textAnchor="end" dy="0.35em" className="hl row">{p}</text>
          ))}
          {m.map((row, x) => row.map((v, y) => (
            <rect key={x + "-" + y} x={L + x * W + 1} y={T + y * H + 1} width={W - 2} height={H - 2} rx="3" style={{ fill: fill(v) }}>
              <title>{`Layer ${layers[x]}, ${prompt_types[y]}: ${Math.round(v * 100)}% of the strongest response`}</title>
            </rect>
          )))}
          {suspicious.map((ly) => {
            const x = layers.indexOf(ly); if (x < 0) return null;
            return <rect key={ly} x={L + x * W - 1} y={T - 3} width={W + 2} height={prompt_types.length * H + 6} rx="5" className="flag" />;
          })}
        </svg>
      </div>
      <div className="scale"><span>weaker</span><i /><span>stronger response</span>
        <span className="flagkey"><b />flagged layer</span></div>
    </section>
  );
}
