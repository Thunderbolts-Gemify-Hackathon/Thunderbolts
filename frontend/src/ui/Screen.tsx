import { ReactNode } from "react";
import { ScrollView, StyleSheet, View, ViewStyle } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { NAV_CLEARANCE } from "@/ui/BottomNavBar";
import { colors, space } from "@/theme";

type Props = {
  children: ReactNode;
  footer?: ReactNode;
  style?: ViewStyle;
  /** Écrans sans barre de navigation flottante (auth, onboarding) : pas d'espace réservé. */
  noNavClearance?: boolean;
};

export function Screen({ children, footer, style, noNavClearance }: Props) {
  const clearance = noNavClearance ? 0 : NAV_CLEARANCE;
  return (
    <SafeAreaView style={styles.safe} edges={["top", "left", "right"]}>
      <ScrollView
        contentContainerStyle={[
          styles.content,
          { paddingBottom: space.xl + clearance },
          style,
        ]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {children}
      </ScrollView>
      {footer ? (
        <View style={[styles.footer, { paddingBottom: space.lg + clearance }]}>
          {footer}
        </View>
      ) : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: {
    paddingHorizontal: space.lg,
    paddingTop: space.md,
    gap: space.md,
    maxWidth: 480,
    width: "100%",
    alignSelf: "center",
  },
  footer: {
    paddingHorizontal: space.lg,
    paddingTop: space.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.line,
    backgroundColor: colors.bg,
    maxWidth: 480,
    width: "100%",
    alignSelf: "center",
  },
});
