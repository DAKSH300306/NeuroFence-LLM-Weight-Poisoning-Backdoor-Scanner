import { useEffect, useState } from "react";
import useScan from "./hooks/useScan.js";
import Sidebar, { ROUTES } from "./components/Sidebar.jsx";
import Header from "./components/Header.jsx";
import ScanProgress from "./components/ScanProgress.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import PromptLab from "./pages/PromptLab.jsx";
import Evidence from "./pages/Evidence.jsx";
import Report from "./pages/Report.jsx";
import { ModelPage, ActivationPage, FindingsPage, History, Settings } from "./pages/Pages.jsx";

const PAGES = { overview: Dashboard, model: ModelPage, prompts: PromptLab, activation: ActivationPage, findings: FindingsPage,
                evidence: Evidence, report: Report, history: History, settings: Settings };
const current = () => window.location.hash.replace(/^#\/?/, "") || "overview";

export default function App() {
  const ctx = useScan();
  const [route, setRoute] = useState(current());
  useEffect(() => {
    const on = () => { setRoute(current()); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  const key = PAGES[route] ? route : "overview", Page = PAGES[key];
  return (
    <div className="shell">
      <Sidebar route={key} mode={ctx.config?.mode} />
      <main className="main">
        <Header title={ROUTES[key]} ctx={ctx} />
        {ctx.error && <div className="alert" role="alert">{ctx.error}</div>}
        <ScanProgress {...ctx.scan} />
        <Page ctx={ctx} />
      </main>
    </div>
  );
}
