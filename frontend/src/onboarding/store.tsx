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
  /** Étape à reprendre si l'onboarding a été interrompu (null si terminé/pas commencé). */
  resumeStep: StepId | null;
  patch: <K extends StepId>(step: K, values: Partial<OnboardingData[K]>) => void;
  complete: () => void;
  reset: () => void;
  /** Restaure data/done/resumeStep depuis la vérité serveur (login, reload). */
  hydrate: (patch: Partial<OnboardingData>, done: boolean, resumeStep: StepId | null) => void;
};

const OnboardingContext = createContext<Ctx | null>(null);

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<OnboardingData>(initialData);
  const [done, setDone] = useState(false);
  const [resumeStep, setResumeStep] = useState<StepId | null>(null);

  const patch = useCallback(
    <K extends StepId>(step: K, values: Partial<OnboardingData[K]>) => {
      setData((prev) => ({ ...prev, [step]: { ...prev[step], ...values } }));
    },
    []
  );

  const complete = useCallback(() => {
    setDone(true);
    setResumeStep(null);
  }, []);
  const reset = useCallback(() => {
    setData(initialData);
    setDone(false);
    setResumeStep(null);
  }, []);

  const hydrate = useCallback(
    (patchData: Partial<OnboardingData>, isDone: boolean, nextStep: StepId | null) => {
      setData((prev) => {
        const next = { ...prev } as OnboardingData;
        for (const key of Object.keys(patchData) as StepId[]) {
          // Fusion dynamique par étape : les formes de chaque étape diffèrent,
          // donc TS ne peut pas vérifier statiquement cette boucle générique.
          (next as Record<StepId, unknown>)[key] = {
            ...(prev as Record<StepId, object>)[key],
            ...(patchData as Record<StepId, object>)[key],
          };
        }
        return next;
      });
      setDone(isDone);
      setResumeStep(nextStep);
    },
    []
  );

  const value = useMemo(
    () => ({ data, done, resumeStep, patch, complete, reset, hydrate }),
    [data, done, resumeStep, patch, complete, reset, hydrate]
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
