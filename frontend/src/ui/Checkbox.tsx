import { ReactNode } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, space, type } from "@/theme";

type Props = {
  checked: boolean;
  onToggle: () => void;
  children: ReactNode;
};

export function Checkbox({ checked, onToggle, children }: Props) {
  return (
    <Pressable
      style={styles.row}
      onPress={onToggle}
      accessibilityRole="checkbox"
      accessibilityState={{ checked }}
    >
      <View style={[styles.box, checked && styles.boxChecked]}>
        {checked ? <Text style={styles.mark}>✓</Text> : null}
      </View>
      <Text style={styles.label}>{children}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "flex-start", gap: space.sm },
  box: {
    width: 22,
    height: 22,
    borderRadius: radius.sm - 4,
    borderWidth: 1.5,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
  },
  boxChecked: { backgroundColor: colors.brand, borderColor: colors.brand },
  mark: { color: "#F7F3EA", fontSize: 13, fontWeight: "700" },
  label: { flex: 1, fontSize: type.body, color: colors.ink, lineHeight: 20 },
});
