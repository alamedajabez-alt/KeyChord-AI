import { Music2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "./lib/api";

type Status = "checking" | "online" | "offline";

// Phase 1 only: proves the frontend can reach the API. Real pages arrive in Phase 2.
export default function App() {
  const [status, setStatus] = useState<Status>("checking");
  useEffect(() => {
    api<{ status: string }>("/health")
      .then(() => setStatus("online"))
      .catch(() => setStatus("offline"));
  }, []);

  return (
    <main className="min-h-screen grid place-items-center">
      <div className="text-center space-y-3">
        <Music2 className="mx-auto h-10 w-10 text-accent-soft" />
        <h1 className="text-3xl font-semibold">KeyChord AI</h1>
        <p className="text-slate-400">
          API status: <span className={status === "online" ? "text-emerald-400" : "text-amber-400"}>{status}</span>
        </p>
      </div>
    </main>
  );
}
