import { api } from "./http";

export type PanierItem = {
  ingredient_nom: string;
  quantite: number;
  unite?: string;
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
}) {
  return api<PanierCheckResult>("/market/panier-check", {
    method: "POST",
    body: payload,
  });
}
