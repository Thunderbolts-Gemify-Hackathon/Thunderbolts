import { type Href, useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { ApiError } from "@/api/http";
import { listDefis, type Defi } from "@/api/social";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

function progressPct(d: Defi): number {
  const p = d.progress;
  if (!p || !p.objectif) return 0;
  return Math.min(100, Math.round((p.valeur / p.objectif) * 100));
}

export default function DefisScreen() {
  const router = useRouter();
  const { session } = useSession();
  const profilId = session?.profilId;
  const token = session?.apiToken;
  const [defis, setDefis] = useState<Defi[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDefis(await listDefis(profilId, token));
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Défis indisponibles");
    } finally {
      setLoading(false);
    }
  }, [profilId, token]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <Screen
      footer={
        <View style={styles.footer}>
          <Button label="Actualiser" onPress={() => void load()} disabled={loading} />
          <Button label="Retour" variant="ghost" onPress={() => router.back()} />
        </View>
      }
    >
      <Title>Défis foyer</Title>
      <Body>
        Budget, anti-gaspi et repas maison — ta progression se met à jour quand tu
        cuisines et gères ton stock.
      </Body>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {defis.map((d) => {
        const pct = progressPct(d);
        const atteint = d.progress?.atteint;
        return (
          <View key={d.id} style={[styles.card, atteint && styles.cardDone]}>
            <Text style={styles.titre}>{d.titre}</Text>
            <Text style={styles.desc}>{d.description}</Text>
            <View style={styles.barTrack}>
              <View style={[styles.barFill, { width: `${pct}%` }]} />
            </View>
            <Text style={styles.meta}>
              {d.progress
                ? `${d.progress.valeur} / ${d.objectif} ${d.unite}`
                : `Objectif : ${d.objectif} ${d.unite}`}
              {atteint ? " · Réussi" : ""}
            </Text>
            {d.id === "anti-gaspi-3j" ? (
              <Pressable onPress={() => router.push("/stock" as Href)}>
                <Text style={styles.link}>Voir le stock →</Text>
              </Pressable>
            ) : null}
            {d.id === "fait-maison" ? (
              <Pressable onPress={() => router.push("/planning" as Href)}>
                <Text style={styles.link}>Cuisiner un repas →</Text>
              </Pressable>
            ) : null}
            {d.id === "budget-semaine" ? (
              <Pressable onPress={() => router.push("/courses" as Href)}>
                <Text style={styles.link}>Liste de courses →</Text>
              </Pressable>
            ) : null}
          </View>
        );
      })}
    </Screen>
  );
}

const styles = StyleSheet.create({
  footer: { gap: space.sm },
  error: { color: colors.danger, fontWeight: "600", marginTop: space.sm },
  card: {
    marginTop: space.md,
    padding: space.md,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    gap: space.xs,
  },
  cardDone: { borderWidth: 1.5, borderColor: colors.ok },
  titre: { fontSize: type.body, fontWeight: "700", color: colors.ink },
  desc: { fontSize: type.small, color: colors.muted, lineHeight: 20 },
  barTrack: {
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.bg,
    overflow: "hidden",
    marginTop: space.xs,
  },
  barFill: {
    height: "100%",
    backgroundColor: colors.brand,
    borderRadius: 4,
  },
  meta: { fontSize: type.small, fontWeight: "600", color: colors.ink },
  link: {
    marginTop: space.xs,
    color: colors.accent,
    fontWeight: "700",
    fontSize: type.small,
  },
});
