import { Feather, Ionicons } from "@expo/vector-icons";
import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { colors, radius, space, type } from "@/theme";

type Props = {
  placeholder?: string;
  suggestions: string[];
  onAdd: (nom: string) => void;
};

/** Barre "Ajouter un article" avec autocomplétion (façon liste de courses classique). */
export function AddItemBar({ placeholder = "Ajouter un article…", suggestions, onAdd }: Props) {
  const [query, setQuery] = useState("");

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return suggestions.filter((s) => s.toLowerCase().includes(q)).slice(0, 6);
  }, [query, suggestions]);

  const exactMatch = matches.some((m) => m.toLowerCase() === query.trim().toLowerCase());
  const showFreeAdd = query.trim().length > 1 && !exactMatch;
  // Note : pas de dépendance à l'état "focus" du champ, pour éviter que le
  // clavier/blur ne fasse disparaître le panneau avant que le tap ne soit pris en compte.
  const showPanel = query.trim().length > 0;

  const commit = (nom: string) => {
    onAdd(nom);
    setQuery("");
  };

  return (
    <View style={styles.wrap}>
      <View style={styles.inputRow}>
        <Feather name="search" size={18} color={colors.muted} />
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder={placeholder}
          placeholderTextColor={colors.muted}
          style={styles.input}
          returnKeyType="done"
          onSubmitEditing={() => query.trim() && commit(query.trim())}
        />
      </View>

      {showPanel ? (
        <View style={styles.panel}>
          {matches.map((nom, i) => (
            <Pressable
              key={nom}
              onPress={() => commit(nom)}
              style={[styles.row, i < matches.length - 1 && styles.rowDivider]}
            >
              <Ionicons name="add-circle-outline" size={20} color={colors.brand} />
              <Text style={styles.rowLabel}>{nom}</Text>
            </Pressable>
          ))}
          {showFreeAdd ? (
            <Pressable
              onPress={() => commit(query.trim())}
              style={[styles.row, matches.length > 0 && styles.rowDivider]}
            >
              <Ionicons name="add-circle-outline" size={20} color={colors.accent} />
              <Text style={styles.rowLabel}>
                Ajouter « {query.trim()} »
              </Text>
            </Pressable>
          ) : null}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 0 },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.sm,
    backgroundColor: colors.surface,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.line,
    paddingHorizontal: space.md,
    height: 48,
  },
  input: { flex: 1, fontSize: type.body, color: colors.ink },
  panel: {
    marginTop: space.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    overflow: "hidden",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.sm,
    paddingVertical: space.sm + 2,
    paddingHorizontal: space.md,
  },
  rowDivider: { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.line },
  rowLabel: { fontSize: type.body, color: colors.ink, flexShrink: 1 },
});
