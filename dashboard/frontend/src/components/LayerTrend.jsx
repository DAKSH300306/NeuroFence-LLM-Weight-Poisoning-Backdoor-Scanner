export default function LayerTrend({ activations: a }) {
  if (!a) return <section className="panel"><h2>Layer response profile</h2><p className="empty">Run a scan to compare normal and trigger prompts layer by layer.</p></section>;
  const { layers, prompt_types: t, activation_matrix: m } = a, n = layers.length, W = 320, H = 140;
  const ti = Math.max(0, t.findIndex((x) => /trigger/i.test(x)));
  const px = (i) => 20 + (n > 1 ? (i * (W - 30)) / (n - 1) : 0), py = (v) => H - 18 - v * (H - 36);
  const line = (k) => m.map((row, i) => `${px(i)},${py(row[k])}`).join(" ");
  return (
    <section className="panel">
      <h2>Layer response profile</h2>
      <svg viewBox={`0 0 ${W} ${H}`} className="trend" role="img" aria-label="Response by layer, normal versus trigger">
        <defs><linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#ff4d5e" stopOpacity=".4" /><stop offset="1" stopColor="#ff4d5e" stopOpacity="0" /></linearGradient></defs>
        {[0, 0.5, 1].map((g) => <line key={g} x1="20" x2={W - 10} y1={py(g)} y2={py(g)} className="ring" />)}
        <polygon points={`${px(0)},${H - 18} ${line(ti)} ${px(n - 1)},${H - 18}`} fill="url(#tg)" />
        <polyline points={line(0)} className="ln n" /><polyline points={line(ti)} className="ln t" />
        {layers.map((l, i) => i % Math.ceil(n / 8) === 0 && <text key={l} x={px(i)} y={H - 4} textAnchor="middle" className="hl">{l}</text>)}
      </svg>
      <div className="scale"><span><b className="sw n" />Normal</span><span><b className="sw t" />Trigger candidate</span></div>
    </section>
  );
}
