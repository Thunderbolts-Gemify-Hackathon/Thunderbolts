import { type Href, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { ApiError } from "@/api/http";
import { formatAr } from "@/api/market";
import { QUARTIER_COORDS } from "@/api/onboarding";
import {
  getListeCoursesPeriode,
  type ListeCoursesPeriode,
  type PeriodeCourses,
} from "@/api/planning";
import { todayIso, weekStartIso } from "@/lib/dates";
import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { AiText } from "@/ui/Markdown";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

type Filter = "acheter" | "tout";

const PERIODE_LABEL: Record<PeriodeCourses, string> = {
  jour: "Aujourd'hui",
  semaine: "Cette semaine",
  mois: "Ce mois",
};

function formatQty(n: number, unite: string) {
  const v = Number.isInteger(n) ? String(n) : n.toFixed(1);
  return `${v} ${unite}`;
}

export default function CoursesScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ periode?: string }>();
  const { session } = useSession();
  const { data } = useOnboarding();
  const profilId = session?.profilId;
  const token = session?.apiToken;

  const initialPeriode: PeriodeCourses =
    params.periode === "jour" || params.periode === "mois" ? params.periode : "semaine";
  const [periode, setPeriode] = useState<PeriodeCourses>(initialPeriode);
  const [filter, setFilter] = useState<Filter>("acheter");
  const [liste, setListe] = useState<ListeCoursesPeriode | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const quartier = data.localisation.quartier;
  const coords = quartier ? QUARTIER_COORDS[quartier] : null;
  const dateDebut = useMemo(
    () => (periode === "jour" ? todayIso() : weekStartIso()),
    [periode]
  );

  const load = useCallback(async () => {
    if (!profilId || !token) {
      setError("Session invalide. Refais l'onboarding.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setListe(
        await getListeCoursesPeriode(profilId, token, periode, dateDebut, coords)
      );
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 404
          ? "Aucun planning trouve. Genere d'abord ton menu."
          : e instanceof ApiError
            ? e.detail
            : "Chargement impossible"
      );
      setListe(null);
    } finally {
      setLoading(false);
    }
  }, [profilId, token, periode, dateDebut, coords]);

  useEffect(() => {
    void load();
  }, [load]);

  const items = liste?.items ?? [];
  const aAcheter = useMemo(() => items.filter((i) => i.quantite_a_acheter > 0), [items]);
  const visible = filter === "acheter" ? aAcheter : items;

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button label="Actualiser" onPress={() => void load()} disabled={loading} />
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
      <Body>Compare le besoin de tes repas avec ton stock actuel.</Body>

      <View style={styles.chips}>
        {(Object.keys(PERIODE_LABEL) as PeriodeCourses[]).map((p) => (
          <Pressable
            key={p}
            onPress={() => setPeriode(p)}
            style={[styles.chip, periode === p && styles.chipActive]}
          >
            <Text style={[styles.chipText, periode === p && styles.chipTextActive]}>
              {PERIODE_LABEL[p]}
            </Text>
          </Pressable>
        ))}
      </View>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {!loading && liste ? (
        <>
          {liste.message ? (
            <View style={styles.messageCard}>
              <AiText content={liste.message} />
            </View>
          ) : null}

          <View style={styles.summary}>
            <Text style={styles.summaryText}>
              {aAcheter.length} a acheter · {items.length - aAcheter.length} deja en stock
            </Text>
            {liste.estimation ? (
              <Text style={styles.summaryCost}>
                ~{formatAr(liste.estimation.cout_total_estime)}
              </Text>
            ) : null}
          </View>

          <View style={styles.filters}>
            <Pressable
              onPress={() => setFilter("acheter")}
              style={[styles.filterChip, filter === "acheter" && styles.chipActive]}
            >
              <Text style={[styles.chipText, filter === "acheter" && styles.chipTextActive]}>
                A acheter
              </Text>
            </Pressable>
            <Pressable
              onPress={() => setFilter("tout")}
              style={[styles.filterChip, filter === "tout" && styles.chipActive]}
            >
              <Text style={[styles.chipText, filter === "tout" && styles.chipTextActive]}>
                Tout
              </Text>
            </Pressable>
          </View>

          {visible.length === 0 ? (
            <Body>
              {filter === "acheter"
                ? "Rien a acheter. Ton stock couvre tes repas prevus."
                : "Liste vide pour cette periode."}
            </Body>
          ) : null}

          {visible.map((item) => {
            const buy = item.quantite_a_acheter > 0;
            return (
              <View
                key={item.ingredient.id}
                style={[styles.card, buy && styles.cardBuy]}
              >
                <Text style={styles.nom}>{item.ingredient.nom}</Text>
                <Text style={styles.meta}>
                  Besoin {formatQty(item.quantite_totale_requise, item.unite)} · stock{" "}
                  {formatQty(item.quantite_disponible, item.unite)}
                </Text>
                {buy ? (
                  <Text style={styles.gap}>
                    A acheter {formatQty(item.quantite_a_acheter, item.unite)}
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
        </>
      ) : null}
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
  messageCard: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.md,
  },
  summary: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.md,
    padding: space.md,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  summaryText: { color: colors.brand, fontWeight: "700", fontSize: type.body },
  summaryCost: { color: colors.brand, fontWeight: "700", fontSize: type.body },
  filters: { flexDirection: "row", gap: space.sm },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  chip: {
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
  },
  filterChip: {
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
