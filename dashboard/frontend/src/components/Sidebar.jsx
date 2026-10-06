import { useEffect, useState } from "react";
const NAV = [["scan", "Scan"], ["layers", "Layer activity"], ["findings", "Findings"], ["model", "Model & prompts"]];
const systemDark = () => window.matchMedia("(prefers-color-scheme: dark)").matches;

export default function Sidebar() {
  const [active, setActive] = useState("scan");
  const [theme, setTheme] = useState(() => { try { return localStorage.getItem("nf-theme") || "auto"; } catch { return "auto"; } });

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

  useEffect(() => {
    const root = document.documentElement;
    theme === "auto" ? root.removeAttribute("data-theme") : root.setAttribute("data-theme", theme);
    try { localStorage.setItem("nf-theme", theme); } catch {}
  }, [theme]);

  const dark = theme === "auto" ? systemDark() : theme === "dark";
  return (
    <aside className="rail">
      <div className="brand">
        <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true">
          <rect x="2" y="2" width="22" height="22" rx="6" fill="none" stroke="currentColor" strokeWidth="2" />
          <path d="M7 17V9l6 8V9M19 9v8" fill="none" stroke="var(--mark)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span>NeuroFence</span>
      </div>
      <nav>
        {NAV.map(([id, label]) => (
          <a key={id} href={`#${id}`} className={active === id ? "on" : ""} onClick={() => setActive(id)}>{label}</a>
        ))}
      </nav>
      <div className="rail-foot">
        <button className="theme" onClick={() => setTheme(dark ? "light" : "dark")}>{dark ? "Switch to light" : "Switch to dark"}</button>
        <span><span className="dot" /> Sandbox online</span>
        <small>Local, offline analysis</small>
      </div>
    </aside>
  );
}
