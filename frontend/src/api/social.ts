import { api } from "./http";

export type DefiProgress = {
  valeur: number;
  objectif: number;
  atteint: boolean;
};

export type Defi = {
  id: string;
  titre: string;
  description: string;
  type: string;
  objectif: number;
  unite: string;
  progress?: DefiProgress | null;
};

export function listDefis(profilId?: string | null, token?: string | null) {
  const q = profilId ? `?profil_id=${encodeURIComponent(profilId)}` : "";
  return api<Defi[]>(`/social/defis${q}`, { token });
}

export function postDefiProgress(
  profilId: string,
  defiId: string,
  token: string,
  increment = 1
) {
  return api<{
    defi_id: string;
    valeur: number;
    objectif: number;
    atteint: boolean;
  }>(`/social/${profilId}/defis/${encodeURIComponent(defiId)}/progress`, {
    method: "POST",
    token,
    body: { increment },
  });
}
