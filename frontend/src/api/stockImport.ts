import { api } from "./http";
import type { IngredientStockOut } from "./stockAlerts";

export type StockImportLine = {
  label: string;
  quantite: number;
  unite: string;
  ingredient_id: string | null;
  matched: boolean;
};

export type StockImportResult = {
  lines: StockImportLine[];
  applied: number;
};

export function importStockText(
  profilId: string,
  token: string,
  payload: { text: string; apply: boolean }
) {
  return api<StockImportResult>(`/stock/${profilId}/import-text`, {
    method: "POST",
    token,
    body: payload,
  });
}

export type { IngredientStockOut };
