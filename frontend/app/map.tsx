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
import { findNearbyMarket, pickSafest, type MarketMatch } from "@/api/market";
import { QUARTIER_COORDS } from "@/api/onboarding";
import { listIngredients, type Ingredient } from "@/api/stock";
import {
  buildMarketMapShellHtml,
  matchesToMapPoints,
} from "@/lib/mapHtml";
import { formatDistanceM, formatDureeS } from "@/lib/travelEstimate";
import { loadActiveTrip } from "@/lib/tripStore";
import type { OneTripResult } from "@/api/marketPanier";
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

const SECURITE_FILTERS: {
  value: string;
  label: string;
  color: keyof typeof colors;
}[] = [
  { value: "sur", label: "Sûr", color: "ok" },
  { value: "prudence", label: "Prudence", color: "accent" },
  { value: "a_eviter", label: "À éviter", color: "danger" },
];

const RAYON_OPTIONS = [5, 15, 30];

const GUTTER = space.lg;

export default function MapScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ ingredientId?: string; mode?: string }>();
  const tripMode = params.mode === "trip";
  const { session } = useSession();
  const { data } = useOnboarding();
  const token = session?.apiToken;
  const { width: screenWidth } = useWindowDimensions();
  const webviewRef = useRef<WebView>(null);
  const carouselRef = useRef<FlatList<MarketMatch>>(null);

  const quartier = data.localisation.quartier;
  const lat = session?.localisationLat;
  const lon = session?.localisationLon;
  const coords = useMemo(() => {
    if (lat != null && lon != null) return { lat, lon };
    return quartier ? QUARTIER_COORDS[quartier] : null;
  }, [lat, lon, quartier]);
  const prefId =
    typeof params.ingredientId === "string" ? params.ingredientId : null;

  const [catalog, setCatalog] = useState<Ingredient[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(prefId);
  const [query, setQuery] = useState("");
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [sortMode, setSortMode] = useState<SortMode>("securite");
  const [hiddenSecurities, setHiddenSecurities] = useState<string[]>([]);
  const [rayonKm, setRayonKm] = useState(15);
  const [matches, setMatches] = useState<MarketMatch[]>([]);
  const [selectedPdvId, setSelectedPdvId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [routeInfo, setRouteInfo] = useState<{
    id: string;
    distanceM: number;
    durationS: number;
  } | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [trip, setTrip] = useState<OneTripResult | null>(null);

  const selectedIngredient = catalog.find((i) => i.id === selectedId) ?? null;
  const recommended = useMemo(() => pickSafest(matches), [matches]);

  const sortedMatches = useMemo(() => {
    const list = [...matches];
    if (sortMode === "distance") {
      list.sort(
        (a, b) =>
          (a.itineraire?.distance ?? Infinity) -
          (b.itineraire?.distance ?? Infinity),
      );
    } else if (sortMode === "prix") {
      list.sort((a, b) => a.prix - b.prix);
    }
    return list;
  }, [matches, sortMode]);

  const cardWidth = screenWidth - GUTTER * 2;

  const search = useCallback(async () => {
    if (!selectedId || !coords) {
      setError(
        coords
          ? "Choisis un ingrédient."
          : "Quartier manquant. Termine l'onboarding localisation.",
      );
      return;
    }
    setSearching(true);
    setError(null);
    try {
      const rows = await findNearbyMarket(
        selectedId,
        coords.lat,
        coords.lon,
        rayonKm,
      );
      setMatches(rows);
      const best = pickSafest(rows);
      setSelectedPdvId(best?.point_de_vente.id ?? null);
      if (rows.length === 0)
        setError(`Aucun point de vente dans un rayon de ${rayonKm} km.`);
    } catch (e) {
      setMatches([]);
      setError(e instanceof ApiError ? e.detail : "Carte indisponible");
    } finally {
      setSearching(false);
    }
  }, [selectedId, coords, rayonKm]);

  useEffect(() => {
    if (tripMode) {
      loadActiveTrip()
        .then((t) => {
          setTrip(t);
          if (!t) setError("Aucun trajet actif. Recalcule depuis Courses.");
          else setSelectedPdvId(t.stops[0]?.point_de_vente.id ?? null);
        })
        .finally(() => setLoading(false));
      return;
    }
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
  }, [token, prefId, tripMode]);

  useEffect(() => {
    if (tripMode) return;
    if (!loading && selectedId && coords) void search();
  }, [loading, selectedId, coords, search, tripMode]);

  // HTML stable : ne dépend que de la position. Les marchés arrivent ensuite
  // via injectJavaScript (pas de reload Leaflet à chaque recherche).
  const shellHtml = useMemo(() => {
    if (!coords) return "";
    return buildMarketMapShellHtml({
      homeLat: coords.lat,
      homeLon: coords.lon,
      homeLabel: quartier ? `Chez toi (${quartier})` : "Chez toi",
      rayonKm: 15,
    });
  }, [coords, quartier]);

  useEffect(() => {
    setMapReady(false);
  }, [shellHtml]);

  const suggestions = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.trim().toLowerCase();
    return catalog.filter((i) => i.nom.toLowerCase().includes(q)).slice(0, 6);
  }, [query, catalog]);

  const pushPointsToMap = useCallback(() => {
    if (!mapReady || !webviewRef.current) return;
    if (tripMode && trip) {
      const stops = trip.stops.map((s, i) => ({
        id: s.point_de_vente.id,
        nom: s.point_de_vente.nom,
        lat: s.point_de_vente.latitude,
        lon: s.point_de_vente.longitude,
        order: i + 1,
        label: s.items.map((it) => it.ingredient_nom).join(", "),
      }));
      webviewRef.current.injectJavaScript(
        `window.setTripStops(${JSON.stringify(stops)}); true;`
      );
      return;
    }
    const points = matchesToMapPoints(
      matches,
      recommended?.point_de_vente.id ?? null
    );
    const focusId = recommended?.point_de_vente.id ?? points[0]?.id ?? null;
    webviewRef.current.injectJavaScript(
      `window.setPoints(${JSON.stringify(points)}, ${JSON.stringify(focusId)}); true;`
    );
  }, [mapReady, matches, recommended, tripMode, trip]);

  useEffect(() => {
    pushPointsToMap();
  }, [pushPointsToMap]);

  useEffect(() => {
    if (!mapReady || !webviewRef.current) return;
    webviewRef.current.injectJavaScript(
      `window.setRayon(${JSON.stringify(rayonKm)}); true;`
    );
  }, [mapReady, rayonKm]);

  const focusPoint = (id: string) => {
    setSelectedPdvId(id);
    setRouteInfo(null);
    webviewRef.current?.injectJavaScript(
      `window.focusPoint(${JSON.stringify(id)}); true;`
    );
  };

  const onCardIndexChange = (offsetX: number) => {
    const index = Math.round(offsetX / (cardWidth + space.sm));
    const match =
      sortedMatches[Math.max(0, Math.min(index, sortedMatches.length - 1))];
    if (match) focusPoint(match.point_de_vente.id);
  };

  const toggleSecurite = (value: string) => {
    const next = hiddenSecurities.includes(value)
      ? hiddenSecurities.filter((v) => v !== value)
      : [...hiddenSecurities, value];
    setHiddenSecurities(next);
    webviewRef.current?.injectJavaScript(
      `window.setHiddenSecurities(${JSON.stringify(next)}); true;`,
    );
  };

  const recenter = () => {
    webviewRef.current?.injectJavaScript("window.recenterHome(); true;");
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={styles.mapArea}>
        {coords && shellHtml ? (
          <>
            <WebView
              ref={webviewRef}
              originWhitelist={["*"]}
              source={{ html: shellHtml }}
              style={styles.map}
              // Cache WebView + ne pas recharger pour rien
              cacheEnabled
              javaScriptEnabled
              domStorageEnabled
              setSupportMultipleWindows={false}
              onLoadEnd={() => {
                // filet si le postMessage "ready" arrive trop tôt
                setTimeout(() => setMapReady(true), 50);
              }}
              onMessage={(ev) => {
                try {
                  const msg = JSON.parse(ev.nativeEvent.data) as {
                    type?: string;
                    id?: string;
                    distanceM?: number;
                    durationS?: number;
                  };
                  if (msg.type === "ready") {
                    setMapReady(true);
                  } else if (msg.type === "select" && msg.id) {
                    setSelectedPdvId(msg.id);
                    setRouteInfo(null);
                    const idx = sortedMatches.findIndex(
                      (m) => m.point_de_vente.id === msg.id,
                    );
                    if (idx >= 0)
                      carouselRef.current?.scrollToIndex({
                        index: idx,
                        animated: true,
                      });
                  } else if (
                    msg.type === "route" &&
                    msg.id &&
                    msg.distanceM != null &&
                    msg.durationS != null
                  ) {
                    setRouteInfo({
                      id: msg.id,
                      distanceM: msg.distanceM,
                      durationS: msg.durationS,
                    });
                  }
                } catch {
                  /* ignore */
                }
              }}
            />
            {(loading || searching || !mapReady) && (
              <View style={styles.mapLoadingOverlay} pointerEvents="none">
                <ActivityIndicator color={colors.brand} />
              </View>
            )}
          </>
        ) : (
          <View style={styles.mapPlaceholder}>
            {loading ? (
              <ActivityIndicator color={colors.brand} />
            ) : (
              <Text style={styles.placeholderText}>
                {error ?? "Quartier manquant. Termine l'onboarding localisation."}
              </Text>
            )}
          </View>
        )}

        <View style={styles.topOverlay}>
          <View style={styles.topRow}>
            <Pressable
              onPress={() => router.back()}
              style={styles.roundBtn}
              hitSlop={8}
            >
              <Feather name="arrow-left" size={20} color={colors.ink} />
            </Pressable>
            {tripMode ? (
              <View style={[styles.searchBox, { flex: 1 }]}>
                <Feather name="navigation" size={16} color={colors.accent} />
                <Text style={styles.searchInput} numberOfLines={1}>
                  {trip
                    ? `${trip.nb_arrets} arrêt(s) · ${trip.distance_totale_km} km`
                    : "Trajet courses"}
                </Text>
              </View>
            ) : (
              <View style={styles.searchBox}>
                <Feather name="search" size={16} color={colors.muted} />
                <TextInput
                  value={query}
                  onChangeText={(t) => {
                    setQuery(t);
                    setSuggestionsOpen(true);
                  }}
                  onFocus={() => setSuggestionsOpen(true)}
                  placeholder={
                    selectedIngredient
                      ? selectedIngredient.nom
                      : "Chercher un ingrédient…"
                  }
                  placeholderTextColor={colors.muted}
                  style={styles.searchInput}
                />
              </View>
            )}
          </View>

          {!tripMode && suggestionsOpen && suggestions.length > 0 ? (
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

          {!tripMode ? (
            <>
              <View style={styles.sortRow}>
                {SORT_OPTIONS.map((opt) => {
                  const active = opt.value === sortMode;
                  return (
                    <Pressable
                      key={opt.value}
                      onPress={() => setSortMode(opt.value)}
                      style={[styles.sortChip, active && styles.sortChipActive]}
                    >
                      <Text
                        style={[
                          styles.sortChipText,
                          active && styles.sortChipTextActive,
                        ]}
                      >
                        {opt.label}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>

              <View style={styles.sortRow}>
                <View style={styles.rayonLabel}>
                  <Feather name="circle" size={12} color={colors.muted} />
                  <Text style={styles.rayonLabelText}>Zone :</Text>
                </View>
                {RAYON_OPTIONS.map((km) => {
                  const active = km === rayonKm;
                  return (
                    <Pressable
                      key={km}
                      onPress={() => setRayonKm(km)}
                      style={[styles.sortChip, active && styles.sortChipActive]}
                    >
                      <Text
                        style={[
                          styles.sortChipText,
                          active && styles.sortChipTextActive,
                        ]}
                      >
                        {km} km
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
            </>
          ) : trip ? (
            <Text style={styles.tripHint}>{trip.message}</Text>
          ) : null}
        </View>

        {routeInfo &&
        (routeInfo.id === selectedPdvId || routeInfo.id === "trip") ? (
          <View style={styles.routeBadge}>
            <Feather name="map-pin" size={13} color={colors.brand} />
            <Text style={styles.routeBadgeText}>
              Trajet réel : {formatDistanceM(routeInfo.distanceM)} ·{" "}
              {formatDureeS(routeInfo.durationS)}
            </Text>
          </View>
        ) : null}

        <Pressable onPress={recenter} style={styles.recenterBtn} hitSlop={8}>
          <Feather name="crosshair" size={20} color={colors.brand} />
        </Pressable>
      </View>

      <View style={styles.bottomArea}>
        {tripMode && trip ? (
          <>
            <Pressable
              style={styles.sortieCta}
              onPress={() => router.push("/sortie-marche" as never)}
            >
              <Feather name="shopping-bag" size={18} color="#F7F3EA" />
              <Text style={styles.sortieCtaText}>Lancer la sortie marché</Text>
            </Pressable>
            {trip.stops.map((s, i) => (
              <Pressable
                key={s.point_de_vente.id}
                style={[
                  styles.tripStopCard,
                  selectedPdvId === s.point_de_vente.id && styles.tripStopActive,
                ]}
                onPress={() => {
                  setSelectedPdvId(s.point_de_vente.id);
                  webviewRef.current?.injectJavaScript(
                    `window.focusPoint(${JSON.stringify(s.point_de_vente.id)}); true;`
                  );
                }}
              >
                <Text style={styles.tripStopTitle}>
                  #{i + 1} {s.point_de_vente.nom}
                </Text>
                <Text style={styles.tripStopMeta}>
                  {s.items.map((it) => it.ingredient_nom).join(", ")} · ~
                  {Math.round(s.cout_estime)} Ar
                </Text>
              </Pressable>
            ))}
          </>
        ) : (
          <>
            <View style={styles.legendRow}>
              {SECURITE_FILTERS.map((f) => {
                const active = !hiddenSecurities.includes(f.value);
                return (
                  <Pressable
                    key={f.value}
                    onPress={() => toggleSecurite(f.value)}
                    style={styles.legendItem}
                  >
                    <View
                      style={[
                        styles.legendDot,
                        { backgroundColor: colors[f.color] },
                        !active && styles.legendDotOff,
                      ]}
                    />
                    <Text
                      style={[
                        styles.legendLabel,
                        !active && styles.legendLabelOff,
                      ]}
                    >
                      {f.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            {error && matches.length > 0 ? (
              <Text style={styles.error}>{error}</Text>
            ) : null}

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
                contentContainerStyle={{
                  paddingHorizontal: GUTTER,
                  gap: space.sm,
                }}
                onMomentumScrollEnd={(ev) =>
                  onCardIndexChange(ev.nativeEvent.contentOffset.x)
                }
                getItemLayout={(_, index) => ({
                  length: cardWidth + space.sm,
                  offset: (cardWidth + space.sm) * index,
                  index,
                })}
                renderItem={({ item }) => (
                  <MarketCard
                    match={item}
                    recommended={
                      item.point_de_vente.id === recommended?.point_de_vente.id
                    }
                    width={cardWidth}
                    onVoirTrajet={() => focusPoint(item.point_de_vente.id)}
                    real={
                      routeInfo && routeInfo.id === item.point_de_vente.id
                        ? {
                            distanceM: routeInfo.distanceM,
                            durationS: routeInfo.durationS,
                          }
                        : null
                    }
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
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  mapArea: { flex: 1 },
  map: { flex: 1, backgroundColor: colors.brandSoft },
  mapLoadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(243,239,230,0.35)",
  },
  mapPlaceholder: {
    flex: 1,
    backgroundColor: colors.brandSoft,
    alignItems: "center",
    justifyContent: "center",
    padding: space.lg,
  },
  placeholderText: {
    color: colors.muted,
    fontSize: type.body,
    textAlign: "center",
  },
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
  sortRow: { flexDirection: "row", gap: 8, alignItems: "center" },
  rayonLabel: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginRight: 2,
  },
  rayonLabelText: {
    fontSize: type.small,
    color: colors.muted,
    fontWeight: "600",
  },
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
  routeBadge: {
    position: "absolute",
    left: space.md,
    bottom: space.md,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: colors.surface,
    borderRadius: 999,
    paddingHorizontal: space.md,
    paddingVertical: 8,
    maxWidth: "62%",
    shadowColor: "#000",
    shadowOpacity: 0.14,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  routeBadgeText: {
    fontSize: type.small,
    color: colors.ink,
    fontWeight: "600",
    flexShrink: 1,
  },
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
  tripHint: {
    color: colors.ink,
    fontSize: type.small,
    fontWeight: "600",
    backgroundColor: colors.surface,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
    borderRadius: radius.md,
    overflow: "hidden",
  },
  sortieCta: {
    marginHorizontal: GUTTER,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    paddingVertical: 12,
  },
  sortieCtaText: { color: "#F7F3EA", fontWeight: "700", fontSize: type.body },
  tripStopCard: {
    marginHorizontal: GUTTER,
    padding: space.md,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: "transparent",
  },
  tripStopActive: { borderColor: colors.accent },
  tripStopTitle: { fontWeight: "700", color: colors.brand, fontSize: type.body },
  tripStopMeta: { fontSize: type.small, color: colors.muted, marginTop: 4 },
});
