import { api } from "./http";

export type MarketMatch = {
  point_de_vente: {
    id: string;
    nom: string;
    type: string;
    latitude: number;
    longitude: number;
  };
  prix: number;
  itineraire: {
    distance: number;
    niveau_securite: string;
    mode_deplacement: string;
  } | null;
  deprioritise: boolean;
  prix_crowd?: number | null;
  ecart_crowd_pct?: number | null;
};

export function findNearbyMarket(
  ingredientId: string,
  lat: number,
  lon: number,
  rayonKm = 15
) {
  const q = new URLSearchParams({
    ingredient_id: ingredientId,
    lat: String(lat),
    lon: String(lon),
    rayon_km: String(rayonKm),
  });
  return api<MarketMatch[]>(`/market/nearby?${q}`);
}

export function formatAr(n: number, devise = "Ar"): string {
  return `${Math.round(n).toLocaleString("fr-FR")} ${devise}`;
}

/** Premier match non deprioritise (deja trie prix + securite cote API). */
export function pickSafest(matches: MarketMatch[]): MarketMatch | null {
  if (matches.length === 0) return null;
  return matches.find((m) => !m.deprioritise) ?? matches[0];
}
