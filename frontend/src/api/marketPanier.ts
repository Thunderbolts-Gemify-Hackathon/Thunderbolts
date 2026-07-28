import { api } from "./http";

export type PanierItem = {
  ingredient_nom: string;
  quantite: number;
  unite?: string;
  ingredient_id?: string;
};

export type PanierSwapSuggestion = {
  ingredient_nom: string;
  alternative: string;
  economie_estimee: number;
  raison: string;
};

export type PanierCheckResult = {
  cout_estime: number;
  budget: number;
  ecart: number;
  statut: "sous_budget" | "au_budget" | "over_budget";
  swaps: PanierSwapSuggestion[];
};

export function checkPanier(payload: {
  items: PanierItem[];
  budget: number;
  quartier?: string | null;
  lat?: number | null;
  lon?: number | null;
}) {
  return api<PanierCheckResult>("/market/panier-check", {
    method: "POST",
    body: payload,
  });
}

export type OneTripStop = {
  point_de_vente: {
    id: string;
    nom: string;
    type: string;
    latitude: number;
    longitude: number;
  };
  distance_km: number;
  cout_estime: number;
  items: {
    ingredient_id: string;
    ingredient_nom: string;
    quantite: number;
    unite: string;
    prix_unitaire: number;
    cout_estime: number;
  }[];
};

export type OneTripResult = {
  nb_arrets: number;
  distance_totale_km: number;
  cout_estime: number;
  budget?: number | null;
  ecart?: number | null;
  statut: string;
  stops: OneTripStop[];
  manquants: { ingredient_id: string; ingredient_nom: string; raison: string }[];
  message: string;
};

export function planOneTrip(payload: {
  items: PanierItem[];
  lat: number;
  lon: number;
  rayon_km?: number;
  budget?: number;
  profil_id?: string;
}) {
  return api<OneTripResult>("/market/one-trip", {
    method: "POST",
    body: payload,
  });
}
