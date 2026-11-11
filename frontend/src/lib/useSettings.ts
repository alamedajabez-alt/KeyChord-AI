import { useCallback, useState } from "react";

export interface Settings {
  accidentals: "sharps" | "flats";
  showConfidence: boolean;
}

const KEY = "keychord.settings";
const DEFAULTS: Settings = { accidentals: "sharps", showConfidence: true };

function load(): Settings {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) ?? "{}") };
  } catch {
    return DEFAULTS;
  }
}

export function useSettings() {
  const [settings, setSettings] = useState<Settings>(load);
  const update = useCallback((patch: Partial<Settings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...patch };
      try {
        localStorage.setItem(KEY, JSON.stringify(next));
      } catch {
        /* storage unavailable: keep in-memory value */
      }
      return next;
    });
  }, []);
  return { settings, update };
}
