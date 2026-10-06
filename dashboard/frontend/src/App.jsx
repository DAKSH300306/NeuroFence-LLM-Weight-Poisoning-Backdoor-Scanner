import Sidebar from "./components/Sidebar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
export default function App() {
  return (
    <div className="shell">
      <Sidebar />
      <Dashboard />
    </div>
  );
}
