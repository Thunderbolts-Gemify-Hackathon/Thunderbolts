import { type Href, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { ApiError } from "@/api/http";
import {
  annulerRepas,
  generatePlanning,
  getPlanning,
  TYPE_REPAS_LABEL,
  validerRepas,
  type Planning,
  type Repas,
} from "@/api/planning";
import { todayIso, weekStartIso } from "@/lib/dates";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

const MEAL_ORDER = ["petit_dejeuner", "dejeuner", "diner"];

export default function PlanningScreen() {
  const router = useRouter();
  const { session } = useSession();
  const profilId = session?.profilId;
  const token = session?.apiToken;
  const dateDebut = useMemo(() => weekStartIso(), []);

  const [planning, setPlanning] = useState<Planning | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!profilId || !token) {
      setError("Session invalide. Refais l'onboarding.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const p = await getPlanning(profilId, token, dateDebut).catch((e) => {
        if (e instanceof ApiError && e.status === 404) return null;
        throw e;
      });
      setPlanning(p);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Chargement impossible");
    } finally {
      setLoading(false);
    }
  }, [profilId, token, dateDebut]);

  useEffect(() => {
    void load();
  }, [load]);

  const onGenerate = async () => {
    if (!profilId || !token) return;
    setGenerating(true);
    setError(null);
    try {
      setPlanning(await generatePlanning(profilId, token, dateDebut));
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

  const onToggleRepas = async (repas: Repas) => {
    if (!token) return;
    setBusyId(repas.id);
    setError(null);
    try {
      if (repas.statut === "consomme") {
        await annulerRepas(repas.id, token);
      } else if (repas.statut === "planifie") {
        await validerRepas(repas.id, token);
      }
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Action impossible");
    } finally {
      setBusyId(null);
    }
  };

  const today = todayIso();
  const repasSorted = [...(planning?.repas ?? [])].sort((a, b) =>
    a.jour === b.jour
      ? MEAL_ORDER.indexOf(a.type_repas) - MEAL_ORDER.indexOf(b.type_repas)
      : a.jour.localeCompare(b.jour)
  );
  const jours = [...new Set(repasSorted.map((r) => r.jour))];

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label={generating ? "Generation en cours…" : "Generer la semaine"}
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
      <Body>
        Semaine du {dateDebut}. Genere via Gemma, puis valide un repas pour deduire le stock.
      </Body>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {!loading && !planning ? (
        <Body>Aucun planning pour cette semaine.</Body>
      ) : null}

      {jours.map((jour) => (
        <View key={jour} style={styles.jourGroup}>
          <Text style={[styles.jourLabel, jour === today && styles.jourLabelToday]}>
            {jour}
            {jour === today ? " · aujourd'hui" : ""}
          </Text>
          {repasSorted
            .filter((r) => r.jour === jour)
            .map((repas) => {
              const busy = busyId === repas.id;
              const canToggle = repas.statut === "planifie" || repas.statut === "consomme";
              const expanded = expandedId === repas.id;
              return (
                <Pressable
                  key={repas.id}
                  onPress={() => setExpandedId(expanded ? null : repas.id)}
                  style={[styles.card, jour === today && styles.cardToday]}
                >
                  <Text style={styles.meta}>{TYPE_REPAS_LABEL[repas.type_repas] ?? repas.type_repas}</Text>
                  <Text style={styles.nom}>{repas.recette.nom}</Text>
                  <View style={styles.metaRow}>
                    <Text style={styles.statut}>{repas.statut}</Text>
                    <Text style={styles.statut}>{Math.round(repas.recette.kcal_total)} kcal</Text>
                    {repas.recette.duree_minutes ? (
                      <Text style={styles.statut}>~{repas.recette.duree_minutes} min</Text>
                    ) : null}
                  </View>

                  {expanded ? (
                    <View style={styles.detail}>
                      <Text style={styles.sub}>Ingredients</Text>
                      {repas.recette.ingredients.map((ligne) => (
                        <Text key={ligne.ingredient.id} style={styles.ingredient}>
                          {ligne.ingredient.nom} — {ligne.poids_requis} {ligne.unite}
                        </Text>
                      ))}
                      {repas.recette.instructions ? (
                        <>
                          <Text style={styles.sub}>Preparation</Text>
                          <Text style={styles.instructions}>{repas.recette.instructions}</Text>
                        </>
                      ) : null}
                    </View>
                  ) : null}

                  {canToggle ? (
                    <Pressable
                      onPress={(e) => {
                        e.stopPropagation();
                        void onToggleRepas(repas);
                      }}
                      disabled={busy}
                      style={styles.action}
                    >
                      <Text style={styles.actionText}>
                        {busy
                          ? "…"
                          : repas.statut === "consomme"
                            ? "Annuler la validation"
                            : "Valider (deduire stock)"}
                      </Text>
                    </Pressable>
                  ) : null}
                </Pressable>
              );
            })}
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
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.md,
    gap: 4,
  },
  cardToday: { borderColor: colors.brand },
  meta: {
    fontSize: type.small,
    color: colors.muted,
    fontWeight: "700",
    textTransform: "uppercase",
  },
  metaRow: { flexDirection: "row", flexWrap: "wrap", gap: space.md },
  nom: { fontSize: type.body, color: colors.ink, fontWeight: "700" },
  statut: { fontSize: type.small, color: colors.muted },
  detail: { gap: 4, marginTop: space.xs },
  sub: {
    fontSize: type.label,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
    marginTop: space.xs,
  },
  ingredient: { fontSize: type.small, color: colors.ink },
  instructions: { fontSize: type.body, color: colors.ink, lineHeight: 20 },
  action: {
    marginTop: space.sm,
    alignSelf: "flex-start",
    paddingVertical: space.xs,
    paddingHorizontal: space.sm,
    backgroundColor: colors.brandSoft,
    borderRadius: radius.sm,
  },
  actionText: { color: colors.brand, fontWeight: "700", fontSize: type.label },
});
