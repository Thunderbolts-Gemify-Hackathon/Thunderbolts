import { Redirect, useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { API_URL } from "@/api/config";
import { ApiError, pingApi } from "@/api/http";
import { useOnboarding } from "@/onboarding/store";
import { STEP_IDS } from "@/onboarding/steps";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Brand, Title } from "@/ui/Typography";
import { colors, space } from "@/theme";

export default function WelcomeScreen() {
  const router = useRouter();
  const { done } = useOnboarding();
  const { session } = useSession();
  const [ping, setPing] = useState<string | null>(null);
  const [pinging, setPinging] = useState(false);

  if (done) return <Redirect href="/dashboard" />;

  const onPing = async () => {
    setPinging(true);
    setPing(null);
    try {
      setPing(await pingApi());
    } catch (e) {
      setPing(e instanceof ApiError ? e.detail : "Echec inconnu");
    } finally {
      setPinging(false);
    }
  };

  return (
    <Screen
      style={styles.hero}
      footer={
        <View style={styles.actions}>
          <Button
            label="Commencer"
            onPress={() => router.push(`/onboarding/${STEP_IDS[0]}`)}
          />
          <Button
            label={pinging ? "Test API…" : "Tester l'API"}
            variant="ghost"
            onPress={() => void onPing()}
            disabled={pinging}
          />
          <Button
            label="Voir le dashboard"
            variant="ghost"
            onPress={() => router.push("/dashboard")}
          />
        </View>
      }
    >
      <Brand>KaliTao</Brand>
      <Title>Manger juste, ici à Tana.</Title>
      <Body>
        Planning de repas, stock, budget et marches proches, adaptes a ton foyer.
      </Body>
      <View style={styles.note}>
        <Body style={{ color: colors.ink }}>
          API : {API_URL}
          {session ? `\nConnecte : ${session.email}` : ""}
        </Body>
        {ping ? (
          <Text
            style={[
              styles.ping,
              ping.includes("ok") || ping.includes("kalitao")
                ? styles.pingOk
                : styles.pingBad,
            ]}
          >
            {ping}
          </Text>
        ) : null}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: {
    flexGrow: 1,
    justifyContent: "flex-end",
    paddingBottom: space.xl,
    gap: space.md,
    minHeight: 520,
  },
  actions: { gap: space.sm },
  note: {
    marginTop: space.sm,
    padding: space.md,
    backgroundColor: colors.brandSoft,
    borderRadius: 14,
    gap: space.sm,
  },
  ping: { fontSize: 13, fontWeight: "700" },
  pingOk: { color: colors.ok },
  pingBad: { color: colors.danger },
});
