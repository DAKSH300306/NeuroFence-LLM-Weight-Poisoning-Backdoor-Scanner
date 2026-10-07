import { useEffect, useState } from "react";
import StatCards from "../components/StatCards.jsx";
const TYPES = ["", "normal", "edge", "long", "trigger"];

export default function PromptLab() {
  const [type, setType] = useState(""), [q, setQ] = useState(""), [data, setData] = useState(null), [err, setErr] = useState("");
  useEffect(() => {
    const t = setTimeout(() => fetch(`/api/prompts/list?type=${type}&q=${encodeURIComponent(q)}`).then((r) => r.json()).then((d) => { setData(d); setErr(""); }).catch(() => setErr("Can't load prompts.")), 200);
    return () => clearTimeout(t);
  }, [type, q]);
  const c = data?.counts || {};
  return (<>
    <StatCards items={["normal", "edge", "long", "trigger"].map((k) => ({ label: k + " prompts", value: c[k] ?? "–", tone: k === "trigger" ? "crit" : "" }))} />
    <section className="panel"><h2>Prompt set</h2>
      <div className="filters">
        <input placeholder="Search prompts" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search prompts" />
        <select value={type} onChange={(e) => setType(e.target.value)} aria-label="Filter by type">{TYPES.map((t) => <option key={t} value={t}>{t || "All types"}</option>)}</select>
        {data && <span className="muted">showing {data.rows.length} of {data.total}</span>}
      </div>
      {err && <p className="empty">{err}</p>}
      <div className="scroll-x"><table>
        <thead><tr><th>ID</th><th>Prompt</th><th>Type</th><th>Result</th><th>Score</th></tr></thead>
        <tbody>{data?.rows.map((r) => (
          <tr key={r.id}><td>{r.id}</td><td className="ptext">{r.prompt || "(empty)"}</td><td>{r.type}</td>
            <td><span className={"pill " + (!r.tested ? "" : r.flagged ? "warn" : "ok")}>{!r.tested ? "Not tested" : r.flagged ? "Flagged" : "Clear"}</span></td>
            <td className="num">{r.score ?? "–"}</td></tr>))}</tbody>
      </table></div>
      <p className="muted">Only the prompts used in the last scan have a result. Flagged means activation anomalies, not proof of a backdoor.</p>
    </section>
  </>);
}
