import { Feather } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type { Recette } from "@/api/repas";
import { recetteVisual } from "@/lib/recipeVisual";
import { colors, radius, space, type } from "@/theme";

type Props = {
  recette: Recette;
  statut?: string;
  onPress: () => void;
};

export function RecipeCard({ recette, statut, onPress }: Props) {
  const visual = recetteVisual(recette);
  const consomme = statut === "consomme";

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && { opacity: 0.85 }]}
    >
      <View style={[styles.hero, { backgroundColor: visual.bg }]}>
        <Text style={styles.emoji}>{visual.emoji}</Text>
        {consomme ? (
          <View style={styles.badge}>
            <Feather name="check" size={12} color="#F7F3EA" />
          </View>
        ) : null}
      </View>
      <Text style={styles.nom} numberOfLines={2}>
        {recette.nom}
      </Text>
      <View style={styles.metaRow}>
        <Text style={styles.meta}>{Math.round(recette.kcal_total)} kcal</Text>
        {recette.duree_minutes ? (
          <Text style={styles.meta}>· {recette.duree_minutes} min</Text>
        ) : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { width: "31%", gap: 6 },
  hero: {
    width: "100%",
    aspectRatio: 1.15,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
  },
  emoji: { fontSize: 34 },
  badge: {
    position: "absolute",
    top: 8,
    right: 8,
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.brand,
    alignItems: "center",
    justifyContent: "center",
  },
  nom: { fontSize: type.small, fontWeight: "700", color: colors.ink, lineHeight: 16 },
  metaRow: { flexDirection: "row", gap: 4 },
  meta: { fontSize: 11, color: colors.muted, fontWeight: "600" },
});
