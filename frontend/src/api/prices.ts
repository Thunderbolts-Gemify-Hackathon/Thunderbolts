import { api } from "./http";

export type PriceReport = {
  id: string;
  profil_id: string | null;
  ingredient_id: string;
  quartier: string;
  prix: number;
  unite: string;
  jour: string;
  created_at: string;
};

export type PriceIndex = {
  id: string;
  ingredient_id: string;
  quartier: string;
  jour: string;
  prix_moyen: number;
  nb_rapports: number;
};

export function createPriceReport(
  profilId: string,
  token: string,
  payload: {
    ingredient_id: string;
    quartier: string;
    prix: number;
    unite?: string;
    jour?: string;
  }
) {
  return api<PriceReport>(`/prices/${profilId}/reports`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function getPriceIndex(params: {
  quartier: string;
  ingredient_id: string;
  jour?: string;
}) {
  const q = new URLSearchParams({
    quartier: params.quartier,
    ingredient_id: params.ingredient_id,
  });
  if (params.jour) q.set("jour", params.jour);
  return api<PriceIndex[]>(`/prices/index?${q.toString()}`).then(
    (rows) => rows[0] ?? null
  );
}

export function listPriceReports(params: {
  quartier?: string;
  ingredient_id?: string;
}) {
  const q = new URLSearchParams();
  if (params.quartier) q.set("quartier", params.quartier);
  if (params.ingredient_id) q.set("ingredient_id", params.ingredient_id);
  const qs = q.toString();
  return api<PriceReport[]>(`/prices/reports${qs ? `?${qs}` : ""}`);
}
