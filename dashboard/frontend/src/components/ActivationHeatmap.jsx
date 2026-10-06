const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
const LOW = [226, 234, 231], MID = [227, 155, 27], HIGH = [209, 23, 90];
const color = (v) => {  // 0..1 -> pale -> amber -> magenta
  const t = Math.min(1, Math.max(0, v));
  return `rgb(${(t < 0.5 ? mix(LOW, MID, t * 2) : mix(MID, HIGH, (t - 0.5) * 2)).join(",")})`;
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
        <span className="muted">{activations.total_events.toLocaleString()} events · brighter means stronger response</span>
      </div>
      <div className="scroll-x">
        <svg viewBox={`0 0 ${L + layers.length * W + 8} ${T + prompt_types.length * H + 14}`} className="heat" style={{ minWidth: 760 }}>
          {layers.map((ly, x) => (
            <text key={ly} x={L + x * W + W / 2} y={T - 10} textAnchor="middle" className={"hl " + (suspicious.includes(ly) ? "hot" : "")}>{ly}</text>
          ))}
          {prompt_types.map((p, y) => (
            <text key={p} x={L - 10} y={T + y * H + H / 2} textAnchor="end" dy="0.35em" className="hl row">{p}</text>
          ))}
          {m.map((row, x) => row.map((v, y) => (
            <rect key={x + "-" + y} x={L + x * W + 1} y={T + y * H + 1} width={W - 2} height={H - 2} rx="3" fill={color(v)}>
              <title>{`Layer ${layers[x]}, ${prompt_types[y]}: ${v.toFixed(2)}`}</title>
            </rect>
          )))}
          {suspicious.map((ly) => {
            const x = layers.indexOf(ly); if (x < 0) return null;
            return <rect key={ly} x={L + x * W - 1} y={T - 3} width={W + 2} height={prompt_types.length * H + 6} rx="5" className="flag" />;
          })}
        </svg>
      </div>
      <p className="muted">Outlined columns are layers flagged for review. The trigger-candidate row is the one to compare against normal prompts.</p>
    </section>
  );
}
