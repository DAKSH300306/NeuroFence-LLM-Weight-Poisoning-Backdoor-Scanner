export default function Header({ model, config, when, state, onStart, onStop, onReset, onConfig }) {
  const running = state === "running", done = state === "done";
  return (
    <header className="head" id="scan">
      <div>
        <p className="muted">Model under inspection · {config?.mode === "live" ? "live pipeline" : "demo data"}{when ? ` · scanned ${when}` : ""}</p>
        <h1>{model ? model.name : "Loading…"}</h1>
        {model && <p className="muted">{model.format} · {model.size} · {model.source}</p>}
        <div className="modelpick">
          <label>Model name or folder
            <input key={config?.model} defaultValue={config?.model || ""} disabled={running} spellCheck="false"
              onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
              onBlur={(e) => e.target.value.trim() !== config?.model && onConfig({ model: e.target.value })} />
          </label>
          <label className="chk"><input type="checkbox" checked={!!config?.local_only} disabled={running}
            onChange={(e) => onConfig({ local_only: e.target.checked })} /> Offline only</label>
        </div>
      </div>
      <div className="actions">
        {done && (<>
          <a className="btn" href="/api/export/json" download>Export JSON</a>
          <a className="btn" href="/api/export/csv" download>Export CSV</a>
        </>)}
        {state !== "idle" && <button className="btn" onClick={onReset}>Reset</button>}
        {running
          ? <button className="btn danger" onClick={onStop}>Stop scan</button>
          : <button className="btn primary" onClick={onStart}>{done ? "Scan again" : "Start scan"}</button>}
      </div>
    </header>
  );
}
