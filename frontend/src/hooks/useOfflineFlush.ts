import { useEffect, useRef } from "react";
import { AppState, type AppStateStatus } from "react-native";

import { flushQueue, peekQueue } from "@/lib/offlineQueue";

/**
 * Rejoue la file offline au démarrage et à chaque retour au premier plan.
 */
export function useOfflineFlush() {
  const flushing = useRef(false);

  useEffect(() => {
    const run = async () => {
      if (flushing.current) return;
      const q = await peekQueue();
      if (!q.length) return;
      flushing.current = true;
      try {
        await flushQueue();
      } finally {
        flushing.current = false;
      }
    };

    void run();

    const onChange = (state: AppStateStatus) => {
      if (state === "active") void run();
    };
    const sub = AppState.addEventListener("change", onChange);
    const interval = setInterval(() => void run(), 30_000);
    return () => {
      sub.remove();
      clearInterval(interval);
    };
  }, []);
}
