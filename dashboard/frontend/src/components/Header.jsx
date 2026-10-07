export default function Header({ title, ctx }) {
  const { model, config, scan, result, start, stop, reset } = ctx;
  const running = scan.state === "running", done = scan.state === "done";
  return (
    <header className="head">
      <div>
        <p className="muted">{model?.name || "Loading…"} · {config?.mode === "live" ? "live pipeline" : "demo data"}{result?.timestamp ? ` · scanned ${result.timestamp}` : ""}</p>
        <h1>{title}</h1>
      </div>
      <div className="actions">
        {done && (<>
          <a className="btn" href="/api/export/json" download>Export JSON</a>
          <a className="btn" href="/api/export/csv" download>Export CSV</a>
        </>)}
        {scan.state !== "idle" && <button className="btn" onClick={reset}>Reset</button>}
        {running ? <button className="btn danger" onClick={stop}>Stop scan</button>
                 : <button className="btn primary" onClick={start}>{done ? "Scan again" : "Start scan"}</button>}
      </div>
    </header>
  );
}
