export default function StatCards({ items }) {
  return (
    <div className="kpis">
      {items.map((i) => (
        <div key={i.label} className={"kpi " + (i.tone || "")}>
          <span className="badge" />
          <div><b className="num">{i.value}</b><small>{i.label}</small>{i.sub && <em>{i.sub}</em>}</div>
        </div>
      ))}
    </div>
  );
}
