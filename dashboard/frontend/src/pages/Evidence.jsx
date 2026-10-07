import { useEffect, useState } from "react";
export default function Evidence() {
  const [rows, setRows] = useState(null);
  useEffect(() => { fetch("/api/evidence").then((r) => r.json()).then(setRows).catch(() => setRows([])); }, []);
  return (
    <section className="panel"><h2>Evidence files</h2>
      {rows && !rows.length && <p className="empty">No scan output yet. Run a scan to create evidence files.</p>}
      {!!rows?.length && <div className="scroll-x"><table>
        <thead><tr><th>File</th><th>Location</th><th>Size</th><th>Modified</th><th>SHA-256</th><th /></tr></thead>
        <tbody>{rows.map((r) => (
          <tr key={r.path}><td>{r.name}</td><td className="muted">{r.path}</td><td className="num">{(r.size / 1024).toFixed(1)} KB</td><td>{r.modified}</td>
            <td className="hash">{r.sha256.slice(0, 16)}…{r.sha256.slice(-6)}</td>
            <td><button className="btn" onClick={() => navigator.clipboard?.writeText(r.sha256)}>Copy hash</button></td></tr>))}</tbody>
      </table></div>}
      <p className="muted">Hashes are calculated now from the files on disk. Compare them later to show a result file was not changed.</p>
    </section>
  );
}
