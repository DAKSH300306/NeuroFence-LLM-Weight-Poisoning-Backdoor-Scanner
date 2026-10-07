const ICON = {
  overview: "M3 12l9-8 9 8M5 10v10h14V10", model: "M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z", prompts: "M4 6h16M4 12h16M4 18h10",
  activation: "M3 12h4l3-8 4 16 3-8h4", findings: "M12 3l10 18H2L12 3zM12 10v5M12 18v.5", evidence: "M4 7h16v12H4zM9 7V4h6v3",
  report: "M6 3h9l4 4v14H6zM9 12h7M9 16h7", history: "M12 7v5l3 2M4 12a8 8 0 1 0 3-6.2M4 4v4h4",
  settings: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v3M12 19v3M2 12h3M19 12h3",
};
export const ROUTES = { overview: "Command Center", model: "Model Intelligence", prompts: "Prompt Lab", activation: "Activation Map",
  findings: "Threat Findings", evidence: "Evidence Vault", report: "Forensic Report", history: "Scan History", settings: "Settings" };
const GROUPS = [["Investigate", ["overview", "model", "prompts", "activation", "findings"]], ["Case files", ["evidence", "report", "history"]], ["System", ["settings"]]];

export default function Sidebar({ route, mode }) {
  return (
    <aside className="rail">
      <div className="brand">
        <svg width="28" height="28" viewBox="0 0 26 26" aria-hidden="true">
          <rect x="2" y="2" width="22" height="22" rx="6" fill="none" stroke="var(--accent)" strokeWidth="1.6" />
          <path d="M7 17V9l6 8V9M19 9v8" fill="none" stroke="var(--violet)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span>NEUROFENCE<small>AI model forensics</small></span>
      </div>
      <nav>
        {GROUPS.map(([g, ids]) => (
          <div key={g}>
            <h3>{g}</h3>
            {ids.map((id) => (
              <a key={id} href={`#/${id}`} className={route === id ? "on" : ""}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={ICON[id]} /></svg>
                {ROUTES[id]}
              </a>
            ))}
          </div>
        ))}
      </nav>
      <div className="rail-foot">
        <h3>System health</h3>
        <span><span className="dot" /> Sandbox online</span>
        <span><span className={"dot " + (mode === "live" ? "" : "amber")} /> Pipeline: {mode === "live" ? "live" : "demo data"}</span>
        <small>Local analysis, no telemetry</small>
      </div>
    </aside>
  );
}
