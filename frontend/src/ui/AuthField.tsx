import { Feather } from "@expo/vector-icons";
import { useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";

import { colors, space, type } from "@/theme";

type Props = {
  icon: keyof typeof Feather.glyphMap;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  keyboard?: "default" | "email-address" | "numeric";
  error?: string;
  onBlur?: () => void;
};

export function AuthField({
  icon,
  value,
  onChange,
  placeholder,
  keyboard = "default",
  error,
  onBlur,
}: Props) {
  const [focused, setFocused] = useState(false);
  const showError = !!error && !focused;

  return (
    <View>
      <View style={[styles.wrap, focused && styles.wrapFocused, showError && styles.wrapError]}>
        <Feather
          name={icon}
          size={18}
          color={showError ? colors.danger : focused ? colors.brand : colors.muted}
        />
        <TextInput
          value={value}
          onChangeText={onChange}
          placeholder={placeholder}
          placeholderTextColor={colors.muted}
          keyboardType={keyboard}
          autoCapitalize={keyboard === "email-address" ? "none" : "sentences"}
          onFocus={() => setFocused(true)}
          onBlur={() => {
            setFocused(false);
            onBlur?.();
          }}
          style={styles.input}
        />
      </View>
      {showError ? <Text style={styles.errorText}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: "row",
    alignItems: "center",
    minHeight: 56,
    borderWidth: 1.5,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: 999,
    paddingHorizontal: space.lg,
    gap: space.sm,
  },
  wrapFocused: { borderColor: colors.brand },
  wrapError: { borderColor: colors.danger },
  input: { flex: 1, fontSize: type.body, color: colors.ink, paddingVertical: space.sm },
  errorText: {
    color: colors.danger,
    fontSize: type.small,
    fontWeight: "600",
    marginTop: 4,
    marginLeft: space.lg,
  },
});
