import { useEffect, useRef } from "react";
import type { CameraView } from "expo-camera";

/**
 * Détection de main devant la caméra selfie (Expo Go, sans ML).
 *
 * v3 (senior) :
 * - taille JPEG (main = assombrissement)
 * - stabilité : variance basse sur 3 frames = couverture réelle (pas un flash)
 * - double armement : main détectée → hold → release → réarme
 *
 * MediaPipe Hands reste le chemin idéal hors Expo Go (custom native).
 */

const SAMPLE_INTERVAL_MS = 320;
const BASELINE_SAMPLES = 6;
const HAND_RATIO = 0.52;
const STRONG_HAND_RATIO = 0.32;
const RELEASE_RATIO = 0.84;
const COOLDOWN_MS = 1100;
const STREAK_NEEDED = 3;
/** Variance relative max entre frames "main" (stabilité). */
const MAX_STREAK_VARIANCE = 0.12;

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
  const streakRatiosRef = useRef<number[]>([]);
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
      streakRatiosRef.current = [];
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

        // Drift lent du baseline seulement si image « normale »
        if (ratio > 0.9 && armedRef.current) {
          baselineRef.current = baselineRef.current * 0.95 + len * 0.05;
        }

        const handNow = ratio < HAND_RATIO;

        if (handNow !== handPresentRef.current) {
          handPresentRef.current = handNow;
          onHandChangeRef.current?.(handNow);
        }

        if (handNow) {
          lowStreakRef.current += 1;
          streakRatiosRef.current.push(ratio);
          if (streakRatiosRef.current.length > STREAK_NEEDED) {
            streakRatiosRef.current.shift();
          }
        } else {
          lowStreakRef.current = 0;
          streakRatiosRef.current = [];
          if (ratio >= RELEASE_RATIO) {
            armedRef.current = true;
          }
        }

        const streak = streakRatiosRef.current;
        const mean =
          streak.length > 0
            ? streak.reduce((a, b) => a + b, 0) / streak.length
            : 1;
        const variance =
          streak.length > 1
            ? streak.reduce((s, r) => s + (r - mean) ** 2, 0) / streak.length
            : 0;
        const stable = variance <= MAX_STREAK_VARIANCE;

        const detected =
          (lowStreakRef.current >= STREAK_NEEDED && stable) ||
          (lowStreakRef.current >= 1 && ratio < STRONG_HAND_RATIO);

        if (armedRef.current && detected && now >= cooldownUntilRef.current) {
          armedRef.current = false;
          lowStreakRef.current = 0;
          streakRatiosRef.current = [];
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

  return { coverProgress: 0 };
}
