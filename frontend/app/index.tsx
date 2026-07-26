import { Redirect, useRouter } from "expo-router";
import { Image, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useOnboarding } from "@/onboarding/store";
import { Button } from "@/ui/Button";
import { CurveBackdrop } from "@/ui/CurveBackdrop";
import { Brand } from "@/ui/Typography";
import { colors, space } from "@/theme";

export default function WelcomeScreen() {
  const router = useRouter();
  const { done } = useOnboarding();

  if (done) return <Redirect href="/dashboard" />;

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <CurveBackdrop color={colors.brandSoft}>
        <Image
          source={require("../assets/pan.png")}
          style={styles.illustration}
          resizeMode="contain"
        />
      </CurveBackdrop>

      <View style={styles.content}>
        <Brand style={styles.brand}>Kaly Tao</Brand>
      </View>

      <View style={styles.actions}>
        <Button label="Commencer" onPress={() => router.push("/signup")} rounded />
        <Text style={styles.footerText}>
          Déjà un compte ?{" "}
          <Text style={styles.link} onPress={() => router.push("/signin")}>
            Se connecter
          </Text>
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  illustration: {
    width: "68%",
    aspectRatio: 380 / 513,
  },
  content: {
    gap: space.sm,
    paddingHorizontal: space.lg,
    paddingTop: space.lg,
    alignItems: "center",
  },
  brand: { textAlign: "center" },
  actions: {
    paddingHorizontal: space.lg,
    paddingTop: space.lg,
    paddingBottom: space.lg,
    gap: space.sm,
  },
  footerText: { textAlign: "center", color: colors.muted, fontSize: 16 },
  link: { color: colors.brand, fontWeight: "700" },
});
