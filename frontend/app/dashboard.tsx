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
import { ApiError } from "@/api/http";
import { QUARTIER_COORDS } from "@/api/onboarding";
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
  stock: StockLine[];
  planning: Planning | null;
  market: MarketMatch | null;
  error: string | null;
};

export default function DashboardScreen() {
  const router = useRouter();
  const { data, reset, done } = useOnboarding();
  const { session, clearSession } = useSession();
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState<DashState>({
    budget: null,
    stock: [],
    planning: null,
    market: null,
    error: null,
  });

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
      const [budget, stock, planning] = await Promise.all([
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

      setState({ budget, stock, planning, market, error: null });
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

      <View style={styles.heroCard}>
        <Text style={styles.heroLabel}>AUJOURD&apos;HUI</Text>
        <Text style={styles.heroValue}>
          {repasToday
            ? `${repasToday.recette.nom} · ${repasToday.type_repas}`
            : "Aucun repas planifié"}
        </Text>
        <Text style={styles.heroHint}>
          {data.localisation.quartier || "Quartier non renseigné"}
        </Text>
      </View>

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
