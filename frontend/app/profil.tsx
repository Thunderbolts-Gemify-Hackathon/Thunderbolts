import { Feather } from "@expo/vector-icons";
import { type Href, useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { ApiError } from "@/api/http";
import { getMonProfilComplet, type ProfilCompletOut } from "@/api/onboarding";
import { hydrationFromComplet } from "@/onboarding/hydrate";
import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

type Row = { label: string; value: string; href: Href };

export default function ProfilScreen() {
  const router = useRouter();
  const { session, clearSession, patchSession } = useSession();
  const { reset, hydrate } = useOnboarding();
  const [complet, setComplet] = useState<ProfilCompletOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!session?.apiToken) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getMonProfilComplet(session.apiToken);
      setComplet(data);
      const h = hydrationFromComplet(data);
      hydrate(h.data, h.done, h.resumeStep);
      await patchSession(h.sessionPatch);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Impossible de charger le profil.");
    } finally {
      setLoading(false);
    }
  }, [session?.apiToken, hydrate, patchSession]);

  useFocusEffect(
    useCallback(() => {
      void reload();
    }, [reload])
  );

  const initiale = (session?.prenom?.[0] ?? "?").toUpperCase();
  const rows: Row[] = [];
  if (complet?.profil) {
    rows.push({
      label: "Profil sante",
      value: `${complet.profil.poids} kg · ${complet.profil.objectif.replace("_", " ")}`,
      href: "/edit/profil" as Href,
    });
  }
  if (complet?.foyer) {
    rows.push({
      label: "Foyer",
      value: `${complet.foyer.nombre_personnes} personne(s)`,
      href: "/edit/foyer" as Href,
    });
  }
  if (complet?.preferences) {
    const n =
      complet.preferences.allergies.length + complet.preferences.tabous.length;
    rows.push({
      label: "Gouts & limites",
      value: n ? `${n} contrainte(s)` : "Aucune contrainte",
      href: "/edit/preferences" as Href,
    });
  }
  if (complet?.budget) {
    rows.push({
      label: "Budget",
      value: `${Math.round(complet.budget.montant_restant)} / ${Math.round(complet.budget.montant)} Ar`,
      href: "/edit/budget" as Href,
    });
  }
  if (complet?.localisation) {
    rows.push({
      label: "Quartier",
      value: complet.localisation.quartier || "Position GPS",
      href: "/edit/localisation" as Href,
    });
  }

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label="Regenerer le planning"
            onPress={() => router.push("/planning" as Href)}
          />
          <Button
            label="Se deconnecter"
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
      <Body>Modifie tes infos pour des repas toujours adaptes.</Body>

      <View style={styles.avatarRow}>
        <View style={styles.avatar}>
          <Text style={styles.avatarLabel}>{initiale}</Text>
        </View>
        <View style={styles.identity}>
          <Text style={styles.name}>{session?.prenom || "Utilisateur"}</Text>
          <Text style={styles.email}>{session?.email || "-"}</Text>
        </View>
      </View>

      {loading ? <ActivityIndicator color={colors.accent} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {rows.map((row) => (
        <Pressable
          key={String(row.href)}
          style={styles.card}
          onPress={() => router.push(row.href)}
        >
          <View style={styles.cardText}>
            <Text style={styles.rowLabel}>{row.label}</Text>
            <Text style={styles.rowValue}>{row.value}</Text>
          </View>
          <Feather name="chevron-right" size={18} color={colors.muted} />
        </Pressable>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  actions: { gap: space.sm },
  avatarRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.md,
    marginTop: space.md,
    marginBottom: space.lg,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.brandSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarLabel: { fontSize: 22, fontWeight: "700", color: colors.accent },
  identity: { flex: 1, gap: 2 },
  name: { fontSize: 20, fontWeight: "700", color: colors.ink },
  email: { fontSize: type.body, color: colors.muted },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.sm,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.md,
    marginBottom: space.sm,
  },
  cardText: { flex: 1, gap: 2 },
  rowLabel: { fontSize: type.small, color: colors.muted },
  rowValue: { fontSize: type.body, color: colors.ink, fontWeight: "600" },
  error: { fontSize: type.body, color: colors.danger, marginBottom: space.sm },
});
