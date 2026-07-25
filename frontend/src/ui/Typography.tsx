import { StyleSheet, Text, TextProps } from "react-native";

import { colors, type } from "@/theme";

export function Brand({ children, ...rest }: TextProps) {
  return (
    <Text {...rest} style={[styles.brand, rest.style]}>
      {children}
    </Text>
  );
}

export function Title({ children, ...rest }: TextProps) {
  return (
    <Text {...rest} style={[styles.title, rest.style]}>
      {children}
    </Text>
  );
}

export function Body({ children, ...rest }: TextProps) {
  return (
    <Text {...rest} style={[styles.body, rest.style]}>
      {children}
    </Text>
  );
}

const styles = StyleSheet.create({
  brand: {
    fontSize: type.brand,
    fontWeight: "700",
    color: colors.brand,
    letterSpacing: -0.5,
  },
  title: {
    fontSize: type.title,
    fontWeight: "700",
    color: colors.ink,
    letterSpacing: -0.3,
  },
  body: {
    fontSize: type.body,
    color: colors.muted,
    lineHeight: 24,
  },
});
