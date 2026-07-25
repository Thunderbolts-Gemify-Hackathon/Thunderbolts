import { useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { ApiError } from "@/api/http";
import {
  getStock,
  listIngredients,
  nameById,
  upsertStockLine,
  type Ingredient,
  type StockLine,
} from "@/api/stock";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

export default function StockScreen() {
  const router = useRouter();
  const { session } = useSession();
  const profilId = session?.profilId;
  const token = session?.apiToken;

  const [catalog, setCatalog] = useState<Ingredient[]>([]);
  const [lines, setLines] = useState<StockLine[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [qty, setQty] = useState("200");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const byId = useMemo(() => nameById(catalog), [catalog]);
  const selected = selectedId ? byId[selectedId] : undefined;

  const load = useCallback(async () => {
    if (!profilId || !token) {
      setError("Session invalide. Refais l'onboarding.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [ings, stock] = await Promise.all([
        listIngredients(token),
        getStock(profilId, token),
      ]);
      setCatalog(ings);
      setLines(stock);
      setSelectedId((prev) => prev ?? ings[0]?.id ?? null);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Chargement impossible");
    } finally {
      setLoading(false);
    }
  }, [profilId, token]);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    if (!profilId || !token || !selected) return;
    const quantite = Number(qty);
    if (!Number.isFinite(quantite) || quantite < 0) {
      setError("Quantité invalide.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await upsertStockLine(
        profilId,
        {
          ingredient_id: selected.id,
          quantite_disponible: quantite,
          unite: selected.unite_defaut,
        },
        token
      );
      const stock = await getStock(profilId, token);
      setLines(stock);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Enregistrement impossible");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label={saving ? "Enregistrement…" : "Enregistrer dans le stock"}
            onPress={() => void save()}
            disabled={saving || loading || !selected}
          />
          <Button label="Retour" variant="ghost" onPress={() => router.back()} />
        </View>
      }
    >
      <Title>Mon stock</Title>
      <Body>Ajoute ou mets à jour ce que tu as en cuisine.</Body>

      {loading ? <ActivityIndicator color={colors.brand} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Text style={styles.section}>Ingrédient</Text>
      <View style={styles.chips}>
        {catalog.map((ing) => {
          const active = ing.id === selectedId;
          return (
            <Pressable
              key={ing.id}
              onPress={() => setSelectedId(ing.id)}
              style={[styles.chip, active && styles.chipActive]}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>
                {ing.nom}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <Text style={styles.section}>
        Quantité {selected ? `(${selected.unite_defaut})` : ""}
      </Text>
      <TextInput
        value={qty}
        onChangeText={setQty}
        keyboardType="numeric"
        style={styles.input}
        placeholder="200"
        placeholderTextColor={colors.muted}
      />

      <Text style={styles.section}>En cuisine maintenant</Text>
      {lines.length === 0 ? (
        <Body>Aucun ingrédient enregistré.</Body>
      ) : (
        lines.map((line) => {
          const ing = byId[line.ingredient_id];
          return (
            <View key={line.id} style={styles.row}>
              <Text style={styles.rowName}>{ing?.nom ?? line.ingredient_id}</Text>
              <Text style={styles.rowQty}>
                {line.quantite_disponible} {line.unite}
              </Text>
            </View>
          );
        })
      )}
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
  input: {
    minHeight: 50,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    paddingHorizontal: space.md,
    fontSize: type.body,
    color: colors.ink,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: space.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
  },
  rowName: { fontSize: type.body, color: colors.ink, fontWeight: "600" },
  rowQty: { fontSize: type.body, color: colors.muted },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
});
