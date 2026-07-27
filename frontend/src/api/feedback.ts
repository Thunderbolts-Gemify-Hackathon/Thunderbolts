import { api } from "./http";

export type RepasFeedback = {
  id: string;
  profil_id: string;
  recette_id: string;
  note: number;
  commentaire: string | null;
  created_at: string;
};

export function postRepasFeedback(
  profilId: string,
  token: string,
  payload: { recette_id: string; note: -1 | 1; commentaire?: string }
) {
  return api<RepasFeedback>(`/ia/${profilId}/feedback`, {
    method: "POST",
    token,
    body: payload,
  });
}
