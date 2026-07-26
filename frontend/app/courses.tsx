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
  getListeCoursesPeriode,
  isAAcheter,
  type EstimationCoutListe,
  type ListeCoursesItem,
  type PeriodeCourses,
} from "@/api/planning";
import { weekStartIso } from "@/lib/dates";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

type Filter = "acheter" | "tout";

const PERIODES: { id: PeriodeCourses; label: string }[] = [
  { id: "jour", label: "Jour" },
  { id: "semaine", label: "Semaine" },
  { id: "mois", label: "Mois" },
];

function formatQty(n: number, unite: string) {
  const v = Number.isInteger(n) ? String(n) : n.toFixed(1);
  return `${v} ${unite}`;
}

function formatAr(n: number) {
  return `${Math.round(n).toLocaleString("fr-FR")} Ar`;
}

export default function CoursesScreen() {
  const router = useRouter();
  const { session } = useSession();
  const profilId = session?.profilId;
  const token = session?.apiToken;
  const dateDebut = useMemo(() => weekStartIso(), []);

  const [periode, setPeriode] = useState<PeriodeCourses>("semaine");
  const [items, setItems] = useState<ListeCoursesItem[]>([]);
  const [estimation, setEstimation] = useState<EstimationCoutListe | null>(null);
  const [joursCouverts, setJoursCouverts] = useState(7);
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
      const data = await getListeCoursesPeriode(
        profilId,
        token,
        dateDebut,
        periode
      );
      setHasPlanning(true);
      setItems(data.items);
      setEstimation(data.estimation);
      setJoursCouverts(data.jours_couverts);
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        setHasPlanning(false);
        setItems([]);
        setEstimation(null);
        setError(null);
        return;
      }
      setError(e instanceof ApiError ? e.detail : "Chargement impossible");
    } finally {
      setLoading(false);
    }
  }, [profilId, token, dateDebut, periode]);

  useEffect(() => {
    void load();
  }, [load]);

  const aAcheter = useMemo(
    () => items.filter((i) => isAAcheter(i.statut)),
    [items]
  );
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
        Du {dateDebut} · {joursCouverts} jour{joursCouverts > 1 ? "s" : ""}. Besoin
        du planning moins ton stock.
      </Body>

      <View style={styles.filters}>
        {PERIODES.map((p) => (
          <Pressable
            key={p.id}
            onPress={() => setPeriode(p.id)}
            style={[styles.chip, periode === p.id && styles.chipActive]}
          >
            <Text
              style={[
                styles.chipText,
                periode === p.id && styles.chipTextActive,
              ]}
            >
              {p.label}
            </Text>
          </Pressable>
        ))}
      </View>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {!loading && !hasPlanning ? (
        <Body>
          Aucun planning semaine pour cette date. Genere d'abord ton menu.
        </Body>
      ) : null}

      {!loading && hasPlanning ? (
        <>
          <View style={styles.summary}>
            <Text style={styles.summaryText}>
              {aAcheter.length} a acheter · {items.length - aAcheter.length} deja
              en stock
            </Text>
            {estimation ? (
              <Text style={styles.costText}>
                Estimation {formatAr(estimation.cout_total_estime)}
                {estimation.marches_a_visiter.length
                  ? ` · ${estimation.marches_a_visiter.length} marche(s)`
                  : ""}
              </Text>
            ) : null}
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
        const unite = item.unite || item.ingredient.unite_defaut;
        return (
          <View
            key={item.ingredient.id}
            style={[styles.card, buy && styles.cardBuy]}
          >
            <Text style={styles.nom}>{item.ingredient.nom}</Text>
            <Text style={styles.meta}>
              {item.categorie} · besoin{" "}
              {formatQty(item.quantite_totale_requise, unite)} · stock{" "}
              {formatQty(item.quantite_disponible, unite)}
            </Text>
            {buy ? (
              <Text style={styles.gap}>
                Manque {formatQty(item.quantite_a_acheter, unite)}
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
    gap: 4,
  },
  summaryText: {
    color: colors.brand,
    fontWeight: "700",
    fontSize: type.body,
  },
  costText: {
    color: colors.ink,
    fontSize: type.small,
    fontWeight: "600",
  },
  filters: { flexDirection: "row", gap: space.sm, flexWrap: "wrap" },
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
