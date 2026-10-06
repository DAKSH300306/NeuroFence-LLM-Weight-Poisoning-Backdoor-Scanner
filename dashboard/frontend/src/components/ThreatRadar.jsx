export default function ThreatRadar({ breakdown }) {
  const keys = breakdown ? Object.keys(breakdown) : [];
  const c = 110, r = 78, pt = (i, v) => {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / keys.length;
    return [c + Math.cos(a) * r * v, c + Math.sin(a) * r * v];
  };
  const poly = keys.map((k, i) => pt(i, breakdown[k] / 100).join(",")).join(" ");
  return (
    <section className="panel">
      <h2>Where the risk comes from</h2>
      {!breakdown ? <p className="empty">Run a scan to see how each check contributes.</p> : (
        <svg viewBox="0 0 220 220" className="radar" role="img" aria-label="Risk by check">
          {[0.25, 0.5, 0.75, 1].map((s) => (
            <polygon key={s} className="ring" points={keys.map((_, i) => pt(i, s).join(",")).join(" ")} />
          ))}
          {keys.map((k, i) => { const [x, y] = pt(i, 1); return <line key={k} x1={c} y1={c} x2={x} y2={y} className="ring" />; })}
          <polygon points={poly} className="shape" />
          {keys.map((k, i) => {
            const [x, y] = pt(i, breakdown[k] / 100), [lx, ly] = pt(i, 1.2);
            return (<g key={k}>
              <circle cx={x} cy={y} r="3.5" className="pt" />
              <text x={lx} y={ly} textAnchor={Math.abs(lx - c) < 5 ? "middle" : lx > c ? "start" : "end"} dy="0.3em" className="rl">{k} {breakdown[k]}</text>
            </g>);
          })}
        </svg>
      )}
    </section>
  );
}
