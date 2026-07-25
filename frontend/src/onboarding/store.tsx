import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { initialData, type OnboardingData, type StepId } from "./types";

type Ctx = {
  data: OnboardingData;
  done: boolean;
  patch: <K extends StepId>(step: K, values: Partial<OnboardingData[K]>) => void;
  complete: () => void;
  reset: () => void;
};

const OnboardingContext = createContext<Ctx | null>(null);

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<OnboardingData>(initialData);
  const [done, setDone] = useState(false);

  const patch = useCallback(
    <K extends StepId>(step: K, values: Partial<OnboardingData[K]>) => {
      setData((prev) => ({ ...prev, [step]: { ...prev[step], ...values } }));
    },
    []
  );

  const complete = useCallback(() => setDone(true), []);
  const reset = useCallback(() => {
    setData(initialData);
    setDone(false);
  }, []);

  const value = useMemo(
    () => ({ data, done, patch, complete, reset }),
    [data, done, patch, complete, reset]
  );

  return (
    <OnboardingContext.Provider value={value}>{children}</OnboardingContext.Provider>
  );
}

export function useOnboarding() {
  const ctx = useContext(OnboardingContext);
  if (!ctx) throw new Error("useOnboarding hors OnboardingProvider");
  return ctx;
}
