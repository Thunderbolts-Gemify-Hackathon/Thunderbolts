import { type Href, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { ApiError } from "@/api/http";
import {
  generatePlanning,
  getPlanning,
  type Planning,
  type Repas,
} from "@/api/planning";
import { monthStartIso, todayIso, weekStartIso } from "@/lib/dates";
import { cacheRecette } from "@/lib/recipeCache";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { RecipeCard } from "@/ui/RecipeCard";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

const MEAL_ORDER = ["petit_dejeuner", "dejeuner", "diner"];

type Periode = "jour" | "semaine" | "mois";

const PERIODE_OPTIONS: { value: Periode; label: string }[] = [
  { value: "jour", label: "Jour" },
  { value: "semaine", label: "Semaine" },
  { value: "mois", label: "Mois" },
];

const DATE_DEBUT_PAR_PERIODE: Record<Periode, () => string> = {
  jour: todayIso,
  semaine: weekStartIso,
  mois: monthStartIso,
};

export default function PlanningScreen() {
  const router = useRouter();
  const { session } = useSession();
  const profilId = session?.profilId;
  const token = session?.apiToken;

  const [periode, setPeriode] = useState<Periode>("semaine");
  const dateDebut = useMemo(() => DATE_DEBUT_PAR_PERIODE[periode](), [periode]);

  const [planning, setPlanning] = useState<Planning | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!profilId || !token) {
      setError("Session invalide. Refais l'onboarding.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const p = await getPlanning(profilId, token, dateDebut, periode).catch((e) => {
        if (e instanceof ApiError && e.status === 404) return null;
        throw e;
      });
      setPlanning(p);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Chargement impossible");
    } finally {
      setLoading(false);
    }
  }, [profilId, token, dateDebut, periode]);

  useEffect(() => {
    void load();
  }, [load]);

  const onGenerate = async () => {
    if (!profilId || !token) return;
    setGenerating(true);
    setError(null);
    try {
      setPlanning(await generatePlanning(profilId, token, dateDebut, periode));
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.detail
          : "Generation impossible. Verifie Ollama ou l'API Gemma."
      );
    } finally {
      setGenerating(false);
    }
  };

  const openRecette = (repas: Repas) => {
    cacheRecette(repas.recette, {
      repasId: repas.id,
      statut: repas.statut,
      jour: repas.jour,
      typeRepas: repas.type_repas,
    });
    router.push(`/recette/${repas.recette.id}` as Href);
  };

  const today = todayIso();
  const repasSorted = [...(planning?.repas ?? [])].sort((a, b) =>
    a.jour === b.jour
      ? MEAL_ORDER.indexOf(a.type_repas) - MEAL_ORDER.indexOf(b.type_repas)
      : a.jour.localeCompare(b.jour)
  );
  const jours = [...new Set(repasSorted.map((r) => r.jour))];

  const generateLabel = generating
    ? "Génération en cours…"
    : periode === "jour"
      ? "Générer le jour"
      : periode === "mois"
        ? "Générer le mois"
        : "Générer la semaine";

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label={generateLabel}
            onPress={() => void onGenerate()}
            disabled={generating || loading}
          />
          {planning ? (
            <Button
              label="Liste de courses"
              variant="ghost"
              onPress={() => router.push("/courses" as Href)}
            />
          ) : null}
          <Button label="Retour" variant="ghost" onPress={() => router.back()} />
        </View>
      }
    >
      <Title>Planning</Title>
      <Body>Choisis tes repas, générés par Gemma selon ton profil.</Body>

      <View style={styles.periodeRow}>
        {PERIODE_OPTIONS.map((opt) => {
          const active = opt.value === periode;
          return (
            <Pressable
              key={opt.value}
              onPress={() => setPeriode(opt.value)}
              style={[styles.periodeChip, active && styles.periodeChipActive]}
            >
              <Text style={[styles.periodeText, active && styles.periodeTextActive]}>
                {opt.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {!loading && !planning ? (
        <Body>Aucun planning pour cette période. Génère-le ci-dessous.</Body>
      ) : null}

      {jours.map((jour) => (
        <View key={jour} style={styles.jourGroup}>
          <Text style={[styles.jourLabel, jour === today && styles.jourLabelToday]}>
            {jour}
            {jour === today ? " · aujourd'hui" : ""}
          </Text>
          <View style={styles.grid}>
            {repasSorted
              .filter((r) => r.jour === jour)
              .map((repas) => (
                <RecipeCard
                  key={repas.id}
                  recette={repas.recette}
                  statut={repas.statut}
                  onPress={() => openRecette(repas)}
                />
              ))}
          </View>
        </View>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  actions: { gap: space.sm },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
  periodeRow: {
    flexDirection: "row",
    gap: space.sm,
  },
  periodeChip: {
    flex: 1,
    paddingVertical: space.sm,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    alignItems: "center",
  },
  periodeChipActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  periodeText: { fontSize: type.body, color: colors.ink, fontWeight: "600" },
  periodeTextActive: { color: "#F7F3EA" },
  jourGroup: { gap: space.sm },
  jourLabel: {
    fontSize: type.label,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
    letterSpacing: 0.3,
    marginTop: space.sm,
  },
  jourLabelToday: { color: colors.brand },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: space.sm,
  },
});
