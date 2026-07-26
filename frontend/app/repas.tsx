import { useRouter } from "expo-router";
import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { ApiError } from "@/api/http";
import {
  getSuggestionRepas,
  inferTypeRepas,
  type SuggestionRepas,
  type TypeRepas,
} from "@/api/repas";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { AiText } from "@/ui/Markdown";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

const TYPE_REPAS_OPTIONS: { value: TypeRepas; label: string }[] = [
  { value: "petit_dejeuner", label: "Petit-dejeuner" },
  { value: "dejeuner", label: "Dejeuner" },
  { value: "diner", label: "Diner" },
];

const DUREE_OPTIONS: { value: number | null; label: string }[] = [
  { value: 20, label: "Rapide (~20 min)" },
  { value: 45, label: "Normal (~45 min)" },
  { value: null, label: "Peu importe" },
];

export default function RepasScreen() {
  const router = useRouter();
  const { session } = useSession();
  const profilId = session?.profilId;
  const token = session?.apiToken;

  const [typeRepas, setTypeRepas] = useState<TypeRepas>(() => inferTypeRepas());
  const [dureeMax, setDureeMax] = useState<number | null>(null);
  const [suggestion, setSuggestion] = useState<SuggestionRepas | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chercher = async () => {
    if (!profilId || !token || loading) return;
    setLoading(true);
    setError(null);
    try {
      setSuggestion(await getSuggestionRepas(profilId, token, typeRepas, dureeMax));
    } catch (e) {
      setError(
        e instanceof ApiError ? e.detail : "Suggestion indisponible. Verifie Ollama / Gemma."
      );
    } finally {
      setLoading(false);
    }
  };

  const recette = suggestion?.recette;
  const manquants = new Set((suggestion?.ingredients_manquants ?? []).map((n) => n.toLowerCase()));

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label={loading ? "…" : suggestion ? "Une autre idee" : "Je veux manger quelque chose"}
            onPress={() => void chercher()}
            disabled={loading || !profilId}
          />
          <Button label="Retour" variant="ghost" onPress={() => router.back()} />
        </View>
      }
    >
      <Title>Je veux manger quelque chose</Title>
      <Body>
        Gemma choisit une recette adaptee au creneau et a ce que tu as deja en stock.
      </Body>

      <Text style={styles.section}>Creneau</Text>
      <View style={styles.chips}>
        {TYPE_REPAS_OPTIONS.map((opt) => {
          const active = opt.value === typeRepas;
          return (
            <Pressable
              key={opt.value}
              onPress={() => setTypeRepas(opt.value)}
              style={[styles.chip, active && styles.chipActive]}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>{opt.label}</Text>
            </Pressable>
          );
        })}
      </View>

      <Text style={styles.section}>Temps disponible</Text>
      <View style={styles.chips}>
        {DUREE_OPTIONS.map((opt) => {
          const active = opt.value === dureeMax;
          return (
            <Pressable
              key={opt.label}
              onPress={() => setDureeMax(opt.value)}
              style={[styles.chip, active && styles.chipActive]}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>{opt.label}</Text>
            </Pressable>
          );
        })}
      </View>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {recette ? (
        <View style={styles.card}>
          <Text style={styles.nom}>{recette.nom}</Text>
          <View style={styles.metaRow}>
            <Text style={styles.meta}>{Math.round(recette.kcal_total)} kcal</Text>
            {recette.duree_minutes ? (
              <Text style={styles.meta}>~{recette.duree_minutes} min</Text>
            ) : null}
            <Text style={styles.meta}>
              Stock : {Math.round(suggestion.couverture_stock * 100)}%
            </Text>
          </View>

          <AiText content={suggestion.message} />

          <Text style={styles.sub}>Ingredients</Text>
          {recette.ingredients.map((ligne) => {
            const manque = manquants.has(ligne.ingredient.nom.toLowerCase());
            return (
              <View key={ligne.ingredient.id} style={styles.ingredientRow}>
                <Text style={styles.ingredientNom}>
                  {manque ? "✗ " : "✓ "}
                  {ligne.ingredient.nom}
                </Text>
                <Text style={styles.ingredientQty}>
                  {ligne.poids_requis} {ligne.unite}
                </Text>
              </View>
            );
          })}

          {recette.instructions ? (
            <>
              <Text style={styles.sub}>Preparation</Text>
              <Body>{recette.instructions}</Body>
            </>
          ) : null}
        </View>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  actions: { gap: space.sm },
  section: {
    marginTop: space.sm,
    fontSize: type.label,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
    letterSpacing: 0.3,
  },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  chip: {
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
  },
  chipActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  chipText: { color: colors.ink, fontSize: type.body },
  chipTextActive: { color: "#F7F3EA", fontWeight: "600" },
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.md,
    gap: space.sm,
  },
  nom: { fontSize: type.title, fontWeight: "700", color: colors.ink },
  metaRow: { flexDirection: "row", flexWrap: "wrap", gap: space.md },
  meta: { fontSize: type.small, color: colors.muted, fontWeight: "600" },
  sub: {
    fontSize: type.label,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
    marginTop: space.xs,
  },
  ingredientRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 4,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
  },
  ingredientNom: { fontSize: type.body, color: colors.ink },
  ingredientQty: { fontSize: type.body, color: colors.muted },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
});
