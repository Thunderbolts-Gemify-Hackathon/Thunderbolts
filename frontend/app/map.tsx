import { Feather } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  useWindowDimensions,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { WebView } from "react-native-webview";

import { ApiError } from "@/api/http";
import {
  findNearbyMarket,
  pickSafest,
  type MarketMatch,
} from "@/api/market";
import { QUARTIER_COORDS } from "@/api/onboarding";
import { listIngredients, type Ingredient } from "@/api/stock";
import { buildMarketMapHtml } from "@/lib/mapHtml";
import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { MarketCard } from "@/ui/MarketCard";
import { colors, radius, space, type } from "@/theme";

type SortMode = "securite" | "distance" | "prix";

const SORT_OPTIONS: { value: SortMode; label: string }[] = [
  { value: "securite", label: "Plus sûr" },
  { value: "distance", label: "Plus proche" },
  { value: "prix", label: "Moins cher" },
];

const SECURITE_FILTERS: { value: string; label: string; color: keyof typeof colors }[] = [
  { value: "sur", label: "Sûr", color: "ok" },
  { value: "prudence", label: "Prudence", color: "accent" },
  { value: "a_eviter", label: "À éviter", color: "danger" },
];

const GUTTER = space.lg;

export default function MapScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ ingredientId?: string }>();
  const { session } = useSession();
  const { data } = useOnboarding();
  const token = session?.apiToken;
  const { width: screenWidth } = useWindowDimensions();
  const webviewRef = useRef<WebView>(null);
  const carouselRef = useRef<FlatList<MarketMatch>>(null);

  const quartier = data.localisation.quartier;
  const coords =
    session?.localisationLat != null && session?.localisationLon != null
      ? { lat: session.localisationLat, lon: session.localisationLon }
      : quartier
        ? QUARTIER_COORDS[quartier]
        : null;
  const prefId = typeof params.ingredientId === "string" ? params.ingredientId : null;

  const [catalog, setCatalog] = useState<Ingredient[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(prefId);
  const [query, setQuery] = useState("");
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [sortMode, setSortMode] = useState<SortMode>("securite");
  const [hiddenSecurities, setHiddenSecurities] = useState<string[]>([]);
  const [matches, setMatches] = useState<MarketMatch[]>([]);
  const [selectedPdvId, setSelectedPdvId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedIngredient = catalog.find((i) => i.id === selectedId) ?? null;
  const recommended = useMemo(() => pickSafest(matches), [matches]);

  const sortedMatches = useMemo(() => {
    const list = [...matches];
    if (sortMode === "distance") {
      list.sort((a, b) => (a.itineraire?.distance ?? Infinity) - (b.itineraire?.distance ?? Infinity));
    } else if (sortMode === "prix") {
      list.sort((a, b) => a.prix - b.prix);
    }
    return list;
  }, [matches, sortMode]);

  const cardWidth = screenWidth - GUTTER * 2;

  const search = useCallback(async () => {
    if (!selectedId || !coords) {
      setError(coords ? "Choisis un ingrédient." : "Quartier manquant. Termine l'onboarding localisation.");
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

  const suggestions = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.trim().toLowerCase();
    return catalog.filter((i) => i.nom.toLowerCase().includes(q)).slice(0, 6);
  }, [query, catalog]);

  const focusPoint = (id: string) => {
    setSelectedPdvId(id);
    webviewRef.current?.injectJavaScript(`window.focusPoint(${JSON.stringify(id)}); true;`);
  };

  const onCardIndexChange = (offsetX: number) => {
    const index = Math.round(offsetX / (cardWidth + space.sm));
    const match = sortedMatches[Math.max(0, Math.min(index, sortedMatches.length - 1))];
    if (match) focusPoint(match.point_de_vente.id);
  };

  const toggleSecurite = (value: string) => {
    const next = hiddenSecurities.includes(value)
      ? hiddenSecurities.filter((v) => v !== value)
      : [...hiddenSecurities, value];
    setHiddenSecurities(next);
    webviewRef.current?.injectJavaScript(`window.setHiddenSecurities(${JSON.stringify(next)}); true;`);
  };

  const recenter = () => {
    webviewRef.current?.injectJavaScript("window.recenterHome(); true;");
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={styles.mapArea}>
        {coords && matches.length > 0 ? (
          <WebView
            ref={webviewRef}
            originWhitelist={["*"]}
            source={{ html }}
            style={styles.map}
            onMessage={(ev) => {
              try {
                const msg = JSON.parse(ev.nativeEvent.data) as { type?: string; id?: string };
                if (msg.type === "select" && msg.id) {
                  setSelectedPdvId(msg.id);
                  const idx = sortedMatches.findIndex((m) => m.point_de_vente.id === msg.id);
                  if (idx >= 0) carouselRef.current?.scrollToIndex({ index: idx, animated: true });
                }
              } catch {
                /* ignore */
              }
            }}
          />
        ) : (
          <View style={styles.mapPlaceholder}>
            {loading || searching ? (
              <ActivityIndicator color={colors.brand} />
            ) : (
              <Text style={styles.placeholderText}>
                {error ?? "Choisis un ingrédient pour voir les marchés."}
              </Text>
            )}
          </View>
        )}

        <View style={styles.topOverlay}>
          <View style={styles.topRow}>
            <Pressable onPress={() => router.back()} style={styles.roundBtn} hitSlop={8}>
              <Feather name="arrow-left" size={20} color={colors.ink} />
            </Pressable>
            <View style={styles.searchBox}>
              <Feather name="search" size={16} color={colors.muted} />
              <TextInput
                value={query}
                onChangeText={(t) => {
                  setQuery(t);
                  setSuggestionsOpen(true);
                }}
                onFocus={() => setSuggestionsOpen(true)}
                placeholder={selectedIngredient ? selectedIngredient.nom : "Chercher un ingrédient…"}
                placeholderTextColor={colors.muted}
                style={styles.searchInput}
              />
            </View>
          </View>

          {suggestionsOpen && suggestions.length > 0 ? (
            <View style={styles.suggestions}>
              {suggestions.map((ing) => (
                <Pressable
                  key={ing.id}
                  onPress={() => {
                    setSelectedId(ing.id);
                    setQuery("");
                    setSuggestionsOpen(false);
                  }}
                  style={styles.suggestionRow}
                >
                  <Text style={styles.suggestionText}>{ing.nom}</Text>
                </Pressable>
              ))}
            </View>
          ) : null}

          <View style={styles.sortRow}>
            {SORT_OPTIONS.map((opt) => {
              const active = opt.value === sortMode;
              return (
                <Pressable
                  key={opt.value}
                  onPress={() => setSortMode(opt.value)}
                  style={[styles.sortChip, active && styles.sortChipActive]}
                >
                  <Text style={[styles.sortChipText, active && styles.sortChipTextActive]}>
                    {opt.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        <Pressable onPress={recenter} style={styles.recenterBtn} hitSlop={8}>
          <Feather name="crosshair" size={20} color={colors.brand} />
        </Pressable>
      </View>

      <View style={styles.bottomArea}>
        <View style={styles.legendRow}>
          {SECURITE_FILTERS.map((f) => {
            const active = !hiddenSecurities.includes(f.value);
            return (
              <Pressable key={f.value} onPress={() => toggleSecurite(f.value)} style={styles.legendItem}>
                <View
                  style={[
                    styles.legendDot,
                    { backgroundColor: colors[f.color] },
                    !active && styles.legendDotOff,
                  ]}
                />
                <Text style={[styles.legendLabel, !active && styles.legendLabelOff]}>{f.label}</Text>
              </Pressable>
            );
          })}
        </View>

        {error && matches.length > 0 ? <Text style={styles.error}>{error}</Text> : null}

        {sortedMatches.length > 0 ? (
          <FlatList
            ref={carouselRef}
            data={sortedMatches}
            keyExtractor={(m) => m.point_de_vente.id}
            horizontal
            pagingEnabled={false}
            snapToInterval={cardWidth + space.sm}
            decelerationRate="fast"
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: GUTTER, gap: space.sm }}
            onMomentumScrollEnd={(ev) => onCardIndexChange(ev.nativeEvent.contentOffset.x)}
            getItemLayout={(_, index) => ({
              length: cardWidth + space.sm,
              offset: (cardWidth + space.sm) * index,
              index,
            })}
            renderItem={({ item }) => (
              <MarketCard
                match={item}
                recommended={item.point_de_vente.id === recommended?.point_de_vente.id}
                width={cardWidth}
              />
            )}
          />
        ) : !loading && !searching ? (
          <View style={styles.emptyCarousel}>
            <Text style={styles.placeholderText}>
              {error ?? "Aucun marché à afficher pour cet ingrédient."}
            </Text>
          </View>
        ) : null}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  mapArea: { flex: 1 },
  map: { flex: 1, backgroundColor: colors.brandSoft },
  mapPlaceholder: {
    flex: 1,
    backgroundColor: colors.brandSoft,
    alignItems: "center",
    justifyContent: "center",
    padding: space.lg,
  },
  placeholderText: { color: colors.muted, fontSize: type.body, textAlign: "center" },
  topOverlay: {
    position: "absolute",
    top: space.sm,
    left: 0,
    right: 0,
    gap: space.sm,
    paddingHorizontal: space.md,
  },
  topRow: { flexDirection: "row", alignItems: "center", gap: space.sm },
  roundBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOpacity: 0.12,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 3 },
    elevation: 6,
  },
  searchBox: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: colors.surface,
    borderRadius: 999,
    paddingHorizontal: space.md,
    height: 42,
    shadowColor: "#000",
    shadowOpacity: 0.12,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 3 },
    elevation: 6,
  },
  searchInput: { flex: 1, color: colors.ink, fontSize: type.body },
  suggestions: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingVertical: 4,
    shadowColor: "#000",
    shadowOpacity: 0.12,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  suggestionRow: { paddingHorizontal: space.md, paddingVertical: space.sm },
  suggestionText: { color: colors.ink, fontSize: type.body },
  sortRow: { flexDirection: "row", gap: 8 },
  sortChip: {
    backgroundColor: colors.surface,
    borderRadius: 999,
    paddingHorizontal: space.md,
    paddingVertical: 8,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 4,
  },
  sortChipActive: { backgroundColor: colors.brand },
  sortChipText: { fontSize: type.small, color: colors.ink, fontWeight: "600" },
  sortChipTextActive: { color: "#F7F3EA" },
  recenterBtn: {
    position: "absolute",
    right: space.md,
    bottom: space.md,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOpacity: 0.14,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  bottomArea: {
    backgroundColor: colors.bg,
    paddingTop: space.sm,
    paddingBottom: space.md,
    gap: space.sm,
  },
  legendRow: { flexDirection: "row", gap: space.md, paddingHorizontal: GUTTER },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 6 },
  legendDot: { width: 9, height: 9, borderRadius: 4.5 },
  legendDotOff: { opacity: 0.25 },
  legendLabel: { fontSize: type.small, color: colors.muted, fontWeight: "600" },
  legendLabelOff: { textDecorationLine: "line-through", opacity: 0.5 },
  emptyCarousel: { paddingHorizontal: GUTTER, paddingVertical: space.lg },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    marginHorizontal: GUTTER,
    padding: space.sm,
    borderRadius: 10,
    fontSize: type.small,
  },
});
