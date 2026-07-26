/**
 * Estimation de durée de trajet à partir de la distance réelle (itinéraire)
 * et du mode de déplacement seedé. Ce n'est pas un temps réel (pas de trafic,
 * pas de GPS live) : on l'affiche toujours comme une estimation, jamais
 * comme une donnée mesurée.
 */
const VITESSE_KMH: Record<string, number> = {
  pied: 4.5,
  moto: 25,
  taxi: 18, // circulation urbaine à Tana, pas une autoroute
};

const MODE_LABEL: Record<string, string> = {
  pied: "à pied",
  moto: "en moto",
  taxi: "en taxi",
};

export function estimateMinutes(distanceKm: number, mode: string): number {
  const vitesse = VITESSE_KMH[mode] ?? VITESSE_KMH.pied;
  return Math.max(1, Math.round((distanceKm / vitesse) * 60));
}

export function formatTrajet(distanceKm: number, mode: string): string {
  const minutes = estimateMinutes(distanceKm, mode);
  const label = MODE_LABEL[mode] ?? mode;
  return `${distanceKm} km ${label} · ≈ ${minutes} min (estimation)`;
}
