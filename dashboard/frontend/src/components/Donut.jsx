export default function Donut({ title, segments, center, sub }) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1, R = 52, C = 2 * Math.PI * R;
  let off = 0;
  return (
    <section className="panel">
      <h2>{title}</h2>
      <div className="donutwrap">
        <svg viewBox="0 0 140 140" className="donut" role="img" aria-label={title}>
          <circle cx="70" cy="70" r={R} className="g-track" style={{ strokeWidth: 14 }} />
          {segments.map((s) => {
            const len = (C * s.value) / total;
            const el = <circle key={s.label} cx="70" cy="70" r={R} fill="none" stroke={s.color} strokeWidth="14" strokeDasharray={`${len} ${C - len}`} strokeDashoffset={-off} transform="rotate(-90 70 70)" />;
            off += len; return el;
          })}
          <text x="70" y="68" textAnchor="middle" className="g-num" style={{ fontSize: 26 }}>{center}</text>
          <text x="70" y="86" textAnchor="middle" className="g-sub">{sub}</text>
        </svg>
        <ul className="legend">
          {segments.map((s) => <li key={s.label}><b style={{ background: s.color }} />{s.label}<span className="num">{s.value}</span></li>)}
        </ul>
      </div>
    </section>
  );
}
