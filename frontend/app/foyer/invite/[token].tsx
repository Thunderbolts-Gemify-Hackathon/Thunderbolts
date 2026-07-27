import { type Href, useLocalSearchParams, useRouter } from "expo-router";
import { useEffect } from "react";
import { ActivityIndicator, View } from "react-native";

import { colors } from "@/theme";

/** Deep link kalitao://foyer/invite/:token → écran accept. */
export default function FoyerInviteDeepLink() {
  const { token } = useLocalSearchParams<{ token: string }>();
  const router = useRouter();

  useEffect(() => {
    if (token) {
      router.replace(
        (`/foyer/accept?token=${encodeURIComponent(token)}` as Href)
      );
    } else {
      router.replace("/foyer/accept" as Href);
    }
  }, [token, router]);

  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
      <ActivityIndicator color={colors.brand} />
    </View>
  );
}
