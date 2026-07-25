import { type Href, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { ApiError } from "@/api/http";
import {
  getCourses,
  getPlanning,
  isAAcheter,
  manquant,
  type CourseItem,
} from "@/api/planning";
import { weekStartIso } from "@/lib/dates";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

type Filter = "acheter" | "tout";

function formatQty(n: number, unite: string) {
  const v = Number.isInteger(n) ? String(n) : n.toFixed(1);
  return `${v} ${unite}`;
}

export default function CoursesScreen() {
  const router = useRouter();
  const { session } = useSession();
  const profilId = session?.profilId;
  const token = session?.apiToken;
  const dateDebut = useMemo(() => weekStartIso(), []);

  const [items, setItems] = useState<CourseItem[]>([]);
  const [filter, setFilter] = useState<Filter>("acheter");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasPlanning, setHasPlanning] = useState(true);

  const load = useCallback(async () => {
    if (!profilId || !token) {
      setError("Session invalide. Refais l'onboarding.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const planning = await getPlanning(profilId, token, dateDebut).catch((e) => {
        if (e instanceof ApiError && e.status === 404) return null;
        throw e;
      });
      if (!planning) {
        setHasPlanning(false);
        setItems([]);
        return;
      }
      setHasPlanning(true);
      setItems(await getCourses(planning.id, token));
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Chargement impossible");
    } finally {
      setLoading(false);
    }
  }, [profilId, token, dateDebut]);

  useEffect(() => {
    void load();
  }, [load]);

  const aAcheter = useMemo(() => items.filter((i) => isAAcheter(i.statut)), [items]);
  const visible = filter === "acheter" ? aAcheter : items;

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label="Actualiser"
            onPress={() => void load()}
            disabled={loading}
          />
          <Button
            label="Voir le planning"
            variant="ghost"
            onPress={() => router.push("/planning" as Href)}
          />
          <Button label="Retour" variant="ghost" onPress={() => router.back()} />
        </View>
      }
    >
      <Title>Liste de courses</Title>
      <Body>
        Semaine du {dateDebut}. Compare le besoin du planning avec ton stock.
      </Body>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {!loading && !hasPlanning ? (
        <Body>Aucun planning cette semaine. Genere d'abord ton menu.</Body>
      ) : null}

      {!loading && hasPlanning ? (
        <>
          <View style={styles.summary}>
            <Text style={styles.summaryText}>
              {aAcheter.length} a acheter · {items.length - aAcheter.length} deja en stock
            </Text>
          </View>

          <View style={styles.filters}>
            <Pressable
              onPress={() => setFilter("acheter")}
              style={[styles.chip, filter === "acheter" && styles.chipActive]}
            >
              <Text
                style={[
                  styles.chipText,
                  filter === "acheter" && styles.chipTextActive,
                ]}
              >
                A acheter
              </Text>
            </Pressable>
            <Pressable
              onPress={() => setFilter("tout")}
              style={[styles.chip, filter === "tout" && styles.chipActive]}
            >
              <Text
                style={[
                  styles.chipText,
                  filter === "tout" && styles.chipTextActive,
                ]}
              >
                Tout
              </Text>
            </Pressable>
          </View>
        </>
      ) : null}

      {!loading && hasPlanning && visible.length === 0 ? (
        <Body>
          {filter === "acheter"
            ? "Rien a acheter. Ton stock couvre le planning."
            : "Liste vide pour ce planning."}
        </Body>
      ) : null}

      {visible.map((item) => {
        const buy = isAAcheter(item.statut);
        const unite = item.ingredient.unite_defaut;
        const gap = manquant(item);
        return (
          <View
            key={item.ingredient.id}
            style={[styles.card, buy && styles.cardBuy]}
          >
            <Text style={styles.nom}>{item.ingredient.nom}</Text>
            <Text style={styles.meta}>
              Besoin {formatQty(item.poids_total_requis, unite)} · stock{" "}
              {formatQty(item.stock_disponible, unite)}
            </Text>
            {buy ? (
              <Text style={styles.gap}>
                Manque {formatQty(gap, unite)}
              </Text>
            ) : (
              <Text style={styles.ok}>Disponible</Text>
            )}
            {buy ? (
              <Pressable
                onPress={() =>
                  router.push(
                    `/map?ingredientId=${encodeURIComponent(item.ingredient.id)}` as Href
                  )
                }
                style={styles.action}
              >
                <Text style={styles.actionText}>Ou acheter (carte)</Text>
              </Pressable>
            ) : null}
          </View>
        );
      })}
    </Screen>
  );
}

const styles = StyleSheet.create({
  actions: { gap: space.sm },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
  summary: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.md,
    padding: space.md,
  },
  summaryText: {
    color: colors.brand,
    fontWeight: "700",
    fontSize: type.body,
  },
  filters: { flexDirection: "row", gap: space.sm },
  chip: {
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
  },
  chipActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  chipText: { color: colors.ink, fontSize: type.body },
  chipTextActive: { color: "#F7F3EA", fontWeight: "600" },
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.md,
    gap: 4,
  },
  cardBuy: { borderColor: colors.accent },
  nom: { fontSize: type.body, fontWeight: "700", color: colors.ink },
  meta: { fontSize: type.small, color: colors.muted },
  gap: { fontSize: type.small, color: colors.accent, fontWeight: "700" },
  ok: { fontSize: type.small, color: colors.brand, fontWeight: "700" },
  action: {
    marginTop: space.sm,
    alignSelf: "flex-start",
    paddingVertical: space.xs,
    paddingHorizontal: space.sm,
    backgroundColor: colors.brandSoft,
    borderRadius: radius.sm,
  },
  actionText: { color: colors.brand, fontWeight: "700", fontSize: type.label },
});
