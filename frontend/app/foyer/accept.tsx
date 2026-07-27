import { type Href, useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";

import { acceptFoyerInvite } from "@/api/foyer";
import { ApiError } from "@/api/http";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

export default function FoyerAcceptScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ token?: string }>();
  const { session } = useSession();
  const [inviteToken, setInviteToken] = useState(
    typeof params.token === "string" ? params.token : ""
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const accept = async () => {
    if (!session?.apiToken) {
      setError("Connecte-toi d'abord.");
      return;
    }
    const token = inviteToken.trim().replace(/^kalitao:\/\/foyer\/invite\//, "");
    if (!token) {
      setError("Colle le token ou le lien d'invitation.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await acceptFoyerInvite(session.apiToken, token);
      setOk("Tu as rejoint le foyer.");
      setTimeout(() => router.replace("/foyer" as Href), 700);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Invitation invalide");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label={loading ? "Validation…" : "Rejoindre le foyer"}
            onPress={() => void accept()}
            disabled={loading}
          />
          <Button label="Annuler" variant="ghost" onPress={() => router.back()} />
        </View>
      }
    >
      <Title>Rejoindre un foyer</Title>
      <Body>Colle le lien kalitao://foyer/invite/... ou juste le token.</Body>
      <TextInput
        value={inviteToken}
        onChangeText={setInviteToken}
        placeholder="kalitao://foyer/invite/…"
        placeholderTextColor={colors.muted}
        style={styles.input}
        autoCapitalize="none"
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {ok ? <Text style={styles.ok}>{ok}</Text> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  actions: { gap: space.sm },
  input: {
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    padding: space.md,
    fontSize: type.body,
    color: colors.ink,
    marginTop: space.md,
  },
  error: { color: colors.danger, marginTop: space.sm },
  ok: { color: colors.ok, marginTop: space.sm, fontWeight: "600" },
});
