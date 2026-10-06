import { useEffect, useState } from "react";
const NAV = [["scan", "Command Center"], ["layers", "Activation Map"], ["findings", "Threat Findings"], ["model", "Model & Prompts"]];

export default function Sidebar() {
  const [active, setActive] = useState("scan");
  useEffect(() => {  // the section whose top has passed 35% of the viewport is the active one
    const update = () => {
      let cur = NAV[0][0];
      for (const [id] of NAV) {
        const el = document.getElementById(id);
        if (el && el.getBoundingClientRect().top <= window.innerHeight * 0.35) cur = id;
      }
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) cur = NAV[NAV.length - 1][0];
      setActive(cur);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => { window.removeEventListener("scroll", update); window.removeEventListener("resize", update); };
  }, []);
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
        {NAV.map(([id, label]) => (
          <a key={id} href={`#${id}`} className={active === id ? "on" : ""} onClick={() => setActive(id)}>{label}</a>
        ))}
      </nav>
      <div className="rail-foot">
        <span><span className="dot" /> Sandbox online</span>
        <small>Local analysis, no telemetry</small>
      </div>
    </aside>
  );
}
