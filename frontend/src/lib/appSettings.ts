import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "kalitao.appSettings.v1";

export type AppSettings = {
  notificationsEnabled: boolean;
  voiceEnabled: boolean;
};

const DEFAULTS: AppSettings = {
  notificationsEnabled: true,
  voiceEnabled: true,
};

export async function loadAppSettings(): Promise<AppSettings> {
  try {
    const raw = await AsyncStorage.getItem(KEY);
    if (!raw) return { ...DEFAULTS };
    return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULTS };
  }
}

export async function saveAppSettings(patch: Partial<AppSettings>): Promise<AppSettings> {
  const current = await loadAppSettings();
  const next = { ...current, ...patch };
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}
