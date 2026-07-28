import { Feather } from "@expo/vector-icons";
import { type Href, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { ApiError } from "@/api/http";
import { formatAr } from "@/api/market";
import type { OneTripResult, OneTripStop } from "@/api/marketPanier";
import { createPriceReport } from "@/api/prices";
import { postDefiProgress } from "@/api/social";
import { approvisionnerStock } from "@/api/stockAlerts";
import { speak, stopSpeaking } from "@/lib/speech";
import {
  checkKey,
  clearActiveTrip,
  loadActiveTrip,
  loadSortieChecks,
  saveSortieChecks,
} from "@/lib/tripStore";
import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

export default function SortieMarcheScreen() {
  const router = useRouter();
  const { session } = useSession();
  const { data } = useOnboarding();
  const profilId = session?.profilId;
  const token = session?.apiToken;
  const quartier = data.localisation.quartier || "Analakely";

  const [trip, setTrip] = useState<OneTripResult | null>(null);
  const [checks, setChecks] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stopIndex, setStopIndex] = useState(0);
  const [priceDraft, setPriceDraft] = useState<{
    ingredientId: string;
    nom: string;
    prix: string;
  } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const [t, c] = await Promise.all([loadActiveTrip(), loadSortieChecks()]);
    setTrip(t);
    setChecks(new Set(c));
    setLoading(false);
    if (!t) setError("Aucun trajet actif. Calcule « Un trajet » depuis Courses.");
  }, []);

  useEffect(() => {
    void load();
    return () => {
      void stopSpeaking();
    };
  }, [load]);

  const stop: OneTripStop | null = trip?.stops[stopIndex] ?? null;
  const totalItems = useMemo(
    () => trip?.stops.reduce((n, s) => n + s.items.length, 0) ?? 0,
    [trip]
  );
  const doneCount = useMemo(() => {
    if (!trip) return 0;
    let n = 0;
    for (const s of trip.stops) {
      for (const it of s.items) {
        if (checks.has(checkKey(s.point_de_vente.id, it.ingredient_id))) n += 1;
      }
    }
    return n;
  }, [trip, checks]);

  const toggle = async (pdvId: string, ingredientId: string) => {
    const key = checkKey(pdvId, ingredientId);
    const next = new Set(checks);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setChecks(next);
    await saveSortieChecks([...next]);
  };

  const announceStop = () => {
    if (!stop) return;
    const noms = stop.items.map((i) => i.ingredient_nom).join(", ");
    speak(
      `Arrêt ${stopIndex + 1} sur ${trip!.stops.length} : ${stop.point_de_vente.nom}. À prendre : ${noms}.`
    );
  };

  const onReportPrice = async () => {
    if (!profilId || !token || !priceDraft) return;
    const prix = Number(priceDraft.prix.replace(",", "."));
    if (!Number.isFinite(prix) || prix <= 0) {
      setError("Prix invalide.");
      return;
    }
    try {
      await createPriceReport(
        profilId,
        token,
        {
          ingredient_id: priceDraft.ingredientId,
          quartier,
          prix,
          unite: "kg",
        }
      );
      setPriceDraft(null);
      speak(`Prix enregistré pour ${priceDraft.nom}.`);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Signalement impossible");
    }
  };

  const onFinish = async () => {
    if (!trip || !profilId || !token) return;
    const stockItems: {
      ingredient_id: string;
      quantite: number;
      unite: string;
    }[] = [];
    for (const s of trip.stops) {
      for (const it of s.items) {
        if (checks.has(checkKey(s.point_de_vente.id, it.ingredient_id))) {
          stockItems.push({
            ingredient_id: it.ingredient_id,
            quantite: it.quantite,
            unite: it.unite,
          });
        }
      }
    }
    if (!stockItems.length) {
      Alert.alert("Sortie", "Coche au moins un produit acheté.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await approvisionnerStock(
        profilId,
        { items: stockItems, label: "Sortie marché" },
        token
      );
      try {
        await postDefiProgress(profilId, "budget-semaine", token, trip.cout_estime);
      } catch {
        /* non bloquant */
      }
      await clearActiveTrip();
      speak("Courses enregistrées dans le stock. Bravo.");
      router.replace("/stock" as Href);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Enregistrement impossible");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Screen>
        <ActivityIndicator color={colors.brand} />
      </Screen>
    );
  }

  if (!trip) {
    return (
      <Screen
        footer={
          <Button
            label="Aller aux courses"
            onPress={() => router.replace("/courses" as Href)}
          />
        }
      >
        <Title>Sortie marché</Title>
        <Body>{error ?? "Pas de trajet actif."}</Body>
      </Screen>
    );
  }

  return (
    <Screen
      footer={
        <View style={styles.footer}>
          <Button
            label="Carte du trajet"
            variant="ghost"
            onPress={() => router.push("/map?mode=trip" as Href)}
          />
          <Button
            label={saving ? "Enregistrement…" : "Terminer → stock"}
            onPress={() => void onFinish()}
            disabled={saving}
          />
          <Button label="Retour" variant="ghost" onPress={() => router.back()} />
        </View>
      }
    >
      <Title>Sortie marché</Title>
      <Body>
        {trip.message} · {doneCount}/{totalItems} cochés · ~
        {formatAr(trip.cout_estime)}
      </Body>
      {error ? <Text style={styles.error}>{error}</Text> : null}

      <View style={styles.stopChips}>
        {trip.stops.map((s, i) => (
          <Pressable
            key={s.point_de_vente.id}
            onPress={() => setStopIndex(i)}
            style={[styles.stopChip, i === stopIndex && styles.stopChipActive]}
          >
            <Text
              style={[
                styles.stopChipText,
                i === stopIndex && styles.stopChipTextActive,
              ]}
            >
              {i + 1}. {s.point_de_vente.nom.split(" ")[0]}
            </Text>
          </Pressable>
        ))}
      </View>

      {stop ? (
        <View style={styles.stopCard}>
          <View style={styles.stopHeader}>
            <Text style={styles.stopNom}>
              #{stopIndex + 1} {stop.point_de_vente.nom}
            </Text>
            <Pressable onPress={announceStop} hitSlop={8} style={styles.micBtn}>
              <Feather name="volume-2" size={18} color={colors.brand} />
            </Pressable>
          </View>
          <Text style={styles.stopMeta}>
            {stop.distance_km} km · ~{formatAr(stop.cout_estime)}
          </Text>

          {stop.items.map((it) => {
            const key = checkKey(stop.point_de_vente.id, it.ingredient_id);
            const done = checks.has(key);
            return (
              <View key={key} style={styles.itemRow}>
                <Pressable
                  onPress={() =>
                    void toggle(stop.point_de_vente.id, it.ingredient_id)
                  }
                  style={styles.itemMain}
                >
                  <View style={[styles.checkbox, done && styles.checkboxDone]}>
                    {done ? (
                      <Feather name="check" size={13} color="#F7F3EA" />
                    ) : null}
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.itemNom, done && styles.itemDone]}>
                      {it.ingredient_nom}
                    </Text>
                    <Text style={styles.itemMeta}>
                      {it.quantite} {it.unite} · ~{formatAr(it.cout_estime)}
                    </Text>
                  </View>
                </Pressable>
                <Pressable
                  hitSlop={8}
                  onPress={() =>
                    setPriceDraft({
                      ingredientId: it.ingredient_id,
                      nom: it.ingredient_nom,
                      prix: String(Math.round(it.prix_unitaire)),
                    })
                  }
                >
                  <Feather name="tag" size={18} color={colors.accent} />
                </Pressable>
              </View>
            );
          })}

          <View style={styles.navRow}>
            <Button
              label="Précédent"
              variant="ghost"
              disabled={stopIndex === 0}
              onPress={() => setStopIndex((i) => Math.max(0, i - 1))}
            />
            <Button
              label="Suivant"
              variant="ghost"
              disabled={stopIndex >= trip.stops.length - 1}
              onPress={() =>
                setStopIndex((i) => Math.min(trip.stops.length - 1, i + 1))
              }
            />
          </View>
        </View>
      ) : null}

      {priceDraft ? (
        <View style={styles.priceBox}>
          <Text style={styles.priceTitle}>
            Prix vu — {priceDraft.nom} ({quartier})
          </Text>
          <TextInput
            value={priceDraft.prix}
            onChangeText={(t) => setPriceDraft({ ...priceDraft, prix: t })}
            keyboardType="numeric"
            placeholder="Prix Ar / kg"
            placeholderTextColor={colors.muted}
            style={styles.priceInput}
          />
          <View style={styles.navRow}>
            <Button label="Annuler" variant="ghost" onPress={() => setPriceDraft(null)} />
            <Button label="Signaler" onPress={() => void onReportPrice()} />
          </View>
        </View>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  footer: { gap: space.sm },
  error: { color: colors.danger, fontWeight: "600", marginTop: space.sm },
  stopChips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: space.xs,
    marginTop: space.md,
  },
  stopChip: {
    paddingHorizontal: space.sm,
    paddingVertical: 6,
    borderRadius: radius.sm,
    backgroundColor: colors.surface,
  },
  stopChipActive: { backgroundColor: colors.brand },
  stopChipText: { fontSize: type.small, fontWeight: "600", color: colors.ink },
  stopChipTextActive: { color: "#F7F3EA" },
  stopCard: {
    marginTop: space.md,
    padding: space.md,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    gap: space.sm,
  },
  stopHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  stopNom: { fontSize: type.body, fontWeight: "700", color: colors.brand, flex: 1 },
  micBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.bg,
  },
  stopMeta: { fontSize: type.small, color: colors.muted, fontWeight: "600" },
  itemRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.sm,
    paddingVertical: 6,
  },
  itemMain: { flex: 1, flexDirection: "row", alignItems: "center", gap: space.sm },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: colors.muted,
    alignItems: "center",
    justifyContent: "center",
  },
  checkboxDone: { backgroundColor: colors.brand, borderColor: colors.brand },
  itemNom: { fontWeight: "700", color: colors.ink },
  itemDone: { textDecorationLine: "line-through", color: colors.muted },
  itemMeta: { fontSize: type.small, color: colors.muted },
  navRow: { flexDirection: "row", gap: space.sm, marginTop: space.xs },
  priceBox: {
    marginTop: space.md,
    padding: space.md,
    borderRadius: radius.md,
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.accent,
    gap: space.sm,
  },
  priceTitle: { fontWeight: "700", color: colors.ink },
  priceInput: {
    borderWidth: 1,
    borderColor: colors.muted,
    borderRadius: radius.sm,
    padding: space.sm,
    color: colors.ink,
    fontSize: type.body,
  },
});
