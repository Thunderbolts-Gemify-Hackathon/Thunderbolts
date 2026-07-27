import { Ionicons } from "@expo/vector-icons";
import { type Href, useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import {
  findNearbyMarket,
  formatAr,
  getBudget,
  getPlanning,
  getStock,
  type Budget,
  type MarketMatch,
  type Planning,
  type StockLine,
} from "@/api/dashboard";
import { getAgentDigest, respondAgentAction, type AgentDigest } from "@/api/agent";
import { getAntiGaspi, type AntiGaspi } from "@/api/antiGaspi";
import { getCeSoir, type CeSoirSuggestion } from "@/api/ceSoir";
import { ApiError } from "@/api/http";
import { QUARTIER_COORDS } from "@/api/onboarding";
import { getAlertesPeremption } from "@/api/stockAlerts";
import { getBudgetSummary, type BudgetSummary } from "@/api/budget";
import { cacheRecette } from "@/lib/recipeCache";
import { weekStartIso } from "@/lib/dates";
import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { Screen } from "@/ui/Screen";
import { Body, Brand, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

type DashState = {
  budget: Budget | null;
  summary: BudgetSummary | null;
  stock: StockLine[];
  planning: Planning | null;
  market: MarketMatch | null;
  ceSoir: CeSoirSuggestion | null;
  digest: AgentDigest | null;
  antiGaspi: AntiGaspi | null;
  peremption: number;
  error: string | null;
};

/**
 * Dashboard senior : une composition, un job.
 * Hero = Ce soir. Le reste est compact (signaux + 4 raccourcis).
 */
export default function DashboardScreen() {
  const router = useRouter();
  const { data, reset, done } = useOnboarding();
  const { session, clearSession } = useSession();
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState<DashState>({
    budget: null,
    summary: null,
    stock: [],
    planning: null,
    market: null,
    ceSoir: null,
    digest: null,
    antiGaspi: null,
    peremption: 0,
    error: null,
  });
  const [actingId, setActingId] = useState<string | null>(null);
  const [showMore, setShowMore] = useState(false);

  const name = session?.prenom || "toi";
  const profilId = session?.profilId;
  const token = session?.apiToken;

  const load = useCallback(async () => {
    if (!profilId || !token) {
      setLoading(false);
      setState((s) => ({
        ...s,
        error: "Session incomplete. Refais l'onboarding.",
      }));
      return;
    }

    setLoading(true);
    try {
      const [budget, stock, planning, ceSoir, peremption, summary, digest, antiGaspi] =
        await Promise.all([
          getBudget(profilId, token).catch((e) => {
            if (e instanceof ApiError && e.status === 404) return null;
            throw e;
          }),
          getStock(profilId, token).catch((e) => {
            if (e instanceof ApiError && e.status === 404) return [];
            throw e;
          }),
          getPlanning(profilId, token, weekStartIso()).catch((e) => {
            if (e instanceof ApiError && e.status === 404) return null;
            throw e;
          }),
          getCeSoir(profilId, token).catch(() => null),
          getAlertesPeremption(profilId, token).catch(() => []),
          getBudgetSummary(profilId, token).catch(() => null),
          getAgentDigest(profilId, token).catch(() => null),
          getAntiGaspi(profilId, token).catch(() => null),
        ]);

      let market: MarketMatch | null = null;
      const quartier = data.localisation.quartier;
      const coords = quartier ? QUARTIER_COORDS[quartier] : null;
      const ingredientId = stock[0]?.ingredient_id;
      if (coords && ingredientId) {
        const matches = await findNearbyMarket(
          ingredientId,
          coords.lat,
          coords.lon,
        ).catch(() => []);
        market = matches[0] ?? null;
      }

      if (ceSoir?.recette?.id) {
        cacheRecette({
          id: ceSoir.recette.id,
          nom: ceSoir.recette.nom,
          heure_conseillee: null,
          kcal_total: ceSoir.recette.kcal_total ?? 0,
          proteines: 0,
          glucides: 0,
          lipides: 0,
          duree_minutes: ceSoir.recette.duree_minutes ?? null,
          tags: [],
          instructions: null,
          ingredients: [],
        });
      }

      setState({
        budget,
        summary,
        stock,
        planning,
        market,
        ceSoir,
        digest,
        antiGaspi,
        peremption: peremption.length,
        error: null,
      });
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.detail
          : e instanceof Error
            ? e.message
            : "Impossible de charger le dashboard";
      setState((s) => ({ ...s, error: msg }));
    } finally {
      setLoading(false);
    }
  }, [profilId, token, data.localisation.quartier]);

  useEffect(() => {
    void load();
  }, [load]);

  const confirmReset = () => {
    Alert.alert("Refaire l'onboarding ?", "Tes réponses actuelles seront réinitialisées.", [
      { text: "Annuler", style: "cancel" },
      {
        text: "Continuer",
        style: "destructive",
        onPress: async () => {
          reset();
          await clearSession();
          router.replace("/");
        },
      },
    ]);
  };

  const respond = async (actionId: string, decision: "accepte" | "refuse") => {
    if (!profilId || !token) return;
    setActingId(actionId);
    try {
      const action = state.digest?.actions?.find((a) => a.id === actionId);
      await respondAgentAction(profilId, token, actionId, decision);
      if (decision === "accepte" && action?.type_action.includes("course")) {
        router.push("/courses" as Href);
      } else {
        await load();
      }
    } catch {
      /* ignore */
    } finally {
      setActingId(null);
    }
  };

  const pendingActions = (state.digest?.actions || []).filter(
    (a) => a.statut === "propose",
  );
  const coveragePct = state.ceSoir
    ? Math.round(state.ceSoir.couverture_stock * 100)
    : null;

  return (
    <Screen refreshing={loading} onRefresh={() => void load()}>
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Brand>Kaly Tao</Brand>
          <Title style={styles.greeting}>Salut {name}.</Title>
        </View>
        <Pressable
          onPress={() => router.push("/reglages" as Href)}
          style={styles.headerIcon}
        >
          <Ionicons name="settings-outline" size={20} color={colors.brand} />
        </Pressable>
      </View>

      {!done ? (
        <Body style={styles.intro}>Termine l'onboarding pour personnaliser Ce soir.</Body>
      ) : null}
      {state.error ? <Text style={styles.error}>{state.error}</Text> : null}

      {/* HERO — un seul job */}
      <View style={styles.hero}>
        <Text style={styles.heroEyebrow}>CE SOIR</Text>
        <Text style={styles.heroTitle}>
          {state.ceSoir?.recette.nom || "Pas encore d'idée"}
        </Text>
        {state.ceSoir ? (
          <Text style={styles.heroMeta}>
            {coveragePct}% du stock
            {state.ceSoir.cout_estime
              ? ` · ~${Math.round(state.ceSoir.cout_estime)} Ar`
              : ""}
            {state.ceSoir.recette.duree_minutes
              ? ` · ${state.ceSoir.recette.duree_minutes} min`
              : ""}
          </Text>
        ) : (
          <Text style={styles.heroMeta}>
            {data.localisation.quartier || "Ajoute ton quartier et du stock"}
          </Text>
        )}
        {state.ceSoir?.message ? (
          <Text style={styles.heroMsg}>{state.ceSoir.message}</Text>
        ) : null}

        <View style={styles.heroCtas}>
          <Pressable
            style={[styles.ctaPrimary, !state.ceSoir?.recette.id && styles.ctaDisabled]}
            disabled={!state.ceSoir?.recette.id}
            onPress={() =>
              state.ceSoir?.recette.id &&
              router.push(`/cuisiner/${state.ceSoir.recette.id}` as Href)
            }
          >
            <Text style={styles.ctaPrimaryText}>Cuisiner maintenant</Text>
          </Pressable>
          <View style={styles.ctaRow}>
            <Pressable
              style={styles.ctaSecondary}
              onPress={() => router.push("/repas" as Href)}
            >
              <Text style={styles.ctaSecondaryText}>Autre idée</Text>
            </Pressable>
            <Pressable
              style={styles.ctaSecondary}
              onPress={() =>
                void getCeSoir(profilId!, token!, "rapide")
                  .then((ceSoir) => setState((s) => ({ ...s, ceSoir })))
                  .catch(() => undefined)
              }
            >
              <Text style={styles.ctaSecondaryText}>Plus rapide</Text>
            </Pressable>
          </View>
        </View>
      </View>

      {/* Signaux compacts — une ligne */}
      <View style={styles.signalRow}>
        <Pressable
          style={styles.signal}
          onPress={() => router.push("/stock" as Href)}
        >
          <Text style={styles.signalValue}>
            {state.peremption > 0 ? state.peremption : state.stock.filter((l) => l.quantite_disponible > 0).length}
          </Text>
          <Text style={styles.signalLabel}>
            {state.peremption > 0 ? "à sauver" : "en stock"}
          </Text>
        </Pressable>
        <Pressable
          style={styles.signal}
          onPress={() => router.push("/courses" as Href)}
        >
          <Text style={styles.signalValue}>
            {state.summary
              ? formatAr(state.summary.montant_restant, state.summary.devise)
              : "—"}
          </Text>
          <Text style={styles.signalLabel}>budget</Text>
        </Pressable>
        <Pressable
          style={styles.signal}
          onPress={() => router.push("/market" as Href)}
        >
          <Text style={styles.signalValue} numberOfLines={1}>
            {state.market?.point_de_vente.nom?.split(" ")[0] || "Marché"}
          </Text>
          <Text style={styles.signalLabel}>
            {state.market
              ? formatAr(state.market.prix_crowd ?? state.market.prix)
              : "près de toi"}
          </Text>
        </Pressable>
        <Pressable style={styles.signal}>
          <Text style={styles.signalValue}>
            {state.antiGaspi ? `${state.antiGaspi.streak_jours}j` : "0"}
          </Text>
          <Text style={styles.signalLabel}>streak</Text>
        </Pressable>
      </View>

      {/* Agent : seulement s'il y a une action */}
      {pendingActions.length > 0 ? (
        <View style={styles.agentCard}>
          <Text style={styles.agentTitle}>Proposition KaliTao</Text>
          <Text style={styles.agentBody}>
            {pendingActions[0].message || pendingActions[0].type_action}
          </Text>
          <View style={styles.ctaRow}>
            <Pressable
              style={styles.ctaPrimarySmall}
              disabled={actingId === pendingActions[0].id}
              onPress={() => void respond(pendingActions[0].id, "accepte")}
            >
              <Text style={styles.ctaPrimaryTextLight}>OK</Text>
            </Pressable>
            <Pressable
              style={styles.ctaGhost}
              disabled={actingId === pendingActions[0].id}
              onPress={() => void respond(pendingActions[0].id, "refuse")}
            >
              <Text style={styles.ctaGhostText}>Plus tard</Text>
            </Pressable>
          </View>
        </View>
      ) : null}

      {/* 4 raccourcis max */}
      <View style={styles.shortcuts}>
        {(
          [
            { icon: "mic-outline" as const, label: "Vocal", href: "/assistant-vocal" },
            { icon: "cart-outline" as const, label: "Courses", href: "/courses" },
            { icon: "calendar-outline" as const, label: "Planning", href: "/planning" },
            { icon: "cube-outline" as const, label: "Stock", href: "/stock" },
          ] as const
        ).map((item) => (
          <Pressable
            key={item.href}
            style={styles.shortcut}
            onPress={() => router.push(item.href as Href)}
          >
            <Ionicons name={item.icon} size={22} color={colors.brand} />
            <Text style={styles.shortcutLabel}>{item.label}</Text>
          </Pressable>
        ))}
      </View>

      <Pressable onPress={() => setShowMore((v) => !v)} style={styles.moreToggle}>
        <Text style={styles.moreToggleText}>
          {showMore ? "Moins" : "Plus d'accès"}
        </Text>
      </Pressable>

      {showMore ? (
        <View style={styles.moreGrid}>
          {(
            [
              ["/market", "Marchés"],
              ["/map", "Carte"],
              ["/recettes", "Recettes"],
              ["/foyer", "Coloc"],
              ["/chat", "Chat"],
              ["/repas", "Je mange"],
            ] as const
          ).map(([href, label]) => (
            <Pressable
              key={href}
              style={styles.moreItem}
              onPress={() => router.push(href as Href)}
            >
              <Text style={styles.moreItemText}>{label}</Text>
            </Pressable>
          ))}
          <Pressable style={styles.moreItem} onPress={confirmReset}>
            <Text style={[styles.moreItemText, { color: colors.danger }]}>
              Reset onboarding
            </Text>
          </Pressable>
        </View>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: { flexDirection: "row", alignItems: "flex-start", gap: space.sm },
  greeting: { marginTop: 2 },
  headerIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.brandSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  intro: { marginTop: space.xs, marginBottom: space.sm },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
    marginBottom: space.sm,
  },
  hero: {
    backgroundColor: colors.brand,
    borderRadius: radius.lg,
    padding: space.lg,
    gap: space.sm,
    marginTop: space.sm,
  },
  heroEyebrow: {
    color: "rgba(255,255,255,0.7)",
    fontSize: type.small,
    fontWeight: "700",
    letterSpacing: 1,
  },
  heroTitle: {
    color: "#fff",
    fontSize: 28,
    fontWeight: "800",
    lineHeight: 32,
  },
  heroMeta: { color: "rgba(255,255,255,0.85)", fontSize: type.body },
  heroMsg: { color: "rgba(255,255,255,0.75)", fontSize: type.small, marginTop: 2 },
  heroCtas: { gap: space.sm, marginTop: space.sm },
  ctaPrimary: {
    backgroundColor: "#fff",
    borderRadius: radius.md,
    minHeight: 52,
    alignItems: "center",
    justifyContent: "center",
  },
  ctaPrimarySmall: {
    flex: 1,
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  ctaDisabled: { opacity: 0.5 },
  ctaPrimaryText: { color: colors.brand, fontWeight: "800", fontSize: type.body },
  ctaPrimaryTextLight: { color: "#fff", fontWeight: "800", fontSize: type.body },
  ctaRow: { flexDirection: "row", gap: space.sm },
  ctaSecondary: {
    flex: 1,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.45)",
    borderRadius: radius.md,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.08)",
  },
  ctaSecondaryText: { color: "#fff", fontWeight: "700", fontSize: type.label },
  ctaGhost: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surface,
  },
  ctaGhostText: { color: colors.brand, fontWeight: "700", fontSize: type.label },
  signalRow: {
    flexDirection: "row",
    gap: space.sm,
    marginTop: space.md,
  },
  signal: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    paddingVertical: space.sm,
    paddingHorizontal: 6,
    alignItems: "center",
    gap: 2,
  },
  signalValue: {
    fontSize: 13,
    fontWeight: "800",
    color: colors.ink,
  },
  signalLabel: {
    fontSize: 10,
    color: colors.muted,
    fontWeight: "600",
    textTransform: "uppercase",
  },
  agentCard: {
    marginTop: space.md,
    backgroundColor: colors.brandSoft,
    borderRadius: radius.md,
    padding: space.md,
    gap: space.sm,
  },
  agentTitle: {
    fontSize: type.small,
    fontWeight: "800",
    color: colors.brand,
    letterSpacing: 0.4,
  },
  agentBody: { fontSize: type.body, color: colors.ink, fontWeight: "600" },
  shortcuts: {
    flexDirection: "row",
    gap: space.sm,
    marginTop: space.lg,
  },
  shortcut: {
    flex: 1,
    alignItems: "center",
    gap: 6,
    paddingVertical: space.md,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
  },
  shortcutLabel: { fontSize: type.small, fontWeight: "700", color: colors.ink },
  moreToggle: { alignItems: "center", marginTop: space.md, padding: space.sm },
  moreToggleText: { color: colors.muted, fontWeight: "700", fontSize: type.label },
  moreGrid: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  moreItem: {
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
    borderRadius: radius.sm,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
  },
  moreItemText: { fontSize: type.label, fontWeight: "600", color: colors.ink },
});
