import { api } from "./http";

export type NotificationPreference = {
  id: string;
  profil_id: string;
  peremption: boolean;
  ce_soir: boolean;
  resume_dimanche: boolean;
  enabled: boolean;
};

export type NotificationPreviewItem = {
  kind: string;
  title: string;
  body: string;
  hour: number;
  minute: number;
  weekday?: number;
};

export type NotificationPreview = {
  profil_id: string;
  enabled: boolean;
  notifications: NotificationPreviewItem[];
};

export function getNotificationPrefs(profilId: string, token: string) {
  return api<NotificationPreference>(
    `/notifications/${profilId}/preferences`,
    { token }
  );
}

export function getNotificationPreview(profilId: string, token: string) {
  return api<NotificationPreview>(`/notifications/${profilId}/preview`, {
    token,
  });
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
