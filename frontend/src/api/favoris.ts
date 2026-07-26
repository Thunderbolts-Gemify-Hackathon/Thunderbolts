import { api } from "./http";

export type FavoriToggle = { favori: boolean; recette_id: string };

export function listFavoris(profilId: string, token: string) {
  return api<{ id: string; profil_id: string; recette_id: string }[]>(
    `/favoris/${profilId}`,
    { token }
  );
}

export function toggleFavori(
  profilId: string,
  token: string,
  recetteId: string
) {
  return api<FavoriToggle>(`/favoris/${profilId}/${recetteId}`, {
    method: "POST",
    token,
  });
}

export function getFavori(profilId: string, token: string, recetteId: string) {
  return api<FavoriToggle>(`/favoris/${profilId}/${recetteId}`, { token });
}
