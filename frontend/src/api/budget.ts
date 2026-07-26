import { api } from "./http";

export type Depense = {
  id: string;
  profil_id: string;
  montant: number;
  source: string;
  label: string | null;
  created_at: string;
};

export type BudgetSummary = {
  montant: number;
  montant_restant: number;
  periode: string;
  devise: string;
  pourcent_consomme: number;
  recentes: Depense[];
};

export function getBudgetSummary(profilId: string, token: string) {
  return api<BudgetSummary>(`/budget/${profilId}/summary`, { token });
}

export function getBudgetHistorique(profilId: string, token: string) {
  return api<Depense[]>(`/budget/${profilId}/historique`, { token });
}

export function createDepense(
  profilId: string,
  payload: { montant: number; source?: string; label?: string },
  token: string
) {
  return api<Depense>(`/budget/${profilId}/depense`, {
    method: "POST",
    body: payload,
    token,
  });
}
