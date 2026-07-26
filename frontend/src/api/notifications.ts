import { api } from "./http";

export type NotificationPreference = {
  id: string;
  profil_id: string;
  peremption: boolean;
  ce_soir: boolean;
  resume_dimanche: boolean;
  enabled: boolean;
};

export function getNotificationPrefs(profilId: string, token: string) {
  return api<NotificationPreference>(
    `/notifications/${profilId}/preferences`,
    { token }
  );
}

export function updateNotificationPrefs(
  profilId: string,
  token: string,
  body: Partial<{
    peremption: boolean;
    ce_soir: boolean;
    resume_dimanche: boolean;
    enabled: boolean;
  }>
) {
  return api<NotificationPreference>(
    `/notifications/${profilId}/preferences`,
    { method: "PUT", token, body }
  );
}
