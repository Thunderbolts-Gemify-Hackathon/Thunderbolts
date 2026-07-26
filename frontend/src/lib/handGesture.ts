import { useCallback, useEffect, useRef, useState } from "react";
import type { CameraView } from "expo-camera";

/**
 * Geste « zappe » : passer rapidement la main devant la caméra avant
 * (pas besoin de boucher l'objectif jusqu'au noir).
 *
 * Heuristique Expo Go (sans ML / MediaPipe) :
 * on mesure la taille des micro-JPEG. Un passage de main = chute brève
 * puis retour à la normale. Un maintien prolongé est ignoré.
 *
 * Une vraie tracking de main (MediaPipe) demanderait un build natif —
 * trop lourd pour Expo Go ; ce geste reste utilisable mains humides.
 */

const SAMPLE_INTERVAL_MS = 550;
const BASELINE_SAMPLES = 4;
const DIP_RATIO = 0.55; // main qui passe devant
const RECOVER_RATIO = 0.78; // main repartie
const MAX_WAVE_MS = 900; // au-delà = maintien, pas un zappe
const COOLDOWN_MS = 1400;

type Options = {
  enabled: boolean;
  cameraRef: React.RefObject<CameraView | null>;
  cameraReady: boolean;
  onTrigger: () => void;
};

export function useHandCoverGesture({ enabled, cameraRef, cameraReady, onTrigger }: Options) {
  /** 0 = idle, 0..1 pendant le passage de main, 1 = zappe détecté (flash court). */
  const [waveProgress, setWaveProgress] = useState(0);
  const baselineRef = useRef<number | null>(null);
  const baselineSamplesRef = useRef<number[]>([]);
  const dipStartedAtRef = useRef<number | null>(null);
  const cooldownUntilRef = useRef(0);
  const runningRef = useRef(false);
  const busyRef = useRef(false);
  const onTriggerRef = useRef(onTrigger);
  onTriggerRef.current = onTrigger;

  const reset = useCallback(() => {
    baselineRef.current = null;
    baselineSamplesRef.current = [];
    dipStartedAtRef.current = null;
    busyRef.current = false;
    setWaveProgress(0);
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

        const now = Date.now();
        const ratio = len / baselineRef.current;

        // Recalibre doucement quand la scène est stable
        if (ratio > 0.9 && dipStartedAtRef.current == null) {
          baselineRef.current = baselineRef.current * 0.92 + len * 0.08;
        }

        if (now < cooldownUntilRef.current) {
          busyRef.current = false;
          return;
        }

        if (dipStartedAtRef.current == null) {
          if (ratio < DIP_RATIO) {
            dipStartedAtRef.current = now;
            setWaveProgress(0.35);
          }
        } else {
          const elapsed = now - dipStartedAtRef.current;
          if (ratio >= RECOVER_RATIO && elapsed >= 80 && elapsed <= MAX_WAVE_MS) {
            // Zappe réussi : chute + retour rapide
            dipStartedAtRef.current = null;
            cooldownUntilRef.current = now + COOLDOWN_MS;
            setWaveProgress(1);
            onTriggerRef.current();
            setTimeout(() => {
              if (runningRef.current) setWaveProgress(0);
            }, 280);
          } else if (elapsed > MAX_WAVE_MS) {
            // Main restée trop longtemps → pas un zappe, on annule
            dipStartedAtRef.current = null;
            setWaveProgress(0);
          } else {
            setWaveProgress(Math.min(0.85, 0.35 + elapsed / MAX_WAVE_MS));
          }
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

  // Alias historique : les écrans lisaient `coverProgress`
  return { coverProgress: waveProgress, waveProgress };
}
