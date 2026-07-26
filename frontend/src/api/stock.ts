import { api } from "./http";

export type Unite = "g" | "ml" | "kg" | "l" | "unite";

export type CategorieIngredient =
  | "féculent"
  | "protéine"
  | "légume"
  | "épice"
  | "condiment"
  | "autre";

export type Ingredient = {
  id: string;
  nom: string;
  unite_defaut: string;
  categorie?: string;
  conservation_jours?: number | null;
};

export type IngredientCreate = {
  nom: string;
  unite_defaut: Unite;
  categorie?: CategorieIngredient;
  conservation_jours?: number | null;
};

export type StockLine = {
  id: string;
  stock_id: string;
  ingredient_id: string;
  quantite_disponible: number;
  unite: string;
  date_peremption: string | null;
};

export type StockUpsert = {
  ingredient_id: string;
  quantite_disponible: number;
  unite: Unite;
  date_peremption?: string | null;
};

export function listIngredients(token: string) {
  return api<Ingredient[]>("/ingredients", { token });
}

export function createIngredient(payload: IngredientCreate, token: string) {
  return api<Ingredient>("/ingredients", { method: "POST", body: payload, token });
}

export function getStock(profilId: string, token: string) {
  return api<StockLine[]>(`/stock/${profilId}`, { token });
}

export function upsertStockLine(profilId: string, payload: StockUpsert, token: string) {
  return api<StockLine>(`/stock/${profilId}/ingredients`, {
    method: "POST",
    body: payload,
    token,
  });
}

export function deleteStockLine(profilId: string, ingredientId: string, token: string) {
  return api<void>(`/stock/${profilId}/ingredients/${ingredientId}`, {
    method: "DELETE",
    token,
  });
}

export function nameById(catalog: Ingredient[]): Record<string, Ingredient> {
  return Object.fromEntries(catalog.map((i) => [i.id, i]));
}
