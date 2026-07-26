import { useEffect, useRef } from "react";
import type { CameraView } from "expo-camera";

/**
 * Détection de main devant la caméra selfie (Expo Go, sans ML).
 *
 * Principe : micro-captures JPEG. Une main devant l'objectif assombrit /
 * uniformise l'image → JPEG nettement plus petit. Dès que 2 captures
 * consécutives sont "basses", on considère la main détectée → on avance.
 * Ensuite il faut retirer la main avant le prochain déclenchement.
 *
 * Aucun setState pendant la boucle → évite le scintillement de l'UI.
 */

const SAMPLE_INTERVAL_MS = 420;
const BASELINE_SAMPLES = 4;
/** Seuil large : une main devant la selfie suffit (cuisine souvent lumineuse). */
const HAND_RATIO = 0.62;
const STRONG_HAND_RATIO = 0.4;
const RELEASE_RATIO = 0.78;
const COOLDOWN_MS = 800;

type Options = {
  enabled: boolean;
  cameraRef: React.RefObject<CameraView | null>;
  cameraReady: boolean;
  onTrigger: () => void;
  /** Optionnel : true pendant que la main est devant (pour un feedback UI rare). */
  onHandChange?: (handPresent: boolean) => void;
};

export function useHandCoverGesture({
  enabled,
  cameraRef,
  cameraReady,
  onTrigger,
  onHandChange,
}: Options) {
  const baselineRef = useRef<number | null>(null);
  const baselineSamplesRef = useRef<number[]>([]);
  const lowStreakRef = useRef(0);
  const armedRef = useRef(true);
  const cooldownUntilRef = useRef(0);
  const runningRef = useRef(false);
  const busyRef = useRef(false);
  const handPresentRef = useRef(false);
  const onTriggerRef = useRef(onTrigger);
  const onHandChangeRef = useRef(onHandChange);
  onTriggerRef.current = onTrigger;
  onHandChangeRef.current = onHandChange;

  useEffect(() => {
    if (!enabled || !cameraReady) {
      baselineRef.current = null;
      baselineSamplesRef.current = [];
      lowStreakRef.current = 0;
      armedRef.current = true;
      busyRef.current = false;
      if (handPresentRef.current) {
        handPresentRef.current = false;
        onHandChangeRef.current?.(false);
      }
      return;
    }

    runningRef.current = true;
    const interval = setInterval(() => {
      if (!runningRef.current || !cameraRef.current || busyRef.current) return;
      busyRef.current = true;

      void (async () => {
        let len = 0;
        try {
          const photo = await cameraRef.current?.takePictureAsync({
            base64: true,
            quality: 0.01,
            skipProcessing: true,
            shutterSound: false,
          });
          len = photo?.base64?.length ?? 0;
        } catch {
          busyRef.current = false;
          return;
        }

        if (!len || !runningRef.current) {
          busyRef.current = false;
          return;
        }

        if (baselineRef.current == null) {
          baselineSamplesRef.current.push(len);
          if (baselineSamplesRef.current.length >= BASELINE_SAMPLES) {
            const sorted = [...baselineSamplesRef.current].sort((a, b) => a - b);
            baselineRef.current = sorted[Math.floor(sorted.length / 2)] || len;
          }
          busyRef.current = false;
          return;
        }

        const now = Date.now();
        const ratio = len / baselineRef.current;

        if (ratio > 0.88 && armedRef.current) {
          baselineRef.current = baselineRef.current * 0.93 + len * 0.07;
        }

        const handNow = ratio < HAND_RATIO;

        if (handNow !== handPresentRef.current) {
          handPresentRef.current = handNow;
          onHandChangeRef.current?.(handNow);
        }

        if (handNow) {
          lowStreakRef.current += 1;
        } else {
          lowStreakRef.current = 0;
          if (ratio >= RELEASE_RATIO) {
            armedRef.current = true;
          }
        }

        // 1 capture très sombre OU 2 captures "main devant" → avance
        const detected =
          lowStreakRef.current >= 2 ||
          (lowStreakRef.current >= 1 && ratio < STRONG_HAND_RATIO);

        if (armedRef.current && detected && now >= cooldownUntilRef.current) {
          armedRef.current = false;
          lowStreakRef.current = 0;
          cooldownUntilRef.current = now + COOLDOWN_MS;
          onTriggerRef.current();
        }

        busyRef.current = false;
      })();
    }, SAMPLE_INTERVAL_MS);

    return () => {
      runningRef.current = false;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, cameraReady]);

  // Plus de coverProgress animé (ça faisait scintiller tout l'écran).
  return { coverProgress: 0 };
}
