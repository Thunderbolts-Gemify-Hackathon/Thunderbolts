import { api } from "./http";

export type IngredientStockOut = {
  id: string;
  stock_id: string;
  ingredient_id: string;
  quantite_disponible: number;
  unite: string;
  date_peremption: string | null;
};

export function getAlertesPeremption(profilId: string, token: string, jours = 7) {
  return api<IngredientStockOut[]>(
    `/stock/${profilId}/alertes/peremption?jours=${jours}`,
    { token }
  );
}

export function approvisionnerStock(
  profilId: string,
  payload: {
    items: { ingredient_id: string; quantite: number; unite?: string; prix?: number }[];
    label?: string;
  },
  token: string
) {
  return api<{
    stock: IngredientStockOut[];
    depense: { id: string; montant: number } | null;
    montant_restant: number;
  }>(`/stock/${profilId}/approvisionner`, {
    method: "POST",
    body: payload,
    token,
  });
}
