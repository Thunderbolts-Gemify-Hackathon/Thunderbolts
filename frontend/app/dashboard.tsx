import { Ionicons } from "@expo/vector-icons";
import { type Href, useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Pressable,
  ScrollView,
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
import { todayIso, weekStartIso } from "@/lib/dates";
import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { ActionCard } from "@/ui/ActionCard";
import { QuickTile } from "@/ui/QuickTile";
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
    Alert.alert(
      "Refaire l'onboarding ?",
      "Tes réponses actuelles seront réinitialisées.",
      [
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
      ],
    );
  };

  const today = todayIso();
  const repasToday =
    state.planning?.repas.find(
      (r) => r.jour === today && r.statut !== "annule",
    ) ?? state.planning?.repas.find((r) => r.statut === "planifie");

  const stockOk = state.stock.filter((l) => l.quantite_disponible > 0).length;
  const stockEmpty = state.stock.filter(
    (l) => l.quantite_disponible <= 0,
  ).length;

  return (
    <Screen refreshing={loading} onRefresh={() => void load()}>
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Brand>Kaly Tao</Brand>
          <Title style={styles.greeting}>Salut {name}.</Title>
        </View>
        <Pressable
          onPress={confirmReset}
          accessibilityLabel="Refaire l'onboarding"
          style={({ pressed }) => [
            styles.headerIcon,
            pressed && { opacity: 0.6 },
          ]}
        >
          <Ionicons name="settings-outline" size={20} color={colors.brand} />
        </Pressable>
      </View>

      <Body style={styles.intro}>
        {done
          ? "Voici un aperçu de ta journée."
          : "Complète l'onboarding pour personnaliser ton accueil."}
      </Body>

      {state.error ? <Text style={styles.error}>{state.error}</Text> : null}

      {state.peremption > 0 ? (
        <Pressable style={styles.alertBanner} onPress={() => router.push("/stock" as Href)}>
          <Ionicons name="warning-outline" size={18} color={colors.danger} />
          <Text style={styles.alertText}>
            {state.peremption} aliment(s) bientôt périmé(s)
          </Text>
        </Pressable>
      ) : null}

      <View style={styles.heroCard}>
        <Text style={styles.heroLabel}>CE SOIR</Text>
        <Text style={styles.heroValue}>
          {state.ceSoir?.recette.nom ||
            (repasToday
              ? `${repasToday.recette.nom} · ${repasToday.type_repas}`
              : "Aucune idée pour ce soir")}
        </Text>
        <Text style={styles.heroHint}>
          {state.ceSoir
            ? `${Math.round(state.ceSoir.couverture_stock * 100)}% stock · ~${Math.round(state.ceSoir.cout_estime)} Ar · ${state.ceSoir.message}`
            : data.localisation.quartier || "Quartier non renseigné"}
        </Text>
        {state.ceSoir?.recette.id ? (
          <View style={styles.heroActions}>
            <Pressable
              style={styles.heroBtn}
              onPress={() =>
                router.push(`/cuisiner/${state.ceSoir!.recette.id}` as Href)
              }
            >
              <Text style={styles.heroBtnText}>Cuisiner</Text>
            </Pressable>
            <Pressable
              style={[styles.heroBtn, styles.heroBtnGhost]}
              onPress={() => router.push("/repas" as Href)}
            >
              <Text style={[styles.heroBtnText, { color: colors.brand }]}>
                Autre idée
              </Text>
            </Pressable>
          </View>
        ) : null}
      </View>

      {state.summary ? (
        <Text style={styles.budgetLine}>
          Budget : {formatAr(state.summary.montant_restant, state.summary.devise)} restant
          {" · "}
          {state.summary.pourcent_consomme}% consommé
        </Text>
      ) : null}

      {state.antiGaspi ? (
        <View style={styles.antiCard}>
          <Text style={styles.digestLabel}>ANTI-GASPI</Text>
          <Text style={styles.digestText}>
            {Math.round(state.antiGaspi.ariary_sauves)} Ar sauvés · streak{" "}
            {state.antiGaspi.streak_jours} j
          </Text>
          <Text style={styles.digestHint}>{state.antiGaspi.message}</Text>
        </View>
      ) : null}

      {state.digest?.resume ? (
        <View style={styles.digestCard}>
          <Text style={styles.digestLabel}>AGENT FOYER</Text>
          <Text style={styles.digestText}>{state.digest.resume}</Text>
          {(state.digest.actions || [])
            .filter((a) => a.statut === "propose")
            .slice(0, 3)
            .map((action) => (
              <View key={action.id} style={styles.actionBlock}>
                <Text style={styles.digestHint}>
                  {action.message || action.type_action}
                </Text>
                <View style={styles.heroActions}>
                  <Pressable
                    style={styles.heroBtn}
                    disabled={actingId === action.id}
                    onPress={async () => {
                      if (!profilId || !token) return;
                      setActingId(action.id);
                      try {
                        await respondAgentAction(profilId, token, action.id, "accepte");
                        if (action.type_action.includes("course")) {
                          router.push("/courses" as Href);
                        } else {
                          await load();
                        }
                      } catch {
                        /* ignore */
                      } finally {
                        setActingId(null);
                      }
                    }}
                  >
                    <Text style={styles.heroBtnText}>Accepter</Text>
                  </Pressable>
                  <Pressable
                    style={[styles.heroBtn, styles.heroBtnGhost]}
                    disabled={actingId === action.id}
                    onPress={async () => {
                      if (!profilId || !token) return;
                      setActingId(action.id);
                      try {
                        await respondAgentAction(profilId, token, action.id, "refuse");
                        await load();
                      } catch {
                        /* ignore */
                      } finally {
                        setActingId(null);
                      }
                    }}
                  >
                    <Text style={[styles.heroBtnText, { color: colors.brand }]}>
                      Refuser
                    </Text>
                  </Pressable>
                </View>
              </View>
            ))}
        </View>
      ) : null}

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.carousel}
        style={styles.carouselWrap}
      >
        <ActionCard
          icon="restaurant-outline"
          title="Je veux manger"
          subtitle="Trouve une idée de repas"
          tint={colors.brand}
          onPress={() => router.push("/repas" as Href)}
        />
        <ActionCard
          icon="calendar-outline"
          title="Planning"
          subtitle="Jour, semaine ou mois"
          tint={colors.accent}
          onPress={() => router.push("/planning" as Href)}
        />
        <ActionCard
          icon="chatbubble-ellipses-outline"
          title="Assistant"
          subtitle="Pose ta question"
          tint={colors.ok}
          onPress={() => router.push("/chat" as Href)}
        />
        <ActionCard
          icon="mic-outline"
          title="Assistant vocal"
          subtitle="Parle-lui directement"
          tint={colors.accent}
          onPress={() => router.push("/assistant-vocal" as Href)}
        />
      </ScrollView>

      <Text style={styles.sectionTitle}>Vue d&apos;ensemble</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.statsRow}
      >
        <StatCard
          label="En stock"
          value={String(stockOk)}
          hint="ingrédients > 0"
        />
        <StatCard
          label="Rupture"
          value={String(stockEmpty)}
          hint="quantité à 0"
          tone="accent"
        />
        <StatCard
          label="Budget restant"
          value={
            state.budget
              ? formatAr(state.budget.montant_restant, state.budget.devise)
              : "n/a"
          }
          hint={
            state.budget
              ? `période : ${state.budget.periode}`
              : "budget non trouvé"
          }
        />
        <StatCard
          label="Marché suggéré"
          value={
            state.market ? state.market.point_de_vente.nom : "Aucune suggestion"
          }
          hint={
            state.market
              ? `${formatAr(state.market.prix)} · ${state.market.itineraire?.niveau_securite ?? "n/a"}`
              : "Ajoute du stock pour proposer un marché"
          }
        />
      </ScrollView>

      <Text style={styles.sectionTitle}>Accès rapide</Text>
      <View style={styles.grid}>
        <QuickTile
          icon="cart-outline"
          label="Liste de courses"
          onPress={() => router.push("/courses" as Href)}
        />
        <QuickTile
          icon="storefront-outline"
          label="Marchés"
          onPress={() => router.push("/market" as Href)}
        />
        <QuickTile
          icon="map-outline"
          label="Carte marchés"
          onPress={() => router.push("/map" as Href)}
        />
        <QuickTile
          icon="cube-outline"
          label="Gérer mon stock"
          onPress={() => router.push("/stock" as Href)}
        />
        <QuickTile
          icon="book-outline"
          label="Recettes"
          onPress={() => router.push("/recettes" as Href)}
        />
        <QuickTile
          icon="people-outline"
          label="Coloc / foyer"
          onPress={() => router.push("/foyer" as Href)}
        />
      </View>
    </Screen>
  );
}

function StatCard({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string;
  hint: string;
  tone?: "accent";
}) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text
        style={[
          styles.statValue,
          tone === "accent" && { color: colors.accent },
        ]}
        numberOfLines={1}
      >
        {value}
      </Text>
      <Text style={styles.statHint} numberOfLines={1}>
        {hint}
      </Text>
    </View>
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
  intro: { marginTop: space.xs, marginBottom: space.md },
  heroCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.line,
    padding: space.md,
    gap: 4,
  },
  heroLabel: {
    fontSize: type.small,
    color: colors.muted,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.4,
  },
  heroValue: {
    fontSize: 20,
    fontWeight: "700",
    color: colors.ink,
    marginTop: 4,
  },
  heroHint: { fontSize: type.small, color: colors.muted },
  heroActions: { flexDirection: "row", gap: space.sm, marginTop: space.sm },
  heroBtn: {
    backgroundColor: colors.brand,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
    borderRadius: radius.sm,
  },
  heroBtnGhost: {
    backgroundColor: colors.brandSoft,
  },
  heroBtnText: { color: "#fff", fontWeight: "700", fontSize: type.label },
  alertBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.sm,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: radius.md,
    marginBottom: space.sm,
  },
  alertText: { color: colors.danger, fontWeight: "600", flex: 1 },
  budgetLine: {
    fontSize: type.small,
    color: colors.muted,
    marginTop: space.sm,
    marginBottom: space.sm,
  },
  digestCard: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.md,
    padding: space.md,
    gap: 4,
    marginBottom: space.sm,
  },
  antiCard: {
    backgroundColor: "#E8F2EA",
    borderRadius: radius.md,
    padding: space.md,
    gap: 4,
    marginBottom: space.sm,
  },
  actionBlock: { gap: 6, marginTop: space.xs },
  digestLabel: {
    fontSize: type.small,
    color: colors.brand,
    fontWeight: "700",
    letterSpacing: 0.4,
  },
  digestText: { fontSize: type.body, color: colors.ink, fontWeight: "600" },
  digestHint: { fontSize: type.small, color: colors.muted },
  carouselWrap: { marginHorizontal: -space.lg },
  carousel: { gap: space.sm, paddingHorizontal: space.lg },
  sectionTitle: {
    fontSize: type.body,
    fontWeight: "700",
    color: colors.ink,
    marginBottom: -space.xs,
  },
  statsRow: { gap: space.sm, paddingRight: space.md },
  statCard: {
    width: 150,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: space.md,
    gap: 4,
  },
  statLabel: {
    fontSize: type.small,
    color: colors.muted,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.4,
  },
  statValue: {
    fontSize: 20,
    fontWeight: "700",
    color: colors.ink,
    marginTop: 4,
  },
  statHint: { fontSize: type.small, color: colors.muted },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
    marginBottom: space.md,
  },
});
