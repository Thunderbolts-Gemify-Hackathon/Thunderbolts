import { Feather } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Switch, Text, View } from "react-native";

import {
  getNotificationPrefs,
  updateNotificationPrefs,
  type NotificationPreference,
} from "@/api/notifications";
import { loadAppSettings, saveAppSettings, type AppSettings } from "@/lib/appSettings";
import { scheduleFromPreferences } from "@/lib/notifications";
import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

export default function ReglagesScreen() {
  const router = useRouter();
  const { clearSession } = useSession();
  const { session } = useSession();
  const { reset } = useOnboarding();
  const [settings, setSettings] = useState<AppSettings>({
    notificationsEnabled: true,
    voiceEnabled: true,
  });
  const [prefs, setPrefs] = useState<NotificationPreference | null>(null);

  const profilId = session?.profilId;
  const token = session?.apiToken;

  useEffect(() => {
    void loadAppSettings().then(setSettings);
  }, []);

  useEffect(() => {
    if (!profilId || !token) return;
    void getNotificationPrefs(profilId, token)
      .then(async (p) => {
        setPrefs(p);
        await scheduleFromPreferences(p);
      })
      .catch(() => undefined);
  }, [profilId, token]);

  const toggle = async (key: keyof AppSettings, value: boolean) => {
    const next = await saveAppSettings({ [key]: value });
    setSettings(next);
    if (key === "notificationsEnabled" && profilId && token) {
      try {
        const p = await updateNotificationPrefs(profilId, token, {
          enabled: value,
        });
        setPrefs(p);
        await scheduleFromPreferences(p);
      } catch {
        /* ignore */
      }
    }
  };

  const togglePref = async (
    key: "peremption" | "ce_soir" | "resume_dimanche",
    value: boolean
  ) => {
    if (!profilId || !token) return;
    try {
      const p = await updateNotificationPrefs(profilId, token, { [key]: value });
      setPrefs(p);
      await scheduleFromPreferences(p);
    } catch {
      /* ignore */
    }
  };

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label="Réinitialiser l'onboarding local"
            variant="ghost"
            onPress={() => {
              reset();
              router.replace("/onboarding/profil");
            }}
          />
          <Button
            label="Se déconnecter"
            variant="ghost"
            onPress={async () => {
              reset();
              await clearSession();
              router.replace("/");
            }}
          />
        </View>
      }
    >
      <Title>Réglages</Title>
      <Body>Contrôle les alertes et l&apos;assistant vocal.</Body>

      <View style={styles.row}>
        <Feather name="bell" size={18} color={colors.ink} />
        <Text style={styles.label}>Notifications</Text>
        <Switch
          value={settings.notificationsEnabled}
          onValueChange={(v) => void toggle("notificationsEnabled", v)}
          trackColor={{ true: colors.accent, false: colors.line }}
        />
      </View>

      {prefs && settings.notificationsEnabled ? (
        <>
          <View style={styles.row}>
            <Feather name="alert-circle" size={18} color={colors.ink} />
            <Text style={styles.label}>Alertes péremption</Text>
            <Switch
              value={prefs.peremption}
              onValueChange={(v) => void togglePref("peremption", v)}
              trackColor={{ true: colors.accent, false: colors.line }}
            />
          </View>
          <View style={styles.row}>
            <Feather name="moon" size={18} color={colors.ink} />
            <Text style={styles.label}>Rappel ce soir</Text>
            <Switch
              value={prefs.ce_soir}
              onValueChange={(v) => void togglePref("ce_soir", v)}
              trackColor={{ true: colors.accent, false: colors.line }}
            />
          </View>
          <View style={styles.row}>
            <Feather name="calendar" size={18} color={colors.ink} />
            <Text style={styles.label}>Résumé dimanche</Text>
            <Switch
              value={prefs.resume_dimanche}
              onValueChange={(v) => void togglePref("resume_dimanche", v)}
              trackColor={{ true: colors.accent, false: colors.line }}
            />
          </View>
        </>
      ) : null}

      <View style={styles.row}>
        <Feather name="mic" size={18} color={colors.ink} />
        <Text style={styles.label}>Assistant vocal</Text>
        <Switch
          value={settings.voiceEnabled}
          onValueChange={(v) => void toggle("voiceEnabled", v)}
          trackColor={{ true: colors.accent, false: colors.line }}
        />
      </View>

      <Pressable style={styles.row} onPress={() => router.push("/profil")}>
        <Feather name="user" size={18} color={colors.ink} />
        <Text style={styles.label}>Modifier mon profil</Text>
        <Feather name="chevron-right" size={18} color={colors.muted} />
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  actions: { gap: space.sm },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.sm,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    paddingHorizontal: space.md,
    paddingVertical: space.md,
    marginTop: space.sm,
  },
  label: { fontSize: type.body, color: colors.ink, flex: 1, fontWeight: "600" },
});
