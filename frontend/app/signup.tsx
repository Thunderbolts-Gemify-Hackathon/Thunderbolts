import { Feather } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { ApiError } from "@/api/http";
import { createUtilisateur } from "@/api/utilisateur";
import { isValidDateNaissance, isValidEmail } from "@/lib/validators";
import { STEP_IDS } from "@/onboarding/steps";
import { useSession } from "@/session/SessionContext";
import { AuthField } from "@/ui/AuthField";
import { AuthPasswordField } from "@/ui/AuthPasswordField";
import { Button } from "@/ui/Button";
import { Checkbox } from "@/ui/Checkbox";
import { DateField } from "@/ui/DateField";
import { Screen } from "@/ui/Screen";
import { colors, space, type } from "@/theme";

type FieldKey = "prenom" | "nom" | "email" | "dateNaissance" | "motDePasse";

export default function SignUpScreen() {
  const router = useRouter();
  const { setSession } = useSession();

  const [prenom, setPrenom] = useState("");
  const [nom, setNom] = useState("");
  const [email, setEmail] = useState("");
  const [dateNaissance, setDateNaissance] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [accepte, setAccepte] = useState(false);
  const [touched, setTouched] = useState<Partial<Record<FieldKey, boolean>>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const markTouched = (key: FieldKey) => setTouched((t) => ({ ...t, [key]: true }));

  const hasLength = motDePasse.length >= 6;
  const hasNumber = /\d/.test(motDePasse);

  const fieldErrors: Partial<Record<FieldKey, string>> = {
    prenom: !prenom.trim() ? "Le prénom est requis." : undefined,
    nom: !nom.trim() ? "Le nom est requis." : undefined,
    email: !email.trim()
      ? "L’email est requis."
      : !isValidEmail(email)
        ? "Format d’email invalide."
        : undefined,
    dateNaissance: !dateNaissance
      ? "La date de naissance est requise."
      : !isValidDateNaissance(dateNaissance)
        ? "Date de naissance invalide."
        : undefined,
    motDePasse: !motDePasse
      ? "Le mot de passe est requis."
      : !hasLength || !hasNumber
        ? "Mot de passe trop faible."
        : undefined,
  };

  const hasFieldErrors = Object.values(fieldErrors).some(Boolean);
  const canSubmit = !hasFieldErrors && accepte && !loading;

  const onSubmit = async () => {
    setError(null);
    setTouched({ prenom: true, nom: true, email: true, dateNaissance: true, motDePasse: true });

    if (hasFieldErrors) {
      setError("Corrige les champs en rouge avant de continuer.");
      return;
    }
    if (!accepte) {
      setError("Merci d’accepter les conditions d’utilisation.");
      return;
    }

    setLoading(true);
    try {
      const user = await createUtilisateur({
        nom: nom.trim(),
        prenom: prenom.trim(),
        email: email.trim().toLowerCase(),
        date_naissance: dateNaissance.trim(),
        mot_de_passe: motDePasse,
      });
      await setSession({
        utilisateurId: user.id,
        apiToken: user.api_token,
        prenom: user.prenom,
        email: user.email,
      });
      router.replace(`/onboarding/${STEP_IDS[0]}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <Button
            label={loading ? "Création…" : "Créer mon compte"}
            onPress={() => void onSubmit()}
            disabled={!canSubmit}
            rounded
          />
          <Text style={styles.footerText}>
            Déjà un compte ?{" "}
            <Text style={styles.link} onPress={() => router.replace("/signin")}>
              Se connecter
            </Text>
          </Text>
        </View>
      }
    >
      <View style={styles.head}>
        <Text style={styles.title}>Bienvenue !</Text>
        <Text style={styles.subtitle}>Entre tes informations pour continuer</Text>
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <View style={styles.form}>
        <AuthField
          icon="user"
          value={prenom}
          onChange={setPrenom}
          placeholder="Prénom"
          error={touched.prenom ? fieldErrors.prenom : undefined}
          onBlur={() => markTouched("prenom")}
        />
        <AuthField
          icon="user"
          value={nom}
          onChange={setNom}
          placeholder="Nom"
          error={touched.nom ? fieldErrors.nom : undefined}
          onBlur={() => markTouched("nom")}
        />
        <AuthField
          icon="mail"
          value={email}
          onChange={setEmail}
          placeholder="Email"
          keyboard="email-address"
          error={touched.email ? fieldErrors.email : undefined}
          onBlur={() => markTouched("email")}
        />
        <DateField
          value={dateNaissance}
          onChange={setDateNaissance}
          placeholder="Date de naissance"
          error={touched.dateNaissance ? fieldErrors.dateNaissance : undefined}
          onBlur={() => markTouched("dateNaissance")}
        />
        <AuthPasswordField
          value={motDePasse}
          onChange={setMotDePasse}
          placeholder="Mot de passe"
          error={touched.motDePasse ? fieldErrors.motDePasse : undefined}
          onBlur={() => markTouched("motDePasse")}
        />

        <View style={styles.requirements}>
          <Text style={styles.requirementsTitle}>Ton mot de passe doit contenir :</Text>
          <Requirement ok={hasLength} label="Au moins 6 caractères" />
          <Requirement ok={hasNumber} label="Un chiffre" />
        </View>

        <Checkbox checked={accepte} onToggle={() => setAccepte((v) => !v)}>
          J’accepte les conditions d’utilisation de Kaly Tao.
        </Checkbox>
      </View>
    </Screen>
  );
}

function Requirement({ ok, label }: { ok: boolean; label: string }) {
  return (
    <View style={styles.reqRow}>
      <View style={[styles.reqCircle, ok && styles.reqCircleOk]}>
        <Feather name="check" size={12} color={ok ? "#F7F3EA" : colors.muted} />
      </View>
      <Text style={[styles.reqLabel, ok && styles.reqLabelOk]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  head: { gap: space.xs, marginBottom: space.md, alignItems: "center" },
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
  requirements: {
    gap: space.xs,
    backgroundColor: colors.brandSoft,
    borderRadius: 14,
    padding: space.md,
  },
  requirementsTitle: { fontSize: type.label, color: colors.muted, fontWeight: "600" },
  reqRow: { flexDirection: "row", alignItems: "center", gap: space.sm },
  reqCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: "center",
    justifyContent: "center",
  },
  reqCircleOk: { backgroundColor: colors.ok, borderColor: colors.ok },
  reqLabel: { fontSize: type.small, color: colors.muted },
  reqLabelOk: { color: colors.ok, fontWeight: "600" },
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
