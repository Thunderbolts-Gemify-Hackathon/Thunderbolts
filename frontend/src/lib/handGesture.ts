import { useCallback, useEffect, useRef, useState } from "react";
import type { CameraView } from "expo-camera";

/**
 * Détection "main devant l'objectif" en mode mains libres, sans dépendance native
 * supplémentaire (pas de vision-camera / frame processors — resterait compatible
 * Expo Go). Heuristique : on capture régulièrement une image minuscule et on
 * compare sa taille JPEG à une taille de référence ("à vide"). Une main qui
 * recouvre l'objectif donne une image quasi uniforme et sombre → beaucoup moins
 * de détails à compresser → un JPEG nettement plus petit que la référence.
 * Ce n'est pas une vraie mesure de luminosité pixel par pixel, mais c'est fiable
 * en pratique, léger, et ne nécessite aucune librairie de décodage d'image.
 */

const SAMPLE_INTERVAL_MS = 350;
const HOLD_MS = 900;
const COVER_RATIO = 0.4; // taille JPEG < 40% de la référence ⇒ objectif couvert
const RELEASE_RATIO = 0.65; // il faut redépasser ce seuil pour pouvoir re-déclencher
const BASELINE_SAMPLES = 3;

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
  const armedRef = useRef(true); // false pendant que l'objectif reste couvert après un déclenchement
  const runningRef = useRef(false);

  const reset = useCallback(() => {
    baselineRef.current = null;
    baselineSamplesRef.current = [];
    coveredSinceRef.current = null;
    armedRef.current = true;
    setCoverProgress(0);
  }, []);

  useEffect(() => {
    if (!enabled || !cameraReady) {
      reset();
      return;
    }

    runningRef.current = true;
    const interval = setInterval(async () => {
      if (!runningRef.current || !cameraRef.current) return;
      let len = 0;
      try {
        const photo = await cameraRef.current.takePictureAsync({
          base64: true,
          quality: 0.1,
          skipProcessing: true,
          shutterSound: false,
        });
        len = photo?.base64?.length ?? 0;
      } catch {
        return; // capture ratée : on ignore cet échantillon, pas grave
      }
      if (!len || !runningRef.current) return;

      if (baselineRef.current == null) {
        baselineSamplesRef.current.push(len);
        if (baselineSamplesRef.current.length >= BASELINE_SAMPLES) {
          const sorted = [...baselineSamplesRef.current].sort((a, b) => a - b);
          baselineRef.current = sorted[Math.floor(sorted.length / 2)];
        }
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
        setCoverProgress(Math.min(1, held / HOLD_MS));
        if (held >= HOLD_MS) {
          armedRef.current = false;
          coveredSinceRef.current = null;
          setCoverProgress(0);
          onTrigger();
        }
      } else {
        coveredSinceRef.current = null;
        setCoverProgress(0);
      }

      // Réajuste doucement la référence quand l'objectif est bien dégagé, pour
      // absorber les changements de luminosité ambiante au fil de la recette.
      if (ratio > 0.9) {
        baselineRef.current = baselineRef.current * 0.85 + len * 0.15;
      }
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
