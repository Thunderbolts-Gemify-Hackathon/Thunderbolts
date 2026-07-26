import { Feather } from "@expo/vector-icons";
import { type Href, useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { ApiError } from "@/api/http";
import { annulerRepas, validerRepas } from "@/api/planning";
import { getRecette } from "@/api/recettes";
import type { Recette } from "@/api/repas";
import { useFavori } from "@/lib/favorites";
import {
  cacheRecette,
  getCachedContext,
  getCachedRecette,
} from "@/lib/recipeCache";
import { recetteVisual } from "@/lib/recipeVisual";
import { useEtapesRecette } from "@/lib/useEtapesRecette";
import { useSession } from "@/session/SessionContext";
import { colors, radius, space, type } from "@/theme";

type Tab = "ingredients" | "instructions";

export default function RecetteDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { session } = useSession();
  const cached = useMemo(() => (id ? getCachedRecette(id) : undefined), [id]);
  const [recette, setRecette] = useState<Recette | undefined>(cached);
  const [fetching, setFetching] = useState(!cached && Boolean(id));
  const context = useMemo(() => (id ? getCachedContext(id) : undefined), [id]);
  const { favori, toggle } = useFavori(id ?? "");

  const [tab, setTab] = useState<Tab>("ingredients");
  const [statut, setStatut] = useState(context?.statut ?? null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const profilId = session?.profilId;
  const token = session?.apiToken;
  const {
    etapes,
    loading: etapesLoading,
    error: etapesError,
    fetchEtapes,
  } = useEtapesRecette(recette?.id, profilId, token, false);

  useEffect(() => {
    if (!id || cached) return;
    let alive = true;
    setFetching(true);
    getRecette(id, token)
      .then((r) => {
        if (!alive) return;
        const mapped = r as unknown as Recette;
        cacheRecette(mapped);
        setRecette(mapped);
      })
      .catch((e) => {
        if (alive) {
          setError(e instanceof ApiError ? e.detail : "Recette introuvable");
        }
      })
      .finally(() => {
        if (alive) setFetching(false);
      });
    return () => {
      alive = false;
    };
  }, [id, cached, token]);

  if (fetching) {
    return (
      <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
        <View style={styles.notFound}>
          <ActivityIndicator color={colors.brand} />
        </View>
      </SafeAreaView>
    );
  }

  if (!recette) {
    return (
      <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
        <View style={styles.notFound}>
          <Text style={styles.notFoundText}>
            {error || "Recette indisponible. Reviens depuis le planning pour l'ouvrir."}
          </Text>
          <Pressable onPress={() => router.back()} style={styles.notFoundBtn}>
            <Text style={styles.notFoundBtnText}>Retour</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  const visual = recetteVisual(recette);
  const canToggle = Boolean(context?.repasId && token);
  const consomme = statut === "consomme";

  const onToggleValidation = async () => {
    if (!context?.repasId || !token) return;
    setBusy(true);
    setError(null);
    try {
      if (consomme) {
        const r = await annulerRepas(context.repasId, token);
        setStatut(r.statut);
      } else {
        const r = await validerRepas(context.repasId, token);
        setStatut(r.statut);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Action impossible");
    } finally {
      setBusy(false);
    }
  };

  const voirInstructions = () => {
    setTab("instructions");
    if (!etapes) void fetchEtapes();
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: visual.bg }]} edges={["top"]}>
      <View style={styles.topBar}>
        <Pressable onPress={() => router.back()} hitSlop={8} style={styles.iconBtn}>
          <Feather name="arrow-left" size={22} color={colors.ink} />
        </Pressable>
        <Pressable onPress={() => void toggle()} hitSlop={8} style={styles.iconBtn}>
          <Feather
            name={favori ? "heart" : "heart"}
            size={22}
            color={favori ? colors.accent : colors.ink}
          />
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>{recette.nom}</Text>
        <Text style={styles.meta}>
          {recette.duree_minutes ? `${recette.duree_minutes} min · ` : ""}
          {Math.round(recette.kcal_total)} kcal
        </Text>

        <View style={styles.tabs}>
          <Pressable
            onPress={() => setTab("ingredients")}
            style={[styles.tab, tab === "ingredients" && styles.tabActive]}
          >
            <Text style={[styles.tabText, tab === "ingredients" && styles.tabTextActive]}>
              Ingrédients
            </Text>
          </Pressable>
          <Pressable
            onPress={voirInstructions}
            style={[styles.tab, tab === "instructions" && styles.tabActive]}
          >
            <Text style={[styles.tabText, tab === "instructions" && styles.tabTextActive]}>
              Instructions
            </Text>
          </Pressable>
        </View>

        {tab === "ingredients" ? (
          <View style={styles.card}>
            {(recette.ingredients || []).map((line, i) => (
              <Text key={i} style={styles.line}>
                {line.ingredient?.nom ?? "?"} — {line.poids_requis} {line.unite}
              </Text>
            ))}
          </View>
        ) : (
          <View style={styles.card}>
            {etapesLoading ? <ActivityIndicator color={colors.brand} /> : null}
            {etapesError ? <Text style={styles.error}>{etapesError}</Text> : null}
            {etapes?.map((e) => (
              <View key={e.numero} style={styles.step}>
                <Text style={styles.stepNum}>Étape {e.numero}</Text>
                <Text style={styles.line}>{e.titre}</Text>
              </View>
            ))}
            {!etapes && !etapesLoading ? (
              <Text style={styles.line}>{recette.instructions || "Pas d'instructions."}</Text>
            ) : null}
          </View>
        )}

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <Pressable
          style={styles.cookBtn}
          onPress={() => router.push(`/cuisiner/${recette.id}` as Href)}
        >
          <Text style={styles.cookBtnText}>Mode cuisine</Text>
        </Pressable>

        {canToggle ? (
          <Pressable
            style={[styles.cookBtn, styles.validateBtn]}
            onPress={() => void onToggleValidation()}
            disabled={busy}
          >
            <Text style={styles.cookBtnText}>
              {consomme ? "Annuler validation" : "Marquer cuisiné"}
            </Text>
          </Pressable>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  topBar: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
  },
  iconBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
  content: { padding: space.lg, gap: space.md, paddingBottom: 40 },
  title: { fontSize: 26, fontWeight: "700", color: colors.ink },
  meta: { fontSize: type.small, color: colors.muted },
  tabs: { flexDirection: "row", gap: space.sm },
  tab: {
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
    borderRadius: radius.sm,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
  },
  tabActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  tabText: { color: colors.ink, fontWeight: "600" },
  tabTextActive: { color: "#F7F3EA" },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: space.md,
    gap: space.sm,
  },
  line: { fontSize: type.body, color: colors.ink },
  step: { gap: 2 },
  stepNum: { fontSize: type.small, fontWeight: "700", color: colors.muted },
  cookBtn: {
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    padding: space.md,
    alignItems: "center",
  },
  validateBtn: { backgroundColor: colors.accent },
  cookBtnText: { color: "#fff", fontWeight: "700" },
  error: { color: colors.danger },
  notFound: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: space.lg,
    gap: space.md,
  },
  notFoundText: { textAlign: "center", color: colors.ink, fontSize: type.body },
  notFoundBtn: {
    backgroundColor: colors.brand,
    paddingHorizontal: space.lg,
    paddingVertical: space.sm,
    borderRadius: radius.sm,
  },
  notFoundBtnText: { color: "#fff", fontWeight: "700" },
});
