import { api } from "./http";

export type AntiGaspi = {
  ariary_sauves: number;
  items_sauves: number;
  streak_jours: number;
  message: string;
};

export function getAntiGaspi(profilId: string, token: string) {
  return api<AntiGaspi>(`/ia/${profilId}/anti-gaspi`, { token });
}
