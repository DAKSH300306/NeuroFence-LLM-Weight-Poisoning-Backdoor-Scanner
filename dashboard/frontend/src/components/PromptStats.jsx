export default function PromptStats({ prompts }) {
  if (!prompts) return null;
  const parts = [["Normal", prompts.normal, "var(--ink)"], ["Unusual", prompts.unusual, "var(--warn)"], ["Trigger candidates", prompts.trigger_candidates, "var(--signal)"]];
  return (
    <section className="panel">
      <div className="row between"><h2>Test prompts</h2><span className="num big">{prompts.total_prompts.toLocaleString()}</span></div>
      <div className="stack" role="img" aria-label="Prompt mix">
        {parts.map(([n, v, c]) => <i key={n} style={{ flex: v, background: c }} title={`${n}: ${v}`} />)}
      </div>
      <ul className="legend">
        {parts.map(([n, v, c]) => <li key={n}><b style={{ background: c }} />{n}<span className="num">{v.toLocaleString()}</span></li>)}
      </ul>
    </section>
  );
}
