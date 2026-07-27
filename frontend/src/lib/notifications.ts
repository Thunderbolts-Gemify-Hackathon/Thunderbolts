/**
 * Planification locale des notifications selon les préférences serveur.
 * Si expo-notifications n'est pas installé / indisponible, no-op sûr.
 */
import { Platform } from "react-native";

import {
  getNotificationPreview,
  type NotificationPreference,
  type NotificationPreviewItem,
} from "@/api/notifications";

type Scheduler = {
  schedule: (prefs: NotificationPreference) => Promise<void>;
  cancelAll: () => Promise<void>;
};

let Notifications: {
  requestPermissionsAsync?: () => Promise<{ status: string }>;
  setNotificationHandler?: (handler: unknown) => void;
  cancelAllScheduledNotificationsAsync?: () => Promise<void>;
  scheduleNotificationAsync?: (req: unknown) => Promise<string>;
} | null = null;

try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  Notifications = require("expo-notifications");
  Notifications?.setNotificationHandler?.({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: false,
      shouldSetBadge: false,
      shouldShowBanner: true,
      shouldShowList: true,
    }),
  });
} catch {
  Notifications = null;
}

async function ensurePermission(): Promise<boolean> {
  if (!Notifications?.requestPermissionsAsync) return false;
  if (Platform.OS === "web") return false;
  try {
    const { status } = await Notifications.requestPermissionsAsync();
    return status === "granted";
  } catch {
    return false;
  }
}

export async function cancelAllLocalNotifications() {
  try {
    await Notifications?.cancelAllScheduledNotificationsAsync?.();
  } catch {
    /* no-op */
  }
}

async function scheduleOne(item: NotificationPreviewItem) {
  if (!Notifications?.scheduleNotificationAsync) return;
  try {
    if (item.weekday != null) {
      await Notifications.scheduleNotificationAsync({
        content: { title: item.title, body: item.body },
        trigger: {
          type: "weekly",
          weekday: item.weekday,
          hour: item.hour,
          minute: item.minute,
        },
      });
    } else {
      await Notifications.scheduleNotificationAsync({
        content: { title: item.title, body: item.body },
        trigger: {
          type: "daily",
          hour: item.hour,
          minute: item.minute,
        },
      });
    }
  } catch {
    /* trigger API varie selon version — ignore */
  }
}

export async function scheduleFromPreferences(prefs: NotificationPreference) {
  await cancelAllLocalNotifications();
  if (!prefs.enabled || !Notifications?.scheduleNotificationAsync) return;
  const ok = await ensurePermission();
  if (!ok) return;

  if (prefs.ce_soir) {
    await scheduleOne({
      kind: "ce_soir",
      title: "Ce soir sur KaliTao",
      body: "Une idée de repas t'attend sur le tableau de bord.",
      hour: 17,
      minute: 30,
    });
  }
  if (prefs.peremption) {
    await scheduleOne({
      kind: "peremption",
      title: "Péremption",
      body: "Vérifie les produits qui approchent de la date limite.",
      hour: 9,
      minute: 0,
    });
  }
  if (prefs.resume_dimanche) {
    await scheduleOne({
      kind: "resume_dimanche",
      title: "Résumé dimanche",
      body: "Budget, stock et anti-gaspi de la semaine.",
      hour: 10,
      minute: 0,
      weekday: 1,
    });
  }
}

/** Récupère le preview serveur (noms d'items + ce soir) puis planifie. */
export async function scheduleContextualNotifications(
  profilId: string,
  token: string
) {
  await cancelAllLocalNotifications();
  if (!Notifications?.scheduleNotificationAsync) return;
  const ok = await ensurePermission();
  if (!ok) return;
  try {
    const preview = await getNotificationPreview(profilId, token);
    if (!preview.enabled) return;
    for (const item of preview.notifications) {
      await scheduleOne(item);
    }
  } catch {
    /* ignore réseau */
  }
}

export const notificationScheduler: Scheduler = {
  schedule: scheduleFromPreferences,
  cancelAll: cancelAllLocalNotifications,
};
