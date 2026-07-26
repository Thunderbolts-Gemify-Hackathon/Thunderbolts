import { Pressable, StyleSheet, Text } from "react-native";

import { colors, radius, space, type } from "@/theme";

type Props = {
  label: string;
  onPress: () => void;
  variant?: "primary" | "ghost";
  disabled?: boolean;
  rounded?: boolean;
};

export function Button({
  label,
  onPress,
  variant = "primary",
  disabled,
  rounded,
}: Props) {
  const primary = variant === "primary";
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        rounded && styles.pill,
        primary ? styles.primary : styles.ghost,
        (pressed || disabled) && { opacity: disabled ? 0.4 : 0.85 },
      ]}
    >
      <Text style={[styles.label, primary ? styles.labelPrimary : styles.labelGhost]}>
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: 52,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: space.lg,
  },
  pill: { minHeight: 56, borderRadius: 999 },
  primary: { backgroundColor: colors.brand },
  ghost: {
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: colors.line,
  },
  label: { fontSize: type.body, fontWeight: "600" },
  labelPrimary: { color: "#F7F3EA" },
  labelGhost: { color: colors.ink },
});
