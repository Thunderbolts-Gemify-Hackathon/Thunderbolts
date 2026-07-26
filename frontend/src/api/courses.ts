import { api } from "./http";

export type ListeCourseItem = {
  id: string;
  profil_id: string;
  ingredient_id: string | null;
  label: string;
  quantite: number;
  unite: string;
  prix_estime: number | null;
  coche: boolean;
  custom: boolean;
  done: boolean;
};

export function listCourseItems(
  profilId: string,
  token: string,
  includeDone = false
) {
  const q = includeDone ? "?include_done=true" : "";
  return api<ListeCourseItem[]>(`/planning/${profilId}/courses/items${q}`, {
    token,
  });
}

export function createCourseItem(
  profilId: string,
  token: string,
  body: {
    label: string;
    ingredient_id?: string | null;
    quantite?: number;
    unite?: string;
    prix_estime?: number | null;
    custom?: boolean;
  }
) {
  return api<ListeCourseItem>(`/planning/${profilId}/courses/items`, {
    method: "POST",
    token,
    body,
  });
}

export function updateCourseItem(
  profilId: string,
  token: string,
  itemId: string,
  body: Partial<{
    label: string;
    quantite: number;
    unite: string;
    prix_estime: number | null;
    coche: boolean;
  }>
) {
  return api<ListeCourseItem>(
    `/planning/${profilId}/courses/items/${itemId}`,
    { method: "PATCH", token, body }
  );
}

export function deleteCourseItem(
  profilId: string,
  token: string,
  itemId: string
) {
  return api<void>(`/planning/${profilId}/courses/items/${itemId}`, {
    method: "DELETE",
    token,
  });
}

export function terminerCourses(
  profilId: string,
  token: string,
  itemIds: string[],
  label = "Courses"
) {
  return api<{
    items_termines: number;
    stock_approvisionne: number;
    montant_restant: number;
  }>(`/planning/${profilId}/courses/terminer`, {
    method: "POST",
    token,
    body: { item_ids: itemIds, label },
  });
}
