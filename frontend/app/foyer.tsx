import { type Href, useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  Share,
  StyleSheet,
  Text,
  View,
} from "react-native";

import {
  inviteFoyerMembre,
  listFoyerMembres,
  listMyFoyers,
  type FoyerMembreLien,
  type FoyerMine,
} from "@/api/foyer";
import { ApiError } from "@/api/http";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

export default function FoyerScreen() {
  const router = useRouter();
  const { session, patchSession } = useSession();
  const profilId = session?.profilId;
  const token = session?.apiToken;
  const activeProfilId = session?.sharedProfilId || session?.profilId;
  const [membres, setMembres] = useState<FoyerMembreLien[]>([]);
  const [foyers, setFoyers] = useState<FoyerMine[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviting, setInviting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastInviteUrl, setLastInviteUrl] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) {
      setError("Session incomplete.");
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const shared = await listMyFoyers(token);
      setFoyers(shared);
      let rows: FoyerMembreLien[] = [];
      if (profilId) {
        try {
          rows = await listFoyerMembres(profilId, token);
        } catch {
          rows = [];
        }
      }
      setMembres(rows);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Chargement impossible");
    } finally {
      setLoading(false);
    }
  }, [profilId, token]);

  useEffect(() => {
    void load();
  }, [load]);

  const switchSharedProfil = async (sharedId: string) => {
    await patchSession({ sharedProfilId: sharedId });
  };

  const invite = async () => {
    if (!profilId || !token) return;
    setInviting(true);
    setError(null);
    try {
      const out = await inviteFoyerMembre(profilId, token, { role: "membre" });
      setLastInviteUrl(out.invite_url);
      await load();
      try {
        await Share.share({
          message: `Rejoins mon foyer KaliTao : ${out.invite_url}`,
        });
      } catch {
        /* ignore share cancel */
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Invitation impossible");
    } finally {
      setInviting(false);
    }
  };

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label={inviting ? "Creation…" : "Inviter un coloc"}
            onPress={() => void invite()}
            disabled={inviting || !profilId}
          />
          <Button label="Retour" variant="ghost" onPress={() => router.back()} />
        </View>
      }
    >
      <Title>Coloc / foyer</Title>
      <Body>Partage le foyer : invite un membre avec un lien.</Body>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Text style={styles.section}>Stock / budget partagés</Text>
      {foyers.length === 0 ? (
        <Body>Aucun foyer lié. Accepte une invitation ou crée la tienne.</Body>
      ) : (
        foyers.map((f) => {
          const active = f.profil_id === activeProfilId;
          return (
            <Pressable
              key={f.foyer_id}
              onPress={() => void switchSharedProfil(f.profil_id)}
              style={[styles.card, active && styles.cardActive]}
            >
              <Text style={styles.nom}>
                {f.role === "owner" ? "Mon foyer" : "Foyer partagé"} · {f.role}
              </Text>
              <Text style={styles.meta}>
                profil {f.profil_id.slice(0, 8)}…
                {active ? " · actif" : " · appuyer pour basculer"}
              </Text>
            </Pressable>
          );
        })
      )}

      {lastInviteUrl ? (
        <View style={styles.card}>
          <Text style={styles.label}>Dernier lien</Text>
          <Text style={styles.url}>{lastInviteUrl}</Text>
          <Pressable
            onPress={() => {
              try {
                void Share.share({ message: lastInviteUrl });
              } catch {
                Alert.alert("Lien", lastInviteUrl);
              }
            }}
          >
            <Text style={styles.link}>Partager à nouveau</Text>
          </Pressable>
        </View>
      ) : null}

      <Text style={styles.section}>Membres</Text>
      {membres.length === 0 ? (
        <Body>Aucun membre lié pour l'instant (crée une invitation).</Body>
      ) : (
        membres.map((m) => (
          <View key={m.id} style={styles.card}>
            <Text style={styles.nom}>
              {m.role}
              {m.utilisateur_id ? "" : " (en attente)"}
            </Text>
            <Text style={styles.meta}>
              {m.utilisateur_id
                ? `user ${m.utilisateur_id.slice(0, 8)}…`
                : m.invite_token
                  ? `token ${m.invite_token.slice(0, 8)}…`
                  : "—"}
            </Text>
          </View>
        ))
      )}

      <Button
        label="J'ai un lien d'invitation"
        variant="ghost"
        onPress={() => router.push("/foyer/accept" as Href)}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  actions: { gap: space.sm },
  section: {
    marginTop: space.md,
    fontSize: type.label,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
  },
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.md,
    gap: 4,
    marginTop: space.sm,
  },
  cardActive: {
    borderColor: colors.brand,
    backgroundColor: colors.brandSoft,
  },
  label: { fontSize: type.small, color: colors.muted, fontWeight: "700" },
  url: { fontSize: type.small, color: colors.ink },
  link: { color: colors.accent, fontWeight: "700", marginTop: 4 },
  nom: { fontSize: type.body, fontWeight: "700", color: colors.ink },
  meta: { fontSize: type.small, color: colors.muted },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
});
