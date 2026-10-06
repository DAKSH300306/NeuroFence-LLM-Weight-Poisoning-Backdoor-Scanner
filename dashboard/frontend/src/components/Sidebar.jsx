import { useEffect, useState } from "react";
const NAV = [["scan", "Scan"], ["layers", "Layer activity"], ["findings", "Findings"], ["model", "Model & prompts"]];

export default function Sidebar() {
  const [active, setActive] = useState("scan");
  useEffect(() => {
    const io = new IntersectionObserver(
      (es) => es.forEach((e) => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: "-30% 0px -60% 0px" }
    );
    NAV.forEach(([id]) => { const el = document.getElementById(id); el && io.observe(el); });
    return () => io.disconnect();
  }, []);
  return (
    <aside className="rail">
      <div className="brand">
        <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true">
          <rect x="2" y="2" width="22" height="22" rx="6" fill="none" stroke="currentColor" strokeWidth="2" />
          <path d="M7 17V9l6 8V9M19 9v8" fill="none" stroke="var(--signal)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span>NeuroFence</span>
      </div>
      <nav>
        {NAV.map(([id, label]) => (
          <a key={id} href={`#${id}`} className={active === id ? "on" : ""}>{label}</a>
        ))}
      </nav>
      <div className="rail-foot">
        <span className="dot" /> Sandbox online
        <small>Local, offline analysis</small>
      </div>
    </aside>
  );
}
