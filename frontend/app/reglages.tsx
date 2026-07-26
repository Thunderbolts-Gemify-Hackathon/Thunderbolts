import { Feather } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";

import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

const SECTIONS: { icon: keyof typeof Feather.glyphMap; label: string }[] = [
  { icon: "bell", label: "Notifications" },
  { icon: "shield", label: "Confidentialité" },
  { icon: "globe", label: "Langue" },
  { icon: "help-circle", label: "Aide" },
];

export default function ReglagesScreen() {
  return (
    <Screen>
      <Title>Réglages</Title>
      <Body>D'autres options arrivent bientôt.</Body>

      {SECTIONS.map((s) => (
        <View key={s.label} style={styles.row}>
          <Feather name={s.icon} size={18} color={colors.muted} />
          <Text style={styles.label}>{s.label}</Text>
          <Feather name="chevron-right" size={18} color={colors.muted} />
        </View>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.sm,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.md,
  },
  label: { flex: 1, fontSize: type.body, color: colors.ink, fontWeight: "600" },
});
