import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { ApiError } from "@/api/http";
import { StepForm } from "@/onboarding/StepForm";
import { useOnboarding } from "@/onboarding/store";
import {
  getStep,
  nextStepId,
  prevStepId,
  STEP_IDS,
  stepIndex,
} from "@/onboarding/steps";
import { submitStep } from "@/onboarding/submitStep";
import type { OnboardingData, StepId } from "@/onboarding/types";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Progress } from "@/ui/Progress";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, space, type } from "@/theme";

export default function OnboardingStepScreen() {
  const { stepId } = useLocalSearchParams<{ stepId: string }>();
  const router = useRouter();
  const { data, patch, complete } = useOnboarding();
  const { session, setSession, patchSession } = useSession();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const step = getStep(stepId ?? "");
  if (!step) {
    return (
      <Screen>
        <Title>Étape introuvable</Title>
        <Button label="Retour" onPress={() => router.replace("/")} />
      </Screen>
    );
  }

  const index = stepIndex(step.id);
  const values = data[step.id];
  const next = nextStepId(step.id);
  const prev = prevStepId(step.id);

  const onChange = (key: string, value: string | string[]) => {
    setError(null);
    patch(step.id, { [key]: value } as Partial<OnboardingData[StepId]>);
  };

  const goNext = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await submitStep(step.id, data, session);
      if (result.session) await setSession(result.session);
      if (result.sessionPatch) await patchSession(result.sessionPatch);

      if (next) {
        router.push(`/onboarding/${next}`);
        return;
      }
      complete();
      router.replace("/dashboard");
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.detail
          : e instanceof Error
            ? e.message
            : "Erreur inconnue";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen
      noNavClearance
      footer={
        <View style={styles.actions}>
          <Button
            label={loading ? "Envoi…" : next ? "Continuer" : "Terminer"}
            onPress={goNext}
            disabled={loading}
          />
          <Button
            label={prev ? "Retour" : "Accueil"}
            variant="ghost"
            disabled={loading}
            onPress={() => (prev ? router.back() : router.replace("/"))}
          />
        </View>
      }
    >
      <Progress index={index} total={STEP_IDS.length} />
      <View style={styles.head}>
        <Title>{step.title}</Title>
        <Body>{step.subtitle}</Body>
      </View>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <StepForm
        stepId={step.id}
        fields={step.fields}
        values={values}
        onChange={onChange}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  head: { gap: space.xs, marginBottom: space.sm },
  actions: { gap: space.sm },
  error: {
    color: colors.danger,
    fontSize: type.body,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
  },
});
