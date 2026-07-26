import { Redirect, useRouter } from "expo-router";
import { Image, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useOnboarding } from "@/onboarding/store";
import { STEP_IDS } from "@/onboarding/steps";
import { Button } from "@/ui/Button";
import { CurveBackdrop } from "@/ui/CurveBackdrop";
import { Body, Brand, Title } from "@/ui/Typography";
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
        <Title style={styles.title}>Manger juste, ici à Tana.</Title>
        <Body style={styles.body}>
          Un planning de repas sains chaque semaine, adapté à ton budget et à
          ton foyer.
        </Body>
      </View>

      <View style={styles.actions}>
        <Button
          label="Commencer"
          onPress={() => router.push(`/onboarding/${STEP_IDS[0]}`)}
        />
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
  title: { textAlign: "center" },
  body: { textAlign: "center" },
  actions: {
    paddingHorizontal: space.lg,
    paddingTop: space.lg,
    paddingBottom: space.lg,
  },
});
