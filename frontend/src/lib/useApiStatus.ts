import { useEffect, useState } from "react";
import { api } from "./api";

export type ApiStatus = "checking" | "online" | "offline";

export function useApiStatus(): ApiStatus {
  const [status, setStatus] = useState<ApiStatus>("checking");
  useEffect(() => {
    let alive = true;
    api<{ status: string }>("/health")
      .then(() => alive && setStatus("online"))
      .catch(() => alive && setStatus("offline"));
    return () => {
      alive = false;
    };
  }, []);
  return status;
}
