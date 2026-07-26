import { useCallback, useEffect, useRef, useState } from "react";
import type { CameraView } from "expo-camera";

/**
 * Détection "main devant l'objectif" sans librairie native.
 * Capture périodique d'une micro-photo : un objectif couvert → JPEG plus petit.
 *
 * Important UX : on ne capture PAS en parallèle (sinon l'écran fige / scintille),
 * et l'intervalle est assez large pour rester fluide sur Expo Go.
 */

const SAMPLE_INTERVAL_MS = 700;
const HOLD_MS = 1000;
const COVER_RATIO = 0.42;
const RELEASE_RATIO = 0.68;
const BASELINE_SAMPLES = 4;

type Options = {
  enabled: boolean;
  cameraRef: React.RefObject<CameraView | null>;
  cameraReady: boolean;
  onTrigger: () => void;
};

export function useHandCoverGesture({ enabled, cameraRef, cameraReady, onTrigger }: Options) {
  const [coverProgress, setCoverProgress] = useState(0);
  const baselineRef = useRef<number | null>(null);
  const baselineSamplesRef = useRef<number[]>([]);
  const coveredSinceRef = useRef<number | null>(null);
  const armedRef = useRef(true);
  const runningRef = useRef(false);
  const busyRef = useRef(false);
  const onTriggerRef = useRef(onTrigger);
  onTriggerRef.current = onTrigger;

  const reset = useCallback(() => {
    baselineRef.current = null;
    baselineSamplesRef.current = [];
    coveredSinceRef.current = null;
    armedRef.current = true;
    busyRef.current = false;
    setCoverProgress(0);
  }, []);

  useEffect(() => {
    if (!enabled || !cameraReady) {
      reset();
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
            quality: 0.05,
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
            baselineRef.current = sorted[Math.floor(sorted.length / 2)];
          }
          busyRef.current = false;
          return;
        }

        const ratio = len / baselineRef.current;
        const now = Date.now();

        if (ratio > RELEASE_RATIO) {
          armedRef.current = true;
        }

        if (ratio < COVER_RATIO && armedRef.current) {
          if (coveredSinceRef.current == null) coveredSinceRef.current = now;
          const held = now - coveredSinceRef.current;
          const progress = Math.min(1, held / HOLD_MS);
          setCoverProgress((prev) => (Math.abs(prev - progress) > 0.04 ? progress : prev));
          if (held >= HOLD_MS) {
            armedRef.current = false;
            coveredSinceRef.current = null;
            setCoverProgress(0);
            onTriggerRef.current();
          }
        } else {
          if (coveredSinceRef.current != null) coveredSinceRef.current = null;
          setCoverProgress((prev) => (prev === 0 ? prev : 0));
        }

        if (ratio > 0.9) {
          baselineRef.current = baselineRef.current * 0.9 + len * 0.1;
        }
        busyRef.current = false;
      })();
    }, SAMPLE_INTERVAL_MS);

    return () => {
      runningRef.current = false;
      clearInterval(interval);
      reset();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, cameraReady]);

  return { coverProgress };
}
