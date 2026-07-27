import { type Href, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { ApiError } from "@/api/http";
import { findNearbyMarket, formatAr, type MarketMatch } from "@/api/market";
import {
  checkPanier,
  type PanierCheckResult,
  type PanierItem,
} from "@/api/marketPanier";
import { QUARTIER_COORDS } from "@/api/onboarding";
import { createPriceReport, getPriceIndex, type PriceIndex } from "@/api/prices";
import { listIngredients, type Ingredient } from "@/api/stock";
import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

export default function MarketScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ ingredientId?: string }>();
  const { session } = useSession();
  const { data } = useOnboarding();
  const token = session?.apiToken;
  const profilId = session?.profilId;

  const quartier = data.localisation.quartier;
  const coords = quartier ? QUARTIER_COORDS[quartier] : null;
  const prefId =
    typeof params.ingredientId === "string" ? params.ingredientId : null;

  const [catalog, setCatalog] = useState<Ingredient[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(prefId);
  const [matches, setMatches] = useState<MarketMatch[]>([]);
  const [crowdIndex, setCrowdIndex] = useState<PriceIndex | null>(null);
  const [reportPrix, setReportPrix] = useState("");
  const [reporting, setReporting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);
  const [autoSearched, setAutoSearched] = useState(false);

  const [panierLines, setPanierLines] = useState<PanierItem[]>([]);
  const [panierQty, setPanierQty] = useState("500");
  const [panierBudget, setPanierBudget] = useState("50000");
  const [panierResult, setPanierResult] = useState<PanierCheckResult | null>(null);
  const [checkingPanier, setCheckingPanier] = useState(false);

  const selected = useMemo(
    () => catalog.find((i) => i.id === selectedId) ?? null,
    [catalog, selectedId],
  );

  const loadCrowd = useCallback(async () => {
    if (!selectedId || !quartier) {
      setCrowdIndex(null);
      return;
    }
    try {
      const idx = await getPriceIndex({
        quartier,
        ingredient_id: selectedId,
      });
      setCrowdIndex(idx);
    } catch {
      setCrowdIndex(null);
    }
  }, [selectedId, quartier]);

  const search = useCallback(async () => {
    if (!selectedId || !coords) {
      setError(
        coords
          ? "Choisis un ingredient."
          : "Quartier manquant. Termine l'onboarding localisation.",
      );
      return;
    }
    setSearching(true);
    setError(null);
    try {
      const rows = await findNearbyMarket(selectedId, coords.lat, coords.lon);
      setMatches(rows);
      await loadCrowd();
      if (rows.length === 0) {
        setError("Aucun point de vente dans le rayon.");
      }
    } catch (e) {
      setMatches([]);
      setError(e instanceof ApiError ? e.detail : "Recherche impossible");
    } finally {
      setSearching(false);
    }
  }, [selectedId, coords, loadCrowd]);

  const submitPrice = async () => {
    if (!profilId || !token || !selectedId || !quartier) return;
    const prix = Number(reportPrix);
    if (!Number.isFinite(prix) || prix <= 0) {
      setError("Indique un prix positif en Ariary.");
      return;
    }
    setReporting(true);
    setError(null);
    setOkMsg(null);
    try {
      await createPriceReport(profilId, token, {
        ingredient_id: selectedId,
        quartier,
        prix,
        unite: "kg",
      });
      setReportPrix("");
      setOkMsg("Prix signalé. Merci !");
      await loadCrowd();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Envoi impossible");
    } finally {
      setReporting(false);
    }
  };

  const addToPanier = () => {
    if (!selected) return;
    const q = Number(panierQty);
    if (!Number.isFinite(q) || q <= 0) {
      setError("Quantité panier invalide.");
      return;
    }
    setPanierLines((prev) => [
      ...prev,
      {
        ingredient_nom: selected.nom,
        quantite: q,
        unite: selected.unite_defaut || "g",
      },
    ]);
  };

  const runPanierCheck = async () => {
    if (!panierLines.length) {
      setError("Ajoute au moins un article au panier.");
      return;
    }
    const budget = Number(panierBudget);
    if (!Number.isFinite(budget) || budget <= 0) {
      setError("Budget panier invalide.");
      return;
    }
    setCheckingPanier(true);
    setError(null);
    try {
      const res = await checkPanier({
        items: panierLines,
        budget,
        quartier: quartier || undefined,
      });
      setPanierResult(res);
    } catch (e) {
      setPanierResult(null);
      setError(e instanceof ApiError ? e.detail : "Vérification panier impossible");
    } finally {
      setCheckingPanier(false);
    }
  };

  useEffect(() => {
    if (!token) {
      setError("Session invalide. Refais l'onboarding.");
      setLoading(false);
      return;
    }
    setLoading(true);
    listIngredients(token)
      .then((ings) => {
        setCatalog(ings);
        const next =
          (prefId && ings.some((i) => i.id === prefId) ? prefId : null) ??
          ings[0]?.id ??
          null;
        setSelectedId(next);
      })
      .catch((e) => {
        setError(e instanceof ApiError ? e.detail : "Catalogue introuvable");
      })
      .finally(() => setLoading(false));
  }, [token, prefId]);

  useEffect(() => {
    if (autoSearched || loading || !prefId || !selectedId || !coords) return;
    if (selectedId !== prefId) return;
    setAutoSearched(true);
    void search();
  }, [autoSearched, loading, prefId, selectedId, coords, search]);

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label={searching ? "Recherche…" : "Chercher autour de moi"}
            onPress={() => void search()}
            disabled={searching || loading || !selectedId}
          />
          <Button
            label="Voir sur la carte"
            variant="ghost"
            onPress={() =>
              router.push(
                (selectedId
                  ? `/map?ingredientId=${encodeURIComponent(selectedId)}`
                  : "/map") as Href,
              )
            }
          />
          <Button
            label="Aller au marche (liste du jour)"
            variant="ghost"
            onPress={() => router.push("/courses?periode=jour" as Href)}
          />
          <Button
            label="Retour"
            variant="ghost"
            onPress={() => router.back()}
          />
        </View>
      }
    >
      <Title>Marches proches</Title>
      <Body>
        {quartier
          ? `Depuis ${quartier}. Tries par prix, trajets a eviter en bas.`
          : "Indique ton quartier dans l'onboarding pour localiser les marches."}
      </Body>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Text style={styles.section}>Ingredient</Text>
      <View style={styles.chips}>
        {catalog.map((ing) => {
          const active = ing.id === selectedId;
          return (
            <Pressable
              key={ing.id}
              onPress={() => setSelectedId(ing.id)}
              style={[styles.chip, active && styles.chipActive]}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>
                {ing.nom}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {selected ? <Body>Recherche pour : {selected.nom}</Body> : null}

      {crowdIndex ? (
        <View style={styles.crowdCard}>
          <Text style={styles.section}>Prix quartier (crowd)</Text>
          <Text style={styles.nom}>
            {formatAr(crowdIndex.prix_moyen)} / {selected?.nom}
          </Text>
          <Text style={styles.meta}>
            {crowdIndex.nb_rapports} signalement(s) · {crowdIndex.quartier}
          </Text>
        </View>
      ) : null}

      {quartier && selectedId ? (
        <View style={styles.reportBox}>
          <Text style={styles.section}>Signaler un prix vu au marché</Text>
          <TextInput
            value={reportPrix}
            onChangeText={setReportPrix}
            keyboardType="numeric"
            placeholder="Prix en Ar (ex. 3000)"
            placeholderTextColor={colors.muted}
            style={styles.input}
          />
          <Button
            label={reporting ? "Envoi…" : "Envoyer ce prix"}
            onPress={() => void submitPrice()}
            disabled={reporting}
          />
          {okMsg ? <Text style={styles.ok}>{okMsg}</Text> : null}
        </View>
      ) : null}

      <Text style={styles.section}>Panier vs budget</Text>
      <View style={styles.reportBox}>
        <TextInput
          value={panierQty}
          onChangeText={setPanierQty}
          keyboardType="numeric"
          placeholder="Quantité"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Button
          label="Ajouter l'ingrédient au panier"
          variant="ghost"
          onPress={addToPanier}
          disabled={!selected}
        />
        {panierLines.map((line, idx) => (
          <Text key={`${line.ingredient_nom}-${idx}`} style={styles.meta}>
            {line.ingredient_nom} · {line.quantite} {line.unite || "g"}
          </Text>
        ))}
        <TextInput
          value={panierBudget}
          onChangeText={setPanierBudget}
          keyboardType="numeric"
          placeholder="Budget Ar"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Button
          label={checkingPanier ? "Calcul…" : "Vérifier le panier"}
          onPress={() => void runPanierCheck()}
          disabled={checkingPanier}
        />
        {panierResult ? (
          <View style={styles.crowdCard}>
            <Text style={styles.nom}>
              {formatAr(panierResult.cout_estime)} / budget{" "}
              {formatAr(panierResult.budget)}
            </Text>
            <Text style={styles.meta}>
              {panierResult.statut === "over_budget"
                ? `Dépassement ${formatAr(Math.abs(panierResult.ecart))}`
                : `Sous budget (${formatAr(Math.abs(panierResult.ecart))} restants)`}
            </Text>
            {panierResult.swaps.map((s, i) => (
              <Text key={`${s.ingredient_nom}-${i}`} style={styles.meta}>
                Swap : {s.ingredient_nom} → {s.alternative} (−
                {formatAr(s.economie_estimee)}) · {s.raison}
              </Text>
            ))}
          </View>
        ) : null}
      </View>

      {matches.map((m, idx) => (
        <View
          key={`${m.point_de_vente.nom}-${idx}`}
          style={[styles.card, m.deprioritise && styles.cardWarn]}
        >
          <Text style={styles.nom}>{m.point_de_vente.nom}</Text>
          <Text style={styles.meta}>
            {formatAr(m.prix)} · {m.point_de_vente.type}
          </Text>
          <Text style={styles.meta}>
            {m.itineraire
              ? `${m.itineraire.distance} km · ${m.itineraire.niveau_securite} · ${m.itineraire.mode_deplacement}`
              : "Itineraire non renseigne"}
          </Text>
          {m.deprioritise ? (
            <Text style={styles.warn}>Deprioritise (a eviter)</Text>
          ) : null}
        </View>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  actions: { gap: space.sm },
  section: {
    marginTop: space.sm,
    fontSize: type.label,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
    letterSpacing: 0.3,
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
  cardWarn: { borderColor: colors.accent },
  nom: { fontSize: type.body, fontWeight: "700", color: colors.ink },
  meta: { fontSize: type.small, color: colors.muted },
  warn: { fontSize: type.small, color: colors.accent, fontWeight: "700" },
  crowdCard: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.md,
    padding: space.md,
    gap: 4,
  },
  reportBox: { gap: space.sm, marginTop: space.sm },
  input: {
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
    fontSize: type.body,
    color: colors.ink,
  },
  ok: { color: colors.ok, fontSize: type.small, fontWeight: "600" },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
});
