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
  createIngredient,
  deleteStockLine,
  getStock,
  listIngredients,
  nameById,
  upsertStockLine,
  type Ingredient,
  type StockLine,
  type Unite,
} from "@/api/stock";
import { importStockImage, importStockText, type StockImportLine } from "@/api/stockImport";
import { enqueueMutation } from "@/lib/offlineQueue";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

type ImageSource = "camera" | "library";

async function captureImageBase64(source: ImageSource): Promise<string | null> {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const ImagePicker = require("expo-image-picker");
    if (source === "camera") {
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (perm.status !== "granted" && perm.granted !== true) return null;
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions?.Images ?? ["images"],
        base64: true,
        quality: 0.65,
        allowsEditing: true,
      });
      if (result.canceled || !result.assets?.[0]?.base64) return null;
      return result.assets[0].base64 as string;
    }
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (perm.status !== "granted" && perm.granted !== true) return null;
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions?.Images ?? ["images"],
      base64: true,
      quality: 0.65,
    });
    if (result.canceled || !result.assets?.[0]?.base64) return null;
    return result.assets[0].base64 as string;
  } catch {
    return null;
  }
}

type UnitGroupKey = "poids" | "liquides" | "unites" | "autre";

const UNIT_GROUPS: { key: UnitGroupKey; label: string; units: string[] }[] = [
  { key: "poids", label: "Poids (kg)", units: ["g", "kg"] },
  { key: "liquides", label: "Liquides (L)", units: ["ml", "l"] },
  { key: "unites", label: "A la piece", units: ["unite"] },
];

const UNITE_OPTIONS: { value: Unite; label: string }[] = [
  { value: "g", label: "g" },
  { value: "kg", label: "kg" },
  { value: "ml", label: "ml" },
  { value: "l", label: "L" },
  { value: "unite", label: "unite" },
];

function groupOf(unite: string): UnitGroupKey {
  const found = UNIT_GROUPS.find((g) => g.units.includes(unite));
  return found?.key ?? "autre";
}

function formatQuantity(qty: number, unite: string): string {
  const rounded = (n: number) => Math.round(n * 100) / 100;
  if (unite === "g" && qty >= 1000) return `${rounded(qty / 1000)} kg`;
  if (unite === "ml" && qty >= 1000) return `${rounded(qty / 1000)} L`;
  if (unite === "l") return `${rounded(qty)} L`;
  if (unite === "unite") return `${rounded(qty)} ${qty > 1 ? "unites" : "unite"}`;
  return `${rounded(qty)} ${unite}`;
}

function daysUntil(dateIso: string | null): number | null {
  if (!dateIso) return null;
  const diffMs = new Date(dateIso).getTime() - new Date().setHours(0, 0, 0, 0);
  return Math.ceil(diffMs / 86_400_000);
}

export default function StockScreen() {
  const router = useRouter();
  const { session } = useSession();
  const profilId = session?.sharedProfilId || session?.profilId;
  const token = session?.apiToken;

  const [catalog, setCatalog] = useState<Ingredient[]>([]);
  const [lines, setLines] = useState<StockLine[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [qty, setQty] = useState("200");
  const [expiry, setExpiry] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [showNewProduct, setShowNewProduct] = useState(false);
  const [newNom, setNewNom] = useState("");
  const [newUnite, setNewUnite] = useState<Unite>("g");
  const [creatingProduct, setCreatingProduct] = useState(false);
  const [importText, setImportText] = useState("");
  const [importPreview, setImportPreview] = useState<StockImportLine[] | null>(null);
  const [importing, setImporting] = useState(false);

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
      setError("Quantite invalide.");
      return;
    }
    setSaving(true);
    setError(null);
    const payload = {
      ingredient_id: selected.id,
      quantite_disponible: quantite,
      unite: selected.unite_defaut as Unite,
      date_peremption: expiry.trim() || null,
    };
    try {
      await upsertStockLine(profilId, payload, token);
      setExpiry("");
      const stock = await getStock(profilId, token);
      setLines(stock);
    } catch (e) {
      await enqueueMutation({
        method: "POST",
        path: `/stock/${profilId}/ingredients`,
        body: payload,
        token,
      });
      setError(
        e instanceof ApiError
          ? `${e.detail} (mis en file hors-ligne)`
          : "Hors ligne — enregistré dans la file."
      );
    } finally {
      setSaving(false);
    }
  };

  const remove = async (ingredientId: string) => {
    if (!profilId || !token) return;
    setRemovingId(ingredientId);
    setError(null);
    try {
      await deleteStockLine(profilId, ingredientId, token);
      setLines((prev) => prev.filter((l) => l.ingredient_id !== ingredientId));
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Suppression impossible");
    } finally {
      setRemovingId(null);
    }
  };

  const createProduct = async () => {
    if (!token || !newNom.trim()) return;
    setCreatingProduct(true);
    setError(null);
    try {
      const created = await createIngredient(
        { nom: newNom.trim(), unite_defaut: newUnite },
        token
      );
      setCatalog((prev) => [...prev, created].sort((a, b) => a.nom.localeCompare(b.nom)));
      setSelectedId(created.id);
      setNewNom("");
      setShowNewProduct(false);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Creation du produit impossible");
    } finally {
      setCreatingProduct(false);
    }
  };

  const previewImport = async () => {
    if (!profilId || !token || !importText.trim()) return;
    setImporting(true);
    setError(null);
    try {
      const res = await importStockText(profilId, token, {
        text: importText,
        apply: false,
      });
      setImportPreview(res.lines);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Analyse impossible");
    } finally {
      setImporting(false);
    }
  };

  const applyImport = async () => {
    if (!profilId || !token || !importText.trim()) return;
    setImporting(true);
    setError(null);
    try {
      const res = await importStockText(profilId, token, {
        text: importText,
        apply: true,
      });
      setImportPreview(res.lines);
      setImportText("");
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Import impossible");
    } finally {
      setImporting(false);
    }
  };

  const importFromImage = async (source: ImageSource) => {
    if (!profilId || !token) return;
    setImporting(true);
    setError(null);
    try {
      const b64 = await captureImageBase64(source);
      if (!b64) {
        setError(
          source === "camera"
            ? "Caméra refusée ou annulée. Autorise la caméra, ou choisis une photo."
            : "Galerie refusée ou annulée. Autorise l'accès photos, ou prends une photo."
        );
        return;
      }
      const res = await importStockImage(profilId, token, {
        image_base64: b64,
        apply: false,
      });
      setImportPreview(res.lines);
      if (!res.lines.length) {
        setError("Aucun produit reconnu. Réessaie avec un ticket plus lisible ou du texte.");
      }
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.detail
          : "OCR indisponible — colle le texte du ticket à la place."
      );
    } finally {
      setImporting(false);
    }
  };

  const applyPhotoPreview = async () => {
    if (!profilId || !token || !importPreview?.length) return;
    const lines = importPreview
      .filter((l) => l.matched)
      .map((l) => `${l.label} ${l.quantite}${l.unite}`)
      .join("\n");
    if (!lines) {
      setError("Aucun produit reconnu à appliquer.");
      return;
    }
    setImporting(true);
    setError(null);
    try {
      await importStockText(profilId, token, { text: lines, apply: true });
      setImportPreview(null);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Application impossible");
    } finally {
      setImporting(false);
    }
  };

  const groupedLines = useMemo(() => {
    const groups = new Map<UnitGroupKey, StockLine[]>();
    for (const line of lines) {
      const key = groupOf(line.unite);
      groups.set(key, [...(groups.get(key) ?? []), line]);
    }
    return groups;
  }, [lines]);

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

      <Text style={styles.section}>Import rapide</Text>
      <Body>
        Prends une photo du ticket / placard, choisis une image, ou colle du texte « tomate 500g ».
      </Body>
      <TextInput
        value={importText}
        onChangeText={setImportText}
        placeholder={"tomate 500g\nriz 1kg\noeufs 6"}
        placeholderTextColor={colors.muted}
        style={[styles.input, styles.importBox]}
        multiline
      />
      <View style={styles.importActions}>
        <Button
          label={importing ? "…" : "Prendre une photo"}
          onPress={() => void importFromImage("camera")}
          disabled={importing}
        />
        <Button
          label={importing ? "…" : "Galerie"}
          variant="ghost"
          onPress={() => void importFromImage("library")}
          disabled={importing}
        />
        <Button
          label={importing ? "…" : "Aperçu texte"}
          variant="ghost"
          onPress={() => void previewImport()}
          disabled={importing || !importText.trim()}
        />
        <Button
          label={importing ? "Import…" : "Appliquer texte"}
          variant="ghost"
          onPress={() => void applyImport()}
          disabled={importing || !importText.trim()}
        />
      </View>
      {importPreview?.some((l) => l.matched) && !importText.trim() ? (
        <Button
          label={importing ? "…" : "Appliquer l'aperçu photo au stock"}
          onPress={() => void applyPhotoPreview()}
          disabled={importing}
        />
      ) : null}
      {importPreview ? (
        <View style={styles.card}>
          {importPreview.map((line, i) => (
            <Text key={`${line.label}-${i}`} style={styles.meta}>
              {line.matched ? "✓" : "?"} {line.label} · {line.quantite}
              {line.unite}
            </Text>
          ))}
        </View>
      ) : null}

      <Text style={styles.section}>Produit</Text>
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
                {ing.nom} · {ing.unite_defaut}
              </Text>
            </Pressable>
          );
        })}
        <Pressable
          onPress={() => setShowNewProduct((v) => !v)}
          style={[styles.chip, styles.chipDashed]}
        >
          <Text style={styles.chipText}>
            {showNewProduct ? "Annuler" : "+ Nouveau produit"}
          </Text>
        </Pressable>
      </View>

      {showNewProduct ? (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Nouveau produit</Text>
          <TextInput
            value={newNom}
            onChangeText={setNewNom}
            placeholder="Nom du produit"
            placeholderTextColor={colors.muted}
            style={styles.input}
          />
          <View style={styles.chips}>
            {UNITE_OPTIONS.map((opt) => {
              const active = opt.value === newUnite;
              return (
                <Pressable
                  key={opt.value}
                  onPress={() => setNewUnite(opt.value)}
                  style={[styles.chip, active && styles.chipActive]}
                >
                  <Text style={[styles.chipText, active && styles.chipTextActive]}>
                    {opt.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
          <Button
            label={creatingProduct ? "Creation…" : "Creer le produit"}
            onPress={() => void createProduct()}
            disabled={creatingProduct || !newNom.trim()}
          />
        </View>
      ) : null}

      <Text style={styles.section}>
        Quantite {selected ? `(${selected.unite_defaut})` : ""}
      </Text>
      <TextInput
        value={qty}
        onChangeText={setQty}
        keyboardType="numeric"
        style={styles.input}
        placeholder="200"
        placeholderTextColor={colors.muted}
      />

      <Text style={styles.section}>Date de peremption (optionnel)</Text>
      <TextInput
        value={expiry}
        onChangeText={setExpiry}
        style={styles.input}
        placeholder="AAAA-MM-JJ"
        placeholderTextColor={colors.muted}
      />

      <Text style={styles.section}>En cuisine maintenant</Text>
      {lines.length === 0 ? (
        <Body>Aucun ingredient enregistre.</Body>
      ) : (
        UNIT_GROUPS.map((group) => {
          const groupLines = groupedLines.get(group.key);
          if (!groupLines || groupLines.length === 0) return null;
          return (
            <View key={group.key} style={styles.group}>
              <Text style={styles.groupLabel}>{group.label}</Text>
              {groupLines.map((line) => {
                const ing = byId[line.ingredient_id];
                const jours = daysUntil(line.date_peremption);
                const tone =
                  jours !== null && jours <= 3
                    ? "danger"
                    : jours !== null && jours <= 7
                      ? "warn"
                      : null;
                return (
                  <View key={line.id} style={styles.row}>
                    <View style={styles.rowMain}>
                      <Text style={styles.rowName}>{ing?.nom ?? line.ingredient_id}</Text>
                      {jours !== null ? (
                        <Text
                          style={[
                            styles.badge,
                            tone === "danger" && styles.badgeDanger,
                            tone === "warn" && styles.badgeWarn,
                          ]}
                        >
                          {jours < 0
                            ? "perime"
                            : jours === 0
                              ? "perime aujourd'hui"
                              : `perime dans ${jours} j`}
                        </Text>
                      ) : null}
                    </View>
                    <Text style={styles.rowQty}>
                      {formatQuantity(line.quantite_disponible, line.unite)}
                    </Text>
                    <Pressable
                      onPress={() => void remove(line.ingredient_id)}
                      disabled={removingId === line.ingredient_id}
                      style={styles.removeBtn}
                    >
                      <Text style={styles.removeLabel}>
                        {removingId === line.ingredient_id ? "…" : "Retirer"}
                      </Text>
                    </Pressable>
                  </View>
                );
              })}
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
  chipDashed: { borderStyle: "dashed" },
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
    paddingVertical: space.sm,
    fontSize: type.body,
    color: colors.ink,
  },
  importBox: { minHeight: 90, textAlignVertical: "top" },
  importActions: { flexDirection: "row", gap: space.sm, flexWrap: "wrap" },
  meta: { fontSize: type.small, color: colors.muted },
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.md,
    gap: space.sm,
  },
  cardLabel: {
    fontSize: type.label,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
  },
  group: { gap: 4, marginTop: space.xs },
  groupLabel: {
    fontSize: type.small,
    fontWeight: "700",
    color: colors.brand,
    marginTop: space.sm,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: space.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
    gap: space.sm,
  },
  rowMain: { flex: 1, gap: 2 },
  rowName: { fontSize: type.body, color: colors.ink, fontWeight: "600" },
  rowQty: { fontSize: type.body, color: colors.muted },
  badge: {
    alignSelf: "flex-start",
    fontSize: type.small,
    color: colors.muted,
  },
  badgeWarn: { color: colors.accent },
  badgeDanger: { color: colors.danger, fontWeight: "700" },
  removeBtn: {
    paddingHorizontal: space.sm,
    paddingVertical: 4,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.line,
  },
  removeLabel: { color: colors.danger, fontSize: type.small, fontWeight: "600" },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
});
