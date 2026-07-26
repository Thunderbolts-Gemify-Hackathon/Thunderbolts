import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { ApiError } from "@/api/http";
import { StepForm } from "@/onboarding/StepForm";
import { useOnboarding } from "@/onboarding/store";
import { getStep } from "@/onboarding/steps";
import { submitEditStep } from "@/onboarding/submitEditStep";
import type { OnboardingData, StepId } from "@/onboarding/types";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, space, type } from "@/theme";

export default function EditStepScreen() {
  const { stepId } = useLocalSearchParams<{ stepId: string }>();
  const router = useRouter();
  const { data, patch } = useOnboarding();
  const { session, patchSession } = useSession();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);

  const step = getStep(stepId ?? "");
  if (!step) {
    return (
      <Screen>
        <Title>Étape introuvable</Title>
        <Button label="Retour" onPress={() => router.back()} />
      </Screen>
    );
  }

  const values = data[step.id];

  const onChange = (key: string, value: string | string[]) => {
    setError(null);
    setOkMsg(null);
    patch(step.id, { [key]: value } as Partial<OnboardingData[StepId]>);
  };

  const onSave = async () => {
    setLoading(true);
    setError(null);
    setOkMsg(null);
    try {
      const result = await submitEditStep(step.id, data, session);
      if (result.sessionPatch) await patchSession(result.sessionPatch);
      setOkMsg(
        result.planningInvalide
          ? "Enregistre. Ton planning a ete invalide, regenere-le."
          : "Enregistre."
      );
      setTimeout(() => router.back(), 600);
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.detail
          : e instanceof Error
            ? e.message
            : "Erreur inconnue"
      );
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
            label={loading ? "Enregistrement…" : "Enregistrer"}
            onPress={onSave}
            disabled={loading}
          />
          <Button label="Annuler" variant="ghost" disabled={loading} onPress={() => router.back()} />
        </View>
      }
    >
      <View style={styles.head}>
        <Title>Modifier · {step.title}</Title>
        <Body>{step.subtitle}</Body>
      </View>
      <StepForm
        stepId={step.id}
        fields={step.fields}
        values={values}
        onChange={onChange}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {okMsg ? <Text style={styles.ok}>{okMsg}</Text> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  head: { gap: space.xs, marginBottom: space.md },
  actions: { gap: space.sm },
  error: { fontSize: type.body, color: colors.danger, marginTop: space.sm },
  ok: { fontSize: type.body, color: colors.accent, marginTop: space.sm },
});
