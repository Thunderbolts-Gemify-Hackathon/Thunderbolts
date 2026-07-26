import { type Href, useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { ApiError } from "@/api/http";
import { listRecettes, type Recette } from "@/api/recettes";
import type { Recette as CachedRecette } from "@/api/repas";
import { cacheRecette } from "@/lib/recipeCache";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

const TAGS = [
  { id: "", label: "Toutes" },
  { id: "rapide", label: "Rapide" },
  { id: "dejeuner", label: "Déjeuner" },
  { id: "diner", label: "Dîner" },
  { id: "vegetarien", label: "Végé" },
  { id: "leger", label: "Léger" },
];

export default function RecettesExplorerScreen() {
  const router = useRouter();
  const { session } = useSession();
  const [q, setQ] = useState("");
  const [tag, setTag] = useState("");
  const [maxDuree, setMaxDuree] = useState<number | undefined>(undefined);
  const [items, setItems] = useState<Recette[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await listRecettes(session?.apiToken ?? null, {
        q: q.trim() || undefined,
        tags: tag || undefined,
        max_duree: maxDuree,
        profil_id: session?.profilId,
      });
      setItems(list);
      list.forEach((r) => cacheRecette(r as unknown as CachedRecette));
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Chargement impossible");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [q, tag, maxDuree, session?.apiToken, session?.profilId]);

  useEffect(() => {
    const t = setTimeout(() => void load(), 200);
    return () => clearTimeout(t);
  }, [load]);

  return (
    <Screen
      footer={
        <View style={{ gap: space.sm }}>
          <Button label="Actualiser" onPress={() => void load()} disabled={loading} />
          <Button label="Retour" variant="ghost" onPress={() => router.back()} />
        </View>
      }
    >
      <Title>Recettes</Title>
      <Body>Explore le catalogue KaliTao — plats étudiants et malagasy.</Body>

      <TextInput
        value={q}
        onChangeText={setQ}
        placeholder="Rechercher (ex. romazava)"
        placeholderTextColor={colors.muted}
        style={styles.input}
      />

      <View style={styles.chips}>
        {TAGS.map((t) => (
          <Pressable
            key={t.id || "all"}
            onPress={() => setTag(t.id)}
            style={[styles.chip, tag === t.id && styles.chipActive]}
          >
            <Text style={[styles.chipText, tag === t.id && styles.chipTextActive]}>
              {t.label}
            </Text>
          </Pressable>
        ))}
        <Pressable
          onPress={() => setMaxDuree(maxDuree === 20 ? undefined : 20)}
          style={[styles.chip, maxDuree === 20 && styles.chipActive]}
        >
          <Text style={[styles.chipText, maxDuree === 20 && styles.chipTextActive]}>
            ≤ 20 min
          </Text>
        </Pressable>
      </View>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {!loading ? (
        <Text style={styles.count}>{items.length} recette(s)</Text>
      ) : null}

      {items.map((r) => (
        <Pressable
          key={r.id}
          style={styles.card}
          onPress={() => router.push(`/recette/${r.id}` as Href)}
        >
          <Text style={styles.nom}>{r.nom}</Text>
          <Text style={styles.meta}>
            {r.duree_minutes ? `${r.duree_minutes} min · ` : ""}
            {Math.round(r.kcal_total)} kcal
            {r.tags?.length ? ` · ${r.tags.slice(0, 3).join(", ")}` : ""}
          </Text>
        </Pressable>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  input: {
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingHorizontal: space.md,
    paddingVertical: space.sm + 2,
    fontSize: type.body,
    color: colors.ink,
  },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  chip: {
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
  },
  chipActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  chipText: { color: colors.ink, fontSize: type.small },
  chipTextActive: { color: "#F7F3EA", fontWeight: "600" },
  count: { color: colors.muted, fontSize: type.small, fontWeight: "600" },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
  },
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.md,
    gap: 4,
  },
  nom: { fontSize: type.body, fontWeight: "700", color: colors.ink },
  meta: { fontSize: type.small, color: colors.muted },
});
