export default function Header({ model, state, onStart, onStop, onReset }) {
  const running = state === "running", done = state === "done";
  return (
    <header className="head" id="scan">
      <div>
        <p className="muted">Model under inspection</p>
        <h1>{model ? model.name : "Loading…"}</h1>
        {model && <p className="muted">{model.format} · {model.parameters} parameters · {model.size}</p>}
      </div>
      <div className="actions">
        {done && (<>
          <a className="btn" href="/api/export/json" download>Export JSON</a>
          <a className="btn" href="/api/export/csv" download>Export CSV</a>
        </>)}
        {(done || running) && <button className="btn" onClick={onReset}>Reset</button>}
        {running
          ? <button className="btn danger" onClick={onStop}>Stop scan</button>
          : <button className="btn primary" onClick={onStart}>{done ? "Scan again" : "Start scan"}</button>}
      </div>
    </header>
  );
}
