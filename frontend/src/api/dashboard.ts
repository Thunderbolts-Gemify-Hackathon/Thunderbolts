import { api } from "./http";
import { findNearbyMarket, formatAr, type MarketMatch } from "./market";
import { getPlanning, type Planning, type Repas } from "./planning";
import { getStock, type StockLine } from "./stock";

export type { MarketMatch, Planning, Repas, StockLine };
export { findNearbyMarket, formatAr, getPlanning, getStock };

export type Budget = {
  id: string;
  montant: number;
  periode: string;
  montant_restant: number;
  devise: string;
};

export function getBudget(profilId: string, token: string) {
  return api<Budget>(`/onboarding/profil/${profilId}/budget`, { token });
}
