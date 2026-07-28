import { Feather } from "@expo/vector-icons";
import { type Href, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { ApiError } from "@/api/http";
import { formatAr } from "@/api/market";
import { planOneTrip, type OneTripResult } from "@/api/marketPanier";
import { QUARTIER_COORDS } from "@/api/onboarding";
import { terminerCourses } from "@/api/courses";
import {
  getListeCoursesPeriode,
  type ListeCoursesPeriode,
  type PeriodeCourses,
} from "@/api/planning";
import { listIngredients } from "@/api/stock";
import { approvisionnerStock } from "@/api/stockAlerts";
import { todayIso, weekStartIso } from "@/lib/dates";
import { useCustomCourses } from "@/lib/customCourses";
import { enqueueMutation } from "@/lib/offlineQueue";
import { saveActiveTrip } from "@/lib/tripStore";
import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { AddItemBar } from "@/ui/AddItemBar";
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
  const [catalogue, setCatalogue] = useState<string[]>([]);
  const [terminating, setTerminating] = useState(false);
  const [trip, setTrip] = useState<OneTripResult | null>(null);
  const [tripLoading, setTripLoading] = useState(false);
  const custom = useCustomCourses(profilId, token);

  const quartier = data.localisation.quartier;
  const coords = useMemo(() => {
    if (session?.localisationLat != null && session?.localisationLon != null) {
      return { lat: session.localisationLat, lon: session.localisationLon };
    }
    return quartier ? QUARTIER_COORDS[quartier] : null;
  }, [session?.localisationLat, session?.localisationLon, quartier]);
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

  useEffect(() => {
    if (!token) return;
    listIngredients(token)
      .then((list) => setCatalogue(list.map((i) => i.nom)))
      .catch(() => setCatalogue([]));
  }, [token]);

  const items = liste?.items ?? [];
  const aAcheter = useMemo(() => items.filter((i) => i.quantite_a_acheter > 0), [items]);
  const visible = filter === "acheter" ? aAcheter : items;
  const customVisible =
    filter === "acheter" ? custom.items.filter((i) => !i.fait) : custom.items;

  const onTerminer = async () => {
    if (!profilId || !token) return;
    const customIds = custom.items
      .filter((i) => i.fait && !i.id.startsWith("local-"))
      .map((i) => i.id);
    const stockItems = aAcheter.map((i) => ({
      ingredient_id: i.ingredient.id,
      quantite: i.quantite_a_acheter,
      unite: i.unite,
    }));

    if (!customIds.length && !stockItems.length) {
      setError("Rien à enregistrer : coche tes ajouts ou génère une liste à acheter.");
      return;
    }
    setTerminating(true);
    setError(null);
    try {
      if (stockItems.length) {
        await approvisionnerStock(
          profilId,
          { items: stockItems, label: `Courses ${periode}` },
          token
        );
      }
      if (customIds.length) {
        await terminerCourses(profilId, token, customIds);
        await custom.reload();
      }
      await load();
    } catch (e) {
      if (stockItems.length) {
        await enqueueMutation({
          method: "POST",
          path: `/stock/${profilId}/approvisionner`,
          body: { items: stockItems, label: `Courses ${periode}` },
          token,
        });
        setError(
          "Hors ligne : courses mises en file, sync auto au retour du réseau."
        );
      } else {
        setError(e instanceof ApiError ? e.detail : "Impossible de terminer les courses");
      }
    } finally {
      setTerminating(false);
    }
  };

  const onOneTrip = async () => {
    if (!coords) {
      setError("Localisation manquante : complète ton quartier dans le profil.");
      return;
    }
    if (!aAcheter.length) {
      setError("Rien à acheter pour calculer un trajet.");
      return;
    }
    setTripLoading(true);
    setError(null);
    try {
      const res = await planOneTrip({
        lat: coords.lat,
        lon: coords.lon,
        rayon_km: 15,
        profil_id: profilId ?? undefined,
        budget: liste?.estimation?.cout_total_estime,
        items: aAcheter.map((i) => ({
          ingredient_id: i.ingredient.id,
          ingredient_nom: i.ingredient.nom,
          quantite: i.quantite_a_acheter,
          unite: i.unite,
        })),
      });
      setTrip(res);
      await saveActiveTrip(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Trajet impossible à calculer");
      setTrip(null);
    } finally {
      setTripLoading(false);
    }
  };

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label={tripLoading ? "Calcul du trajet…" : "Un trajet (marchés)"}
            onPress={() => void onOneTrip()}
            disabled={loading || tripLoading || !aAcheter.length}
          />
          <Button
            label="Courses terminées → stock"
            onPress={() => void onTerminer()}
            disabled={loading || terminating}
          />
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

      <AddItemBar
        suggestions={catalogue}
        onAdd={(nom) => void custom.add(nom)}
      />

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

      {customVisible.length > 0 ? (
        <View style={styles.customSection}>
          <Text style={styles.customTitle}>Ajoutés par toi</Text>
          {customVisible.map((item, i) => (
            <Pressable
              key={item.id}
              onPress={() => void custom.toggle(item.id)}
              style={[styles.customRow, i < customVisible.length - 1 && styles.customRowDivider]}
            >
              <View style={[styles.checkbox, item.fait && styles.checkboxDone]}>
                {item.fait ? <Feather name="check" size={13} color="#F7F3EA" /> : null}
              </View>
              <Text style={[styles.customLabel, item.fait && styles.customLabelDone]}>
                {item.nom}
              </Text>
              <Pressable
                onPress={(e) => {
                  e.stopPropagation();
                  void custom.remove(item.id);
                }}
                hitSlop={8}
              >
                <Feather name="x" size={16} color={colors.muted} />
              </Pressable>
            </Pressable>
          ))}
        </View>
      ) : null}

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

          {trip ? (
            <View style={styles.tripCard}>
              <Text style={styles.tripTitle}>{trip.message}</Text>
              <Text style={styles.tripMeta}>
                {trip.nb_arrets} arrêt(s) · {trip.distance_totale_km} km · ~
                {formatAr(trip.cout_estime)}
              </Text>
              {trip.stops.map((s) => (
                <Pressable
                  key={s.point_de_vente.id}
                  style={styles.tripStop}
                  onPress={() => router.push("/map?mode=trip" as Href)}
                >
                  <Text style={styles.tripStopNom}>{s.point_de_vente.nom}</Text>
                  <Text style={styles.tripStopMeta}>
                    {s.distance_km} km · {s.items.length} produit(s) · ~
                    {formatAr(s.cout_estime)}
                  </Text>
                </Pressable>
              ))}
              <View style={styles.tripActions}>
                <Button
                  label="Voir sur la carte"
                  onPress={() => router.push("/map?mode=trip" as Href)}
                />
                <Button
                  label="Lancer la sortie"
                  variant="ghost"
                  onPress={() => router.push("/sortie-marche" as Href)}
                />
              </View>
            </View>
          ) : null}

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
  customSection: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    overflow: "hidden",
  },
  customTitle: {
    fontSize: type.small,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
    letterSpacing: 0.4,
    paddingHorizontal: space.md,
    paddingTop: space.sm,
    paddingBottom: space.xs,
  },
  customRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.sm,
    paddingVertical: space.sm + 2,
    paddingHorizontal: space.md,
  },
  customRowDivider: { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.line },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1.5,
    borderColor: colors.line,
    alignItems: "center",
    justifyContent: "center",
  },
  checkboxDone: { backgroundColor: colors.brand, borderColor: colors.brand },
  customLabel: { flex: 1, fontSize: type.body, color: colors.ink },
  customLabelDone: { color: colors.muted, textDecorationLine: "line-through" },
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
  tripCard: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.md,
    padding: space.md,
    gap: space.sm,
  },
  tripTitle: { fontSize: type.body, fontWeight: "700", color: colors.ink },
  tripMeta: { fontSize: type.small, color: colors.muted, fontWeight: "600" },
  tripStop: {
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    padding: space.sm,
    gap: 2,
  },
  tripStopNom: { fontWeight: "700", color: colors.brand, fontSize: type.body },
  tripStopMeta: { fontSize: type.small, color: colors.muted },
  tripActions: { gap: space.sm, marginTop: space.sm },
});
