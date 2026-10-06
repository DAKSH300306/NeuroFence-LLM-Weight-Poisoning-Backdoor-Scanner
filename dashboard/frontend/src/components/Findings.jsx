const PILL = { Normal: "ok", Warning: "warn", Critical: "crit" };
export default function Findings({ detection }) {
  if (!detection) return (
    <section className="panel" id="findings">
      <h2>Findings</h2>
      <p className="empty">Findings appear here once a scan finishes.</p>
    </section>
  );
  const t = detection.trigger;
  return (
    <section className="panel" id="findings">
      <h2>Findings</h2>
      <div className="trigger">
        <div>
          <p className="muted">Suspected trigger</p>
          <p className="tname">{t.name}</p>
          <p className="muted">Layer {t.layer} · {t.deviation} above baseline · {t.investigation.toLowerCase()}</p>
        </div>
        <div className="conf">
          <span className="num">{t.confidence}%</span>
          <div className="bar"><i style={{ width: t.confidence + "%" }} /></div>
          <small className="muted">confidence</small>
        </div>
      </div>
      <div className="scroll-x">
        <table>
          <thead><tr><th>Prompt</th><th>Layer</th><th>Activation</th><th>Baseline</th><th>Deviation</th><th>Result</th></tr></thead>
          <tbody>
            {detection.table.map((r, i) => (
              <tr key={i}>
                <td>{r[0]}</td><td>{r[1]}</td><td className="num">{r[2].toFixed(2)}</td>
                <td className="num">{r[3].toFixed(2)}</td><td className="num">{r[4]}</td>
                <td><span className={"pill " + PILL[r[5]]}>{r[5]}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {t.confidence >= 50
        ? <p className="muted">Do not deploy until the trigger is reviewed. Re-run the trigger prompts with layer {t.layer} ablated and compare weights against a trusted checkpoint.</p>
        : <p className="muted">No strong trigger signal in this run. Try a larger prompt sample before treating the model as clean.</p>}
    </section>
  );
}
