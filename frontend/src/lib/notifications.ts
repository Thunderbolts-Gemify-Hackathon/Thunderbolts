/**
 * Planification locale des notifications selon les préférences serveur.
 * Si expo-notifications n'est pas installé / indisponible, no-op sûr.
 */
import { Platform } from "react-native";

import type { NotificationPreference } from "@/api/notifications";

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

export async function scheduleFromPreferences(prefs: NotificationPreference) {
  await cancelAllLocalNotifications();
  if (!prefs.enabled || !Notifications?.scheduleNotificationAsync) return;
  const ok = await ensurePermission();
  if (!ok) return;

  const schedule = async (title: string, body: string, hour: number, minute: number) => {
    try {
      await Notifications!.scheduleNotificationAsync!({
        content: { title, body },
        trigger: {
          type: "daily",
          hour,
          minute,
        },
      });
    } catch {
      /* trigger API varie selon version — ignore */
    }
  };

  if (prefs.ce_soir) {
    await schedule(
      "Ce soir sur KaliTao",
      "Une idée de repas t'attend sur le tableau de bord.",
      17,
      30
    );
  }
  if (prefs.peremption) {
    await schedule(
      "Péremption",
      "Vérifie les produits qui approchent de la date limite.",
      9,
      0
    );
  }
  if (prefs.resume_dimanche) {
    try {
      await Notifications!.scheduleNotificationAsync!({
        content: {
          title: "Résumé dimanche",
          body: "Budget, stock et anti-gaspi de la semaine.",
        },
        trigger: {
          type: "weekly",
          weekday: 1,
          hour: 10,
          minute: 0,
        },
      });
    } catch {
      /* no-op */
    }
  }
}

export const notificationScheduler: Scheduler = {
  schedule: scheduleFromPreferences,
  cancelAll: cancelAllLocalNotifications,
};
