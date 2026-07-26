import { type Href, useRouter } from "expo-router";
import { useRef, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import Markdown from "react-native-markdown-display";

import {
  postChat,
  postDirectiveCourses,
  postSuggestionRemede,
  type ChatMessage,
} from "@/api/chat";
import { ApiError } from "@/api/http";
import { createEtatDuJour } from "@/api/onboarding";
import { todayIso } from "@/lib/dates";
import { listenOnce, speak, stopSpeaking } from "@/lib/speech";
import { useSession } from "@/session/SessionContext";
import { Button } from "@/ui/Button";
import { Screen } from "@/ui/Screen";
import { Body, Title } from "@/ui/Typography";
import { colors, radius, space, type } from "@/theme";

const QUICK = [
  "Ou acheter du poulet ?",
  "Qu'est-ce qu'il me reste en stock ?",
  "Propose un repas leger pour aujourd'hui",
];

function AiText({ content }: { content: string }) {
  return <Markdown style={markdownStyles}>{content}</Markdown>;
}

export default function ChatScreen() {
  const router = useRouter();
  const { session } = useSession();
  const profilId = session?.profilId;
  const token = session?.apiToken;
  const inputRef = useRef<TextInput>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [lastDirective, setLastDirective] = useState<string | null>(null);
  const [remede, setRemede] = useState<string | null>(null);

  const pushAssistant = (content: string, readAloud: boolean) => {
    setMessages((prev) => [...prev, { role: "assistant", content }]);
    if (readAloud) speak(content);
  };

  const sendText = async (raw: string, readAloud = true) => {
    const message = raw.trim();
    if (!message || !profilId || !token || busy) return;

    setBusy(true);
    setError(null);
    setHint(null);
    setDraft("");
    setMessages((prev) => [...prev, { role: "user", content: message }]);

    try {
      const historique = messages.slice(-8);
      const res = await postChat(profilId, token, message, historique);
      pushAssistant(res.reponse, readAloud);
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.detail
          : "Chat indisponible. Verifie Ollama / Gemma."
      );
    } finally {
      setBusy(false);
    }
  };

  const onDirective = async (nom: string) => {
    if (!profilId || !token || busy) return;
    setBusy(true);
    setError(null);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: `Ou acheter : ${nom}` },
    ]);
    try {
      const d = await postDirectiveCourses(profilId, token, nom);
      setLastDirective(d.phrase);
      pushAssistant(d.phrase, true);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Directive impossible");
    } finally {
      setBusy(false);
    }
  };

  const onListen = async () => {
    setError(null);
    setListening(true);
    const result = await listenOnce();
    setListening(false);
    if ("error" in result) {
      setHint(result.error);
      inputRef.current?.focus();
      return;
    }
    setDraft(result.text);
    await sendText(result.text, true);
  };

  const onMalade = async () => {
    if (!profilId || !token || busy) return;
    setBusy(true);
    setError(null);
    setRemede(null);
    try {
      await createEtatDuJour(
        profilId,
        { date: todayIso(), type: "un_peu_malade" },
        token
      );
      const res = await postSuggestionRemede(profilId, token);
      setRemede(res.remede);
      pushAssistant(res.remede, true);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Remede indisponible");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Screen
      footer={
        <View style={styles.actions}>
          <View style={styles.composer}>
            <TextInput
              ref={inputRef}
              value={draft}
              onChangeText={setDraft}
              placeholder="Pose ta question a KaliTao…"
              placeholderTextColor={colors.muted}
              style={styles.input}
              editable={!busy}
              multiline
            />
            <Button
              label={busy ? "…" : "Envoyer"}
              onPress={() => void sendText(draft, true)}
              disabled={busy || !draft.trim()}
            />
          </View>
          <View style={styles.row}>
            <Pressable
              style={[styles.chip, listening && styles.chipActive]}
              onPress={() => void onListen()}
              disabled={busy}
            >
              <Text style={styles.chipText}>
                {listening ? "Ecoute…" : "Parler"}
              </Text>
            </Pressable>
            <Pressable style={styles.chip} onPress={() => stopSpeaking()}>
              <Text style={styles.chipText}>Stop voix</Text>
            </Pressable>
            <Pressable
              style={styles.chip}
              onPress={() => void onDirective("poulet")}
              disabled={busy}
            >
              <Text style={styles.chipText}>Ou acheter poulet</Text>
            </Pressable>
          </View>
          <Button
            label="Je me sens un peu malade"
            variant="ghost"
            onPress={() => void onMalade()}
            disabled={busy}
          />
          <Button
            label="Voir la carte"
            variant="ghost"
            onPress={() => router.push("/map" as Href)}
          />
          <Button label="Retour" variant="ghost" onPress={() => router.back()} />
        </View>
      }
    >
      <Title>Assistant KaliTao</Title>
      <Body>
        Gemma repond avec ton profil, ton stock et nos marches seedes. Pas de
        donnees inventees.
      </Body>

      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {busy ? <ActivityIndicator color={colors.brand} /> : null}

      <View style={styles.quick}>
        {QUICK.map((q) => (
          <Pressable
            key={q}
            style={styles.chip}
            onPress={() => {
              if (q.toLowerCase().includes("acheter")) {
                void onDirective("poulet");
              } else {
                void sendText(q, true);
              }
            }}
            disabled={busy}
          >
            <Text style={styles.chipText}>{q}</Text>
          </Pressable>
        ))}
      </View>

      {messages.map((m, i) => (
        <View
          key={`${m.role}-${i}`}
          style={[styles.bubble, m.role === "user" ? styles.user : styles.bot]}
        >
          {m.role === "assistant" ? (
            <AiText content={m.content} />
          ) : (
            <Text style={styles.bubbleText}>{m.content}</Text>
          )}
          {m.role === "assistant" ? (
            <Pressable onPress={() => speak(m.content)} style={styles.speakBtn}>
              <Text style={styles.speakLabel}>Lire</Text>
            </Pressable>
          ) : null}
        </View>
      ))}

      {lastDirective ? (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Derniere directive courses</Text>
          <AiText content={lastDirective} />
        </View>
      ) : null}

      {remede ? (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Remede du jour</Text>
          <AiText content={remede} />
        </View>
      ) : null}
    </Screen>
  );
}

const markdownStyles = StyleSheet.create({
  body: { color: colors.ink, fontSize: type.body, lineHeight: 22 },
  paragraph: { marginTop: 0, marginBottom: 6 },
  heading1: {
    color: colors.ink,
    fontSize: type.title,
    fontWeight: "700",
    marginTop: 4,
    marginBottom: 6,
  },
  heading2: {
    color: colors.ink,
    fontSize: type.body + 4,
    fontWeight: "700",
    marginTop: 4,
    marginBottom: 6,
  },
  heading3: {
    color: colors.ink,
    fontSize: type.body + 2,
    fontWeight: "700",
    marginTop: 4,
    marginBottom: 4,
  },
  strong: { fontWeight: "700" },
  em: { fontStyle: "italic" },
  bullet_list: { marginVertical: 4 },
  ordered_list: { marginVertical: 4 },
  list_item: { marginVertical: 2, flexDirection: "row" },
  bullet_list_icon: { color: colors.ink, marginRight: 6 },
  ordered_list_icon: { color: colors.ink, marginRight: 6 },
  code_inline: {
    backgroundColor: colors.bg,
    color: colors.accent,
    borderRadius: 4,
    paddingHorizontal: 4,
    fontFamily: "monospace",
  },
  fence: {
    backgroundColor: colors.bg,
    borderColor: colors.line,
    borderRadius: radius.sm,
    padding: space.sm,
  },
  code_block: {
    backgroundColor: colors.bg,
    borderColor: colors.line,
    borderRadius: radius.sm,
    padding: space.sm,
  },
  link: { color: colors.brand, textDecorationLine: "underline" },
  hr: { backgroundColor: colors.line, height: 1, marginVertical: space.sm },
  blockquote: {
    backgroundColor: colors.bg,
    borderLeftColor: colors.brand,
    borderLeftWidth: 3,
    paddingHorizontal: space.sm,
    marginVertical: 4,
  },
  table: { borderColor: colors.line, borderWidth: 1, borderRadius: radius.sm },
  th: { padding: space.xs, backgroundColor: colors.bg },
  td: { padding: space.xs, borderColor: colors.line, borderWidth: 1 },
});

const styles = StyleSheet.create({
  actions: { gap: space.sm },
  composer: { gap: space.sm },
  input: {
    minHeight: 52,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
    color: colors.ink,
    fontSize: type.body,
  },
  row: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  quick: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  chip: {
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
  },
  chipActive: { backgroundColor: colors.brandSoft, borderColor: colors.brand },
  chipText: { color: colors.ink, fontSize: type.small, fontWeight: "600" },
  bubble: {
    borderRadius: radius.md,
    padding: space.md,
    gap: 6,
  },
  user: {
    backgroundColor: colors.brandSoft,
    alignSelf: "flex-end",
    maxWidth: "92%",
  },
  bot: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    alignSelf: "flex-start",
    maxWidth: "92%",
  },
  bubbleText: { color: colors.ink, fontSize: type.body, lineHeight: 22 },
  speakBtn: {
    alignSelf: "flex-start",
    paddingVertical: 4,
    paddingHorizontal: 8,
    backgroundColor: colors.brandSoft,
    borderRadius: radius.sm,
  },
  speakLabel: { color: colors.brand, fontWeight: "700", fontSize: type.label },
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.md,
    gap: 6,
  },
  cardLabel: {
    fontSize: type.label,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
  },
  error: {
    color: colors.danger,
    backgroundColor: "#F8E8E4",
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
  hint: {
    color: colors.brand,
    backgroundColor: colors.brandSoft,
    padding: space.md,
    borderRadius: 12,
    fontSize: type.body,
  },
});
