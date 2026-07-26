import { useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { ApiError } from "@/api/http";
import { getMonProfilComplet } from "@/api/onboarding";
import { loginUtilisateur } from "@/api/utilisateur";
import { isValidEmail } from "@/lib/validators";
import { hydrationFromComplet } from "@/onboarding/hydrate";
import { useOnboarding } from "@/onboarding/store";
import { STEP_IDS } from "@/onboarding/steps";
import { useSession } from "@/session/SessionContext";
import { AuthField } from "@/ui/AuthField";
import { AuthPasswordField } from "@/ui/AuthPasswordField";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { colors, space, type } from "@/theme";

type FieldKey = "email" | "motDePasse";

export default function SignInScreen() {
  const router = useRouter();
  const { setSession, patchSession } = useSession();
  const { hydrate } = useOnboarding();

  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [touched, setTouched] = useState<Partial<Record<FieldKey, boolean>>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const markTouched = (key: FieldKey) => setTouched((t) => ({ ...t, [key]: true }));

  const fieldErrors: Partial<Record<FieldKey, string>> = {
    email: !email.trim()
      ? "L’email est requis."
      : !isValidEmail(email)
        ? "Format d’email invalide."
        : undefined,
    motDePasse: !motDePasse ? "Le mot de passe est requis." : undefined,
  };
  const hasFieldErrors = Object.values(fieldErrors).some(Boolean);
  const canSubmit = !hasFieldErrors && !loading;

  const onSubmit = async () => {
    setError(null);
    setTouched({ email: true, motDePasse: true });
    if (hasFieldErrors) {
      setError("Corrige les champs en rouge avant de continuer.");
      return;
    }

    setLoading(true);
    try {
      const user = await loginUtilisateur({
        email: email.trim().toLowerCase(),
        mot_de_passe: motDePasse,
      });
      await setSession({
        utilisateurId: user.id,
        apiToken: user.api_token,
        prenom: user.prenom,
        email: user.email,
      });

      // Retrouve le profil existant (et ses ids) pour ne pas atterrir sur un
      // dashboard "session incomplète" : sans ça, se reconnecter équivalait
      // à perdre tout son onboarding.
      try {
        const complet = await getMonProfilComplet(user.api_token);
        const { data, sessionPatch, done, resumeStep } = hydrationFromComplet(complet);
        await patchSession(sessionPatch);
        hydrate(data, done, resumeStep);
        if (done) {
          router.replace("/dashboard");
        } else {
          router.replace(`/onboarding/${resumeStep ?? STEP_IDS[0]}`);
        }
      } catch (completError) {
        if (completError instanceof ApiError && completError.status === 404) {
          router.replace(`/onboarding/${STEP_IDS[0]}`);
        } else {
          // Backend momentanément inatteignable : on laisse quand même
          // entrer, le dashboard réessaiera ses propres appels.
          router.replace("/dashboard");
        }
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen
      style={styles.screen}
      noNavClearance
      footer={
        <View style={styles.actions}>
          <Button
            label={loading ? "Connexion…" : "Se connecter"}
            onPress={() => void onSubmit()}
            disabled={!canSubmit}
            rounded
          />
          <Text style={styles.footerText}>
            Pas de compte ?{" "}
            <Text style={styles.link} onPress={() => router.replace("/signup")}>
              S’inscrire
            </Text>
          </Text>
        </View>
      }
    >
      <View style={styles.head}>
        <Text style={styles.title}>Content de te revoir !</Text>
        <Text style={styles.subtitle}>Entre tes informations pour continuer</Text>
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <View style={styles.form}>
        <AuthField
          icon="mail"
          value={email}
          onChange={setEmail}
          placeholder="Email"
          keyboard="email-address"
          error={touched.email ? fieldErrors.email : undefined}
          onBlur={() => markTouched("email")}
        />
        <AuthPasswordField
          value={motDePasse}
          onChange={setMotDePasse}
          placeholder="Mot de passe"
          error={touched.motDePasse ? fieldErrors.motDePasse : undefined}
          onBlur={() => markTouched("motDePasse")}
        />
        <Text style={styles.forgot}>Mot de passe oublié ?</Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { flexGrow: 1, justifyContent: "center" },
  head: { gap: space.xs, marginBottom: space.lg, alignItems: "center" },
  title: {
    fontSize: 26,
    fontWeight: "800",
    color: colors.ink,
    textAlign: "center",
  },
  subtitle: {
    fontSize: type.body,
    color: colors.muted,
    textAlign: "center",
  },
  form: { gap: space.md },
  forgot: {
    textAlign: "right",
    color: colors.muted,
    fontSize: type.small,
    fontWeight: "600",
  },
  actions: { gap: space.sm },
  footerText: { textAlign: "center", color: colors.muted, fontSize: type.body },
  link: { color: colors.brand, fontWeight: "700" },
  error: {
    color: colors.danger,
    fontSize: type.body,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
  },
});
