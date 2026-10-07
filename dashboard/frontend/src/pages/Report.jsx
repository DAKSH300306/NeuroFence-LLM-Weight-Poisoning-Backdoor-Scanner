export default function Report({ ctx }) {
  const r = ctx.result, d = r?.detection;
  if (!r) return <section className="panel"><h2>Forensic report</h2><p className="empty">Run a scan to generate a report.</p></section>;
  const t = d.trigger;
  return (
    <section className="panel report">
      <div className="row between"><h2>Forensic report</h2><button className="btn noprint" onClick={() => window.print()}>Print / save as PDF</button></div>
      <dl className="kv"><dt>Model</dt><dd>{r.model.name}</dd><dt>Scanned</dt><dd>{r.timestamp}</dd><dt>SHA-256</dt><dd className="hash">{r.model.hash}</dd><dt>Integrity</dt><dd>{r.model.status}</dd></dl>
      <h3>Summary</h3>
      <p>The model was tested with {d.tested ?? r.prompts.total_prompts} prompts and {r.activations.total_events.toLocaleString()} recorded activation values across {r.activations.layers.length} layers. {d.anomalies} prompts showed activation anomalies, mainly in layers {d.suspicious_layers.join(", ") || "none"}. The prototype risk score is {d.risk_score} ({d.severity.toLowerCase()}).</p>
      <h3>Suspected trigger</h3>
      <p>{t.name} · layer {t.layer} · {t.deviation} peak deviation · confidence {t.confidence}% · {t.status.toLowerCase()}.</p>
      <h3>Strongest observations</h3>
      <table><thead><tr><th>Prompt</th><th>Layer</th><th>Deviation</th><th>Result</th></tr></thead>
        <tbody>{d.table.map((x, i) => <tr key={i}><td>{x[0]}</td><td>{x[1]}</td><td>{x[4]}</td><td>{x[5]}</td></tr>)}</tbody></table>
      <p className="muted">Limits: results are preliminary signals from activation Z-scores against a baseline of normal prompts. They are not proof of a backdoor and have not been validated on a known-clean versus known-backdoored model.</p>
    </section>
  );
}
