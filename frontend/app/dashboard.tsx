import { type Href, useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

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
import { Button } from "@/ui/Button";
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
          coords.lon
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

  const today = todayIso();
  const repasToday =
    state.planning?.repas.find((r) => r.jour === today && r.statut !== "annule") ??
    state.planning?.repas.find((r) => r.statut === "planifie");

  const stockOk = state.stock.filter((l) => l.quantite_disponible > 0).length;
  const stockEmpty = state.stock.filter((l) => l.quantite_disponible <= 0).length;

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button label="Planning" onPress={() => router.push("/planning" as Href)} />
          <Button label="Assistant" variant="ghost" onPress={() => router.push("/chat" as Href)} />
          <Button label="Liste de courses" variant="ghost" onPress={() => router.push("/courses" as Href)} />
          <Button label="Marches" variant="ghost" onPress={() => router.push("/market" as Href)} />
          <Button label="Carte marches" variant="ghost" onPress={() => router.push("/map" as Href)} />
          <Button label="Gerer mon stock" variant="ghost" onPress={() => router.push("/stock" as Href)} />
          <Button label="Actualiser" variant="ghost" onPress={() => void load()} disabled={loading} />
          <Button
            label="Refaire l'onboarding"
            variant="ghost"
            onPress={async () => {
              reset();
              await clearSession();
              router.replace("/");
            }}
          />
        </View>
      }
    >
      <Brand>Kaly Tao</Brand>
      <Title>Salut {name}.</Title>
      <Body>
        {done
          ? "Donnees chargees depuis l'API."
          : "Complete l'onboarding pour personnaliser ton accueil."}
      </Body>

      {loading ? (
        <ActivityIndicator color={colors.brand} style={{ marginVertical: space.lg }} />
      ) : null}

      {state.error ? <Text style={styles.error}>{state.error}</Text> : null}

      <Card
        label="Aujourd'hui"
        value={
          repasToday
            ? `${repasToday.recette.nom} · ${repasToday.type_repas}`
            : "Aucun repas planifie"
        }
        hint={data.localisation.quartier || "Quartier non renseigne"}
      />

      <View style={styles.row}>
        <Card compact label="En stock" value={String(stockOk)} hint="ingredients > 0" />
        <Card
          compact
          label="Rupture"
          value={String(stockEmpty)}
          hint="quantite a 0"
          tone="accent"
        />
      </View>

      <Card
        label="Budget restant"
        value={
          state.budget
            ? formatAr(state.budget.montant_restant, state.budget.devise)
            : "n/a"
        }
        hint={state.budget ? `periode : ${state.budget.periode}` : "budget non trouve"}
      />

      <Card
        label="Marche suggere"
        value={state.market ? state.market.point_de_vente.nom : "Pas de suggestion"}
        hint={
          state.market
            ? `${formatAr(state.market.prix)} · ${state.market.itineraire?.niveau_securite ?? "n/a"}`
            : "Ajoute du stock pour proposer un marche"
        }
      />
    </Screen>
  );
}

function Card({
  label,
  value,
  hint,
  compact,
  tone,
}: {
  label: string;
  value: string;
  hint: string;
  compact?: boolean;
  tone?: "accent";
}) {
  return (
    <View style={[styles.card, compact && styles.cardCompact]}>
      <Text style={styles.cardLabel}>{label}</Text>
      <Text style={[styles.cardValue, tone === "accent" && { color: colors.accent }]}>
        {value}
      </Text>
      <Text style={styles.cardHint}>{hint}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: space.sm },
  card: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: space.md,
    gap: 4,
  },
  cardCompact: { minHeight: 110 },
  cardLabel: {
    fontSize: type.small,
    color: colors.muted,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.4,
  },
  cardValue: {
    fontSize: 22,
    fontWeight: "700",
    color: colors.ink,
    marginTop: 4,
  },
  cardHint: { fontSize: type.small, color: colors.muted },
  actions: { gap: space.sm },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
});
