import { Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import MarketingLayout from "./components/layout/MarketingLayout";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Landing from "./pages/Landing";
import NotFound from "./pages/NotFound";
import Settings from "./pages/Settings";
import Upload from "./pages/Upload";
import Workspace from "./pages/Workspace";

export default function App() {
  return (
    <Routes>
      <Route element={<MarketingLayout />}>
        <Route index element={<Landing />} />
      </Route>
      <Route element={<AppShell />}>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="upload" element={<Upload />} />
        <Route path="history" element={<History />} />
        <Route path="settings" element={<Settings />} />
        <Route path="workspace" element={<Workspace />} />
        <Route path="workspace/:songId" element={<Workspace />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
