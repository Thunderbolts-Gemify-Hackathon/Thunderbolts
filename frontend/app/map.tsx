import { useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { WebView } from "react-native-webview";

import { ApiError } from "@/api/http";
import {
  findNearbyMarket,
  formatAr,
  pickSafest,
  type MarketMatch,
} from "@/api/market";
import { QUARTIER_COORDS } from "@/api/onboarding";
import { listIngredients, type Ingredient } from "@/api/stock";
import { buildMarketMapHtml } from "@/lib/mapHtml";
import { speak } from "@/lib/speech";
import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

export default function MapScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ ingredientId?: string }>();
  const { session } = useSession();
  const { data } = useOnboarding();
  const token = session?.apiToken;

  const quartier = data.localisation.quartier;
  const coords = quartier ? QUARTIER_COORDS[quartier] : null;
  const prefId =
    typeof params.ingredientId === "string" ? params.ingredientId : null;

  const [catalog, setCatalog] = useState<Ingredient[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(prefId);
  const [matches, setMatches] = useState<MarketMatch[]>([]);
  const [selectedPdvId, setSelectedPdvId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recommended = useMemo(() => pickSafest(matches), [matches]);
  const selected =
    matches.find((m) => m.point_de_vente.id === selectedPdvId) ?? recommended;

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
      const best = pickSafest(rows);
      setSelectedPdvId(best?.point_de_vente.id ?? null);
      if (rows.length === 0) setError("Aucun point de vente dans le rayon.");
    } catch (e) {
      setMatches([]);
      setError(e instanceof ApiError ? e.detail : "Carte indisponible");
    } finally {
      setSearching(false);
    }
  }, [selectedId, coords]);

  useEffect(() => {
    if (!token) {
      setError("Session invalide.");
      setLoading(false);
      return;
    }
    listIngredients(token)
      .then((ings) => {
        setCatalog(ings);
        const next =
          (prefId && ings.some((i) => i.id === prefId) ? prefId : null) ??
          ings.find((i) => i.nom.toLowerCase() === "poulet")?.id ??
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
    if (!loading && selectedId && coords) void search();
  }, [loading, selectedId, coords, search]);

  const html = useMemo(() => {
    if (!coords) return "";
    return buildMarketMapHtml({
      homeLat: coords.lat,
      homeLon: coords.lon,
      homeLabel: quartier ? `Chez toi (${quartier})` : "Chez toi",
      matches,
      recommendedId: recommended?.point_de_vente.id ?? null,
    });
  }, [coords, quartier, matches, recommended]);

  const onSpeak = () => {
    if (!selected) return;
    const sec = selected.itineraire?.niveau_securite ?? "inconnu";
    const dist = selected.itineraire?.distance;
    const phrase = [
      `Pour cet ingredient, va a ${selected.point_de_vente.nom}.`,
      `Prix indicatif ${Math.round(selected.prix)} Ar.`,
      dist != null ? `Environ ${dist} km.` : "",
      sec === "a_eviter"
        ? "Attention, trajet a eviter."
        : sec === "prudence"
          ? "Trajet a faire avec prudence."
          : "Trajet sur.",
    ]
      .filter(Boolean)
      .join(" ");
    speak(phrase);
  };

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label={searching ? "Chargement…" : "Actualiser la carte"}
            onPress={() => void search()}
            disabled={searching || loading}
          />
          <Button
            label="Lire la directive"
            variant="ghost"
            onPress={onSpeak}
            disabled={!selected}
          />
          <Button label="Retour" variant="ghost" onPress={() => router.back()} />
        </View>
      }
    >
      <Title>Carte des marches</Title>
      <Body>
        OpenStreetMap + CARTO Voyager. KaliTao recommande le trajet plus safe
        (a eviter visible mais non prioritaire).
      </Body>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      <View style={styles.chips}>
        {catalog.slice(0, 10).map((ing) => {
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

      {coords && matches.length > 0 ? (
        <View style={styles.mapBox}>
          <WebView
            originWhitelist={["*"]}
            source={{ html }}
            style={styles.map}
            onMessage={(ev) => {
              try {
                const msg = JSON.parse(ev.nativeEvent.data) as {
                  type?: string;
                  id?: string;
                };
                if (msg.type === "select" && msg.id) setSelectedPdvId(msg.id);
              } catch {
                /* ignore */
              }
            }}
          />
        </View>
      ) : null}

      {selected ? (
        <View
          style={[
            styles.card,
            selected.deprioritise ? styles.cardWarn : styles.cardOk,
          ]}
        >
          <Text style={styles.cardLabel}>
            {selected.point_de_vente.id === recommended?.point_de_vente.id
              ? "Choix recommande"
              : "Point selectionne"}
          </Text>
          <Text style={styles.nom}>{selected.point_de_vente.nom}</Text>
          <Text style={styles.meta}>
            {formatAr(selected.prix)}
            {selected.itineraire
              ? ` · ${selected.itineraire.distance} km · ${selected.itineraire.niveau_securite}`
              : ""}
          </Text>
          {selected.deprioritise ? (
            <Text style={styles.warn}>Deprioritise (a eviter)</Text>
          ) : (
            <Text style={styles.ok}>Trajet acceptable</Text>
          )}
        </View>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  actions: { gap: space.sm },
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
  mapBox: {
    height: 340,
    borderRadius: radius.lg,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: colors.line,
  },
  map: { flex: 1, backgroundColor: colors.brandSoft },
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderRadius: radius.md,
    padding: space.md,
    gap: 4,
  },
  cardOk: { borderColor: colors.ok },
  cardWarn: { borderColor: colors.accent },
  cardLabel: {
    fontSize: type.label,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
  },
  nom: { fontSize: type.body, fontWeight: "700", color: colors.ink },
  meta: { fontSize: type.small, color: colors.muted },
  warn: { fontSize: type.small, color: colors.accent, fontWeight: "700" },
  ok: { fontSize: type.small, color: colors.ok, fontWeight: "700" },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
});
