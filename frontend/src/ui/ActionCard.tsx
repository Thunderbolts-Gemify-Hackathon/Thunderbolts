import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { radius, space, type } from "@/theme";

type Props = {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  subtitle: string;
  tint: string;
  onPress: () => void;
};

/** Carte colorée pour le carousel "à la une" du dashboard (remplace les gros boutons empilés). */
export function ActionCard({ icon, title, subtitle, tint, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, { backgroundColor: tint }, pressed && { opacity: 0.85 }]}
    >
      <View style={styles.iconWrap}>
        <Ionicons name={icon} size={22} color="#F7F3EA" />
      </View>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    width: 168,
    minHeight: 140,
    borderRadius: radius.lg,
    padding: space.md,
    justifyContent: "space-between",
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "rgba(247,243,234,0.22)",
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: type.body,
    fontWeight: "700",
    color: "#F7F3EA",
    marginTop: space.sm,
  },
  subtitle: {
    fontSize: type.small,
    color: "rgba(247,243,234,0.85)",
    marginTop: 2,
  },
});
