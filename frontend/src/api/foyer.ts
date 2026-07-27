import { api } from "./http";

export type FoyerMembreLien = {
  id: string;
  utilisateur_id: string | null;
  foyer_id: string;
  role: string;
  invite_token: string | null;
  created_at: string;
};

export type FoyerInvite = {
  lien: FoyerMembreLien;
  invite_url: string;
};

export function listFoyerMembres(profilId: string, token: string) {
  return api<FoyerMembreLien[]>(`/foyer/${profilId}/membres`, { token });
}

export function inviteFoyerMembre(
  profilId: string,
  token: string,
  payload?: { email?: string; role?: string }
) {
  return api<FoyerInvite>(`/foyer/${profilId}/invite`, {
    method: "POST",
    token,
    body: payload ?? { role: "membre" },
  });
}

export function acceptFoyerInvite(token: string, inviteToken: string) {
  return api<FoyerMembreLien>(`/foyer/invite/${inviteToken}/accept`, {
    method: "POST",
    token,
  });
}

export type FoyerMine = {
  foyer_id: string;
  profil_id: string;
  role: string;
  partage_stock: boolean;
  partage_budget: boolean;
};

/** Foyers accessibles (owner + membre) avec profil_id partagé stock/budget. */
export function listMyFoyers(token: string) {
  return api<FoyerMine[]>("/foyer/mine", { token });
}
