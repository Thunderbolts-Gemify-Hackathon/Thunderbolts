import { Feather } from "@expo/vector-icons";
import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { colors, space, type } from "@/theme";

type Props = {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  error?: string;
  onBlur?: () => void;
};

export function AuthPasswordField({ value, onChange, placeholder, error, onBlur }: Props) {
  const [visible, setVisible] = useState(false);
  const [focused, setFocused] = useState(false);
  const showError = !!error && !focused;

  return (
    <View>
      <View style={[styles.wrap, focused && styles.wrapFocused, showError && styles.wrapError]}>
        <Feather
          name="lock"
          size={18}
          color={showError ? colors.danger : focused ? colors.brand : colors.muted}
        />
        <TextInput
          value={value}
          onChangeText={onChange}
          placeholder={placeholder}
          placeholderTextColor={colors.muted}
          secureTextEntry={!visible}
          autoCapitalize="none"
          autoCorrect={false}
          onFocus={() => setFocused(true)}
          onBlur={() => {
            setFocused(false);
            onBlur?.();
          }}
          style={styles.input}
        />
        <Pressable
          onPress={() => setVisible((v) => !v)}
          accessibilityRole="button"
          accessibilityLabel={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
          hitSlop={8}
        >
          <Feather name={visible ? "eye-off" : "eye"} size={18} color={colors.muted} />
        </Pressable>
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
