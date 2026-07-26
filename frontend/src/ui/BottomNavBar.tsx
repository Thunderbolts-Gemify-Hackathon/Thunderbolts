import { Ionicons } from "@expo/vector-icons";
import { type Href, usePathname, useRouter } from "expo-router";
import { Pressable, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { colors } from "@/theme";

/** Espace réservé en bas des écrans pour ne pas être masqué par la barre flottante. */
export const NAV_CLEARANCE = 78;

type IconName = keyof typeof Ionicons.glyphMap;

type Tab = {
  key: string;
  route: Href;
  outline: IconName;
  filled: IconName;
};

const TABS: Tab[] = [
  { key: "home", route: "/dashboard", outline: "home-outline", filled: "home" },
  { key: "folder", route: "/courses", outline: "folder-outline", filled: "folder" },
  { key: "calendar", route: "/planning", outline: "calendar-outline", filled: "calendar" },
  { key: "profil", route: "/profil", outline: "person-outline", filled: "person" },
  { key: "reglages", route: "/reglages", outline: "settings-outline", filled: "settings" },
];

const HIDDEN_PREFIXES = [
  "/signup",
  "/signin",
  "/welcome",
  "/onboarding",
  "/recette",
  "/map",
  "/cuisiner",
];

export function BottomNavBar() {
  const pathname = usePathname();
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const hidden =
    pathname === "/" || HIDDEN_PREFIXES.some((p) => pathname.startsWith(p));
  if (hidden) return null;

  return (
    <View
      style={[styles.wrap, { bottom: Math.max(insets.bottom, 10) + 10 }]}
      pointerEvents="box-none"
    >
      <View style={styles.pill}>
        {TABS.map((tab) => {
          const routePath = String(tab.route);
          const active =
            pathname === routePath || pathname.startsWith(`${routePath}/`);
          return (
            <Pressable
              key={tab.key}
              accessibilityRole="button"
              hitSlop={8}
              onPress={() => {
                if (!active) router.push(tab.route);
              }}
              style={styles.item}
            >
              <View style={[styles.iconWrap, active && styles.iconWrapActive]}>
                <Ionicons
                  name={active ? tab.filled : tab.outline}
                  size={20}
                  color={active ? "#F7F3EA" : "#ADB0B8"}
                />
              </View>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    position: "absolute",
    left: 0,
    right: 0,
    alignItems: "center",
  },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.surface,
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 6,
    shadowColor: "#000",
    shadowOpacity: 0.14,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 10 },
    elevation: 12,
  },
  item: {
    width: 52,
    height: 52,
    alignItems: "center",
    justifyContent: "center",
  },
  iconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  iconWrapActive: {
    backgroundColor: colors.brand,
  },
});
