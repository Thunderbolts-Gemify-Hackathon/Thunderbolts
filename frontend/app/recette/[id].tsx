import { Feather } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useMemo, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { getEtapesRecette } from "@/api/chat";
import { ApiError } from "@/api/http";
import { annulerRepas, validerRepas } from "@/api/planning";
import { useFavori } from "@/lib/favorites";
import { getCachedContext, getCachedRecette } from "@/lib/recipeCache";
import { recetteVisual } from "@/lib/recipeVisual";
import { useSession } from "@/session/SessionContext";
import { AiText } from "@/ui/Markdown";
import { colors, radius, space, type } from "@/theme";

type Tab = "ingredients" | "instructions";

export default function RecetteDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { session } = useSession();
  const recette = useMemo(() => (id ? getCachedRecette(id) : undefined), [id]);
  const context = useMemo(() => (id ? getCachedContext(id) : undefined), [id]);
  const { favori, toggle } = useFavori(id ?? "");

  const [tab, setTab] = useState<Tab>("ingredients");
  const [statut, setStatut] = useState(context?.statut ?? null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [etapes, setEtapes] = useState<string | null>(null);
  const [etapesLoading, setEtapesLoading] = useState(false);
  const [etapesError, setEtapesError] = useState<string | null>(null);

  if (!recette) {
    return (
      <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
        <View style={styles.notFound}>
          <Text style={styles.notFoundText}>
            Recette indisponible. Reviens depuis le planning pour l'ouvrir.
          </Text>
          <Pressable onPress={() => router.back()} style={styles.notFoundBtn}>
            <Text style={styles.notFoundBtnText}>Retour</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  const visual = recetteVisual(recette);
  const token = session?.apiToken;
  const profilId = session?.profilId;
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

  const demanderEtapes = async () => {
    if (!profilId || !token || etapesLoading) return;
    setTab("instructions");
    if (etapes) return;
    setEtapesLoading(true);
    setEtapesError(null);
    try {
      const res = await getEtapesRecette(profilId, token, recette.id);
      setEtapes(res.etapes);
    } catch (e) {
      setEtapesError(
        e instanceof ApiError ? e.detail : "Etapes indisponibles. Verifie Ollama / Gemma."
      );
    } finally {
      setEtapesLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={[styles.hero, { backgroundColor: visual.bg }]}>
        <View style={styles.heroTopRow}>
          <Pressable onPress={() => router.back()} style={styles.heroBtn} hitSlop={8}>
            <Feather name="arrow-left" size={20} color={colors.ink} />
          </Pressable>
          <Pressable onPress={() => void toggle()} style={styles.heroBtn} hitSlop={8}>
            <Feather name="heart" size={20} color={favori ? colors.danger : colors.ink} />
          </Pressable>
        </View>
        <Text style={styles.emoji}>{visual.emoji}</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.nom}>{recette.nom}</Text>
        <View style={styles.metaRow}>
          {recette.duree_minutes ? (
            <Text style={styles.meta}>{recette.duree_minutes} minutes</Text>
          ) : null}
          <Text style={styles.meta}>· {Math.round(recette.kcal_total)} kcal</Text>
        </View>

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
            onPress={() => void demanderEtapes()}
            style={[styles.tab, tab === "instructions" && styles.tabActive]}
          >
            <Text style={[styles.tabText, tab === "instructions" && styles.tabTextActive]}>
              Instructions
            </Text>
          </Pressable>
        </View>

        {tab === "ingredients" ? (
          <View style={styles.list}>
            {recette.ingredients.map((ligne) => (
              <View key={ligne.ingredient.id} style={styles.ingredientRow}>
                <Text style={styles.ingredientNom}>{ligne.ingredient.nom}</Text>
                <Text style={styles.ingredientQty}>
                  {ligne.poids_requis} {ligne.unite}
                </Text>
              </View>
            ))}
          </View>
        ) : (
          <View style={styles.list}>
            {etapesLoading ? (
              <View style={styles.etapesLoading}>
                <ActivityIndicator color={colors.brand} />
                <Text style={styles.meta}>Kaly Tao prépare les étapes…</Text>
              </View>
            ) : etapes ? (
              <AiText content={etapes} />
            ) : etapesError ? (
              <>
                <Text style={styles.error}>{etapesError}</Text>
                <Pressable onPress={() => void demanderEtapes()} hitSlop={8}>
                  <Text style={styles.retry}>Réessayer</Text>
                </Pressable>
              </>
            ) : recette.instructions ? (
              <Text style={styles.instructions}>{recette.instructions}</Text>
            ) : (
              <Text style={styles.instructions}>
                Appuie sur cet onglet pour demander les étapes détaillées à Kaly Tao.
              </Text>
            )}
          </View>
        )}

        {error ? <Text style={styles.error}>{error}</Text> : null}
      </ScrollView>

      <View style={styles.actionBar}>
        {canToggle ? (
          <Pressable
            onPress={() => void onToggleValidation()}
            disabled={busy}
            style={[styles.cookedBtn, consomme && styles.cookedBtnActive, busy && { opacity: 0.6 }]}
          >
            <Feather
              name="check-circle"
              size={18}
              color={consomme ? "#F7F3EA" : colors.muted}
            />
            <Text style={[styles.cookedLabel, consomme && styles.cookedLabelActive]}>Cuisiné ?</Text>
          </Pressable>
        ) : null}
        <Pressable
          onPress={() => void demanderEtapes()}
          disabled={etapesLoading}
          style={[styles.actionBtn, etapesLoading && { opacity: 0.7 }]}
        >
          <Feather name="play-circle" size={18} color="#1A1207" />
          <Text style={styles.actionLabel}>Commencer à cuisiner</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const ORANGE = "#E58F16";

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  hero: {
    height: 260,
    alignItems: "center",
    justifyContent: "center",
  },
  heroTopRow: {
    position: "absolute",
    top: space.sm,
    left: 0,
    right: 0,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: space.lg,
  },
  heroBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: "rgba(255,255,255,0.7)",
    alignItems: "center",
    justifyContent: "center",
  },
  emoji: { fontSize: 72 },
  content: { padding: space.lg, gap: space.sm, paddingBottom: space.xl },
  nom: { fontSize: 24, fontWeight: "800", color: colors.ink },
  metaRow: { flexDirection: "row", gap: 4 },
  meta: { fontSize: type.body, color: colors.muted, fontWeight: "600" },
  tabs: {
    flexDirection: "row",
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 4,
    marginTop: space.sm,
  },
  tab: {
    flex: 1,
    paddingVertical: space.sm,
    borderRadius: radius.sm - 2,
    alignItems: "center",
  },
  tabActive: { backgroundColor: ORANGE },
  tabText: { fontSize: type.body, color: colors.muted, fontWeight: "600" },
  tabTextActive: { color: "#1A1207" },
  list: { gap: 4, marginTop: space.sm },
  ingredientRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
  },
  ingredientNom: { fontSize: type.body, color: colors.ink },
  ingredientQty: { fontSize: type.body, color: colors.muted },
  instructions: { fontSize: type.body, color: colors.ink, lineHeight: 22, marginTop: space.sm },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
  actionBar: {
    flexDirection: "row",
    gap: space.sm,
    padding: space.lg,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.line,
    backgroundColor: colors.bg,
  },
  cookedBtn: {
    flexDirection: "row",
    gap: 6,
    minHeight: 56,
    paddingHorizontal: space.md,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
  cookedBtnActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  cookedLabel: { fontSize: type.body, fontWeight: "700", color: colors.muted },
  cookedLabelActive: { color: "#F7F3EA" },
  actionBtn: {
    flex: 1,
    flexDirection: "row",
    gap: space.sm,
    minHeight: 56,
    borderRadius: 999,
    backgroundColor: ORANGE,
    alignItems: "center",
    justifyContent: "center",
  },
  actionLabel: { fontSize: 16, fontWeight: "700", color: "#1A1207" },
  etapesLoading: { flexDirection: "row", alignItems: "center", gap: space.sm },
  retry: { color: colors.brand, fontWeight: "700", textDecorationLine: "underline" },
  notFound: { flex: 1, alignItems: "center", justifyContent: "center", gap: space.md, padding: space.lg },
  notFoundText: { fontSize: type.body, color: colors.muted, textAlign: "center" },
  notFoundBtn: {
    paddingHorizontal: space.lg,
    paddingVertical: space.sm,
    borderRadius: radius.sm,
    backgroundColor: colors.brand,
  },
  notFoundBtnText: { color: "#F7F3EA", fontWeight: "700" },
});
