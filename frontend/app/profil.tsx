import { useRouter } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

export default function ProfilScreen() {
  const router = useRouter();
  const { session, clearSession } = useSession();
  const { reset } = useOnboarding();

  const initiale = (session?.prenom?.[0] ?? "?").toUpperCase();

  return (
    <Screen
      footer={
        <View style={styles.actions}>
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
      <Title>Mon profil</Title>
      <Body>Tes informations personnelles.</Body>

      <View style={styles.avatarRow}>
        <View style={styles.avatar}>
          <Text style={styles.avatarLabel}>{initiale}</Text>
        </View>
        <View style={styles.identity}>
          <Text style={styles.name}>{session?.prenom || "Utilisateur"}</Text>
          <Text style={styles.email}>{session?.email || "—"}</Text>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.rowLabel}>Nom</Text>
        <Text style={styles.rowValue}>{session?.prenom || "—"}</Text>
      </View>
      <View style={styles.card}>
        <Text style={styles.rowLabel}>Email</Text>
        <Text style={styles.rowValue}>{session?.email || "—"}</Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  actions: { gap: space.sm },
  avatarRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.md,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: colors.brandSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarLabel: { fontSize: 24, fontWeight: "700", color: colors.brand },
  identity: { gap: 2 },
  name: { fontSize: type.title, fontWeight: "700", color: colors.ink },
  email: { fontSize: type.body, color: colors.muted },
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.md,
    gap: 4,
  },
  rowLabel: {
    fontSize: type.label,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
    letterSpacing: 0.3,
  },
  rowValue: { fontSize: type.body, color: colors.ink, fontWeight: "600" },
});
