import { type Href, useLocalSearchParams, useRouter } from "expo-router";
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
  findNearbyMarket,
  formatAr,
  type MarketMatch,
} from "@/api/market";
import { QUARTIER_COORDS } from "@/api/onboarding";
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

  const quartier = data.localisation.quartier;
  const coords = quartier ? QUARTIER_COORDS[quartier] : null;
  const prefId = typeof params.ingredientId === "string" ? params.ingredientId : null;

  const [catalog, setCatalog] = useState<Ingredient[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(prefId);
  const [matches, setMatches] = useState<MarketMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoSearched, setAutoSearched] = useState(false);

  const selected = useMemo(
    () => catalog.find((i) => i.id === selectedId) ?? null,
    [catalog, selectedId]
  );

  const search = useCallback(async () => {
    if (!selectedId || !coords) {
      setError(
        coords
          ? "Choisis un ingredient."
          : "Quartier manquant. Termine l'onboarding localisation."
      );
      return;
    }
    setSearching(true);
    setError(null);
    try {
      const rows = await findNearbyMarket(selectedId, coords.lat, coords.lon);
      setMatches(rows);
      if (rows.length === 0) {
        setError("Aucun point de vente dans le rayon.");
      }
    } catch (e) {
      setMatches([]);
      setError(e instanceof ApiError ? e.detail : "Recherche impossible");
    } finally {
      setSearching(false);
    }
  }, [selectedId, coords]);

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
                  : "/map") as Href
              )
            }
          />
          <Button label="Retour" variant="ghost" onPress={() => router.back()} />
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

      {selected ? (
        <Body>Recherche pour : {selected.nom}</Body>
      ) : null}

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
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
});
