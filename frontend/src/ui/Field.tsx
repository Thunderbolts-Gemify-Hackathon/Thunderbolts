import { StyleSheet, Text, TextInput, View } from "react-native";

import { colors, radius, space, type } from "@/theme";

type Props = {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  keyboard?: "default" | "email-address" | "numeric";
};

export function Field({ label, value, onChange, placeholder, keyboard = "default" }: Props) {
  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder={placeholder}
        placeholderTextColor={colors.muted}
        keyboardType={keyboard}
        autoCapitalize={keyboard === "email-address" ? "none" : "sentences"}
        // Sur un chiffre prérempli, un tap sélectionne tout : la saisie remplace
        // au lieu d'obliger à effacer à la main (ex. nombre de personnes).
        selectTextOnFocus={keyboard === "numeric"}
        style={styles.input}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: space.xs },
  label: {
    fontSize: type.label,
    color: colors.muted,
    fontWeight: "600",
    letterSpacing: 0.3,
    textTransform: "uppercase",
  },
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
});
