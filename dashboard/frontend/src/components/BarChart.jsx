export default function BarChart({ title, data }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {!data ? <p className="empty">Run a scan to see this chart.</p> : (
        <div className="bars">
          {data.map(([l, v]) => (
            <div key={l} className="barcol" title={`${l}: ${v}%`}>
              <span className="num">{v}%</span>
              <div className="track"><i className={v >= 50 ? "hot" : ""} style={{ height: `${Math.max(4, v)}%` }} /></div>
              <small>{l.replace(" prompts", "")}</small>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
