import { Feather } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useEffect, useRef, useState } from "react";
import {
  Animated,
  Easing,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { postChat, type ChatMessage } from "@/api/chat";
import { ApiError } from "@/api/http";
import { loadAppSettings } from "@/lib/appSettings";
import { listenOnce, pushToTalk, speakTracked, stopSpeaking } from "@/lib/speech";
import { useOnboarding } from "@/onboarding/store";
import { useSession } from "@/session/SessionContext";
import { space, type } from "@/theme";

type Phase = "idle" | "listening" | "thinking" | "speaking";

const BG = "#0E1712";
const ORB_CORE = "#2F6B45";
const ORB_GLOW = "#4C8A5E";
const CREAM = "#FEFEFE";
const CARD = "rgba(255,255,255,0.08)";

const GREETING =
  "Salut ! Je suis Kaly Tao. Dis-moi ce dont tu as besoin : un chemin à trouver, un marché proche, une idée de repas… je t'écoute.";

export default function AssistantVocalScreen() {
  const router = useRouter();
  const { session } = useSession();
  const { data } = useOnboarding();
  const profilId = session?.profilId;
  const token = session?.apiToken;
  const inputRef = useRef<TextInput>(null);

  const [phase, setPhase] = useState<Phase>("idle");
  const [transcript, setTranscript] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [showInput, setShowInput] = useState(Platform.OS !== "web");
  const [voiceEnabled, setVoiceEnabled] = useState(true);

  const breathe = useRef(new Animated.Value(1)).current;
  const dot0 = useRef(new Animated.Value(0)).current;
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;

  const busy = phase === "thinking" || phase === "listening";
  const localise = Boolean(session?.localisationLat) || Boolean(data.localisation.quartier);

  useEffect(() => {
    void loadAppSettings().then((s) => {
      setVoiceEnabled(s.voiceEnabled);
      if (!s.voiceEnabled) return;
      speakTracked(GREETING, {
        onStart: () => setPhase("speaking"),
        onDone: () => setPhase("idle"),
      });
    });
    return () => stopSpeaking();
  }, []);

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(breathe, {
          toValue: phase === "speaking" ? 1.16 : phase === "listening" ? 1.1 : 1.06,
          duration: phase === "speaking" ? 420 : 1400,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(breathe, {
          toValue: 1,
          duration: phase === "speaking" ? 420 : 1400,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [phase, breathe]);

  useEffect(() => {
    if (phase !== "speaking") return;
    const bounce = (v: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(v, { toValue: 1, duration: 260, delay, useNativeDriver: true }),
          Animated.timing(v, { toValue: 0, duration: 260, useNativeDriver: true }),
        ])
      );
    const anims = [bounce(dot0, 0), bounce(dot1, 120), bounce(dot2, 240)];
    anims.forEach((a) => a.start());
    return () => anims.forEach((a) => a.stop());
  }, [phase, dot0, dot1, dot2]);

  const sendMessage = async (raw: string) => {
    const message = raw.trim();
    if (!message || !profilId || !token || busy) return;
    setError(null);
    setDraft("");
    setShowInput(Platform.OS !== "web");
    setTranscript((prev) => [...prev, { role: "user", content: message }]);
    setPhase("thinking");
    try {
      const historique = transcript.slice(-8);
      const res = await postChat(profilId, token, message, historique, true);
      setTranscript((prev) => [...prev, { role: "assistant", content: res.reponse }]);
      if (voiceEnabled) {
        speakTracked(res.reponse, {
          onStart: () => setPhase("speaking"),
          onDone: () => setPhase("idle"),
        });
      } else {
        setPhase("idle");
      }
    } catch (e) {
      const raw =
        e instanceof ApiError ? e.detail : "Je n'ai pas pu répondre, vérifie Ollama / Gemma.";
      const detail = /Limite d'itérations|tool/i.test(raw)
        ? "Je me suis un peu embrouillé. Reformule plus simplement (ex. « marché le plus proche »)."
        : raw;
      setError(detail);
      setPhase("idle");
      if (voiceEnabled) {
        speakTracked("Désolé, " + detail, {
          onStart: () => setPhase("speaking"),
          onDone: () => setPhase("idle"),
        });
      }
    }
  };

  const onPressOrb = async () => {
    if (busy) return;
    stopSpeaking();
    setPhase("listening");
    setError(null);
    // Push-to-talk : web SpeechRecognition ou module natif si dispo
    const result = Platform.OS === "web" ? await listenOnce() : await pushToTalk();
    if ("error" in result) {
      setPhase("idle");
      setError(result.error);
      if (Platform.OS !== "web") {
        setShowInput(true);
        setTimeout(() => inputRef.current?.focus(), 80);
      }
      return;
    }
    await sendMessage(result.text);
  };

  const lastAssistant = [...transcript].reverse().find((m) => m.role === "assistant");
  const lastUser = [...transcript].reverse().find((m) => m.role === "user");

  const statusLabel =
    phase === "listening"
      ? "Je t'écoute…"
      : phase === "thinking"
        ? "Kaly Tao réfléchit…"
        : phase === "speaking"
          ? "Kaly Tao répond"
          : "Touche l'orbe pour parler";

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={styles.header}>
        <Pressable
          onPress={() => {
            stopSpeaking();
            router.back();
          }}
          style={styles.headerBtn}
          hitSlop={8}
        >
          <Feather name="arrow-left" size={20} color={CREAM} />
        </Pressable>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>Assistant vocal</Text>
          {localise ? (
            <View style={styles.locRow}>
              <Feather name="map-pin" size={11} color="rgba(255,255,255,0.6)" />
              <Text style={styles.locText}>Basé sur ta position</Text>
            </View>
          ) : null}
        </View>
        <Pressable onPress={() => stopSpeaking()} style={styles.headerBtn} hitSlop={8}>
          <Feather name="volume-x" size={18} color="rgba(255,255,255,0.7)" />
        </Pressable>
      </View>

      <View style={styles.orbArea}>
        <View style={styles.glowOuter} />
        <View style={styles.glowMid} />
        <Animated.View style={[styles.orb, { transform: [{ scale: breathe }] }]}>
          {phase === "speaking" ? (
            <View style={styles.speakBadge}>
              {[dot0, dot1, dot2].map((d, i) => (
                <Animated.View
                  key={i}
                  style={[
                    styles.speakDot,
                    {
                      transform: [
                        {
                          translateY: d.interpolate({
                            inputRange: [0, 1],
                            outputRange: [0, -10],
                          }),
                        },
                      ],
                    },
                  ]}
                />
              ))}
            </View>
          ) : (
            <Feather
              name="mic"
              size={30}
              color={phase === "listening" ? ORB_CORE : "rgba(255,255,255,0.9)"}
            />
          )}
        </Animated.View>

        <Text style={styles.statusLabel}>{statusLabel}</Text>

        {lastUser ? (
          <View style={styles.captionCard}>
            <Text style={styles.captionLabel}>Toi</Text>
            <Text style={styles.captionText} numberOfLines={3}>
              {lastUser.content}
            </Text>
          </View>
        ) : null}

        {lastAssistant ? (
          <View style={[styles.captionCard, styles.captionCardAssistant]}>
            <Text style={styles.captionLabel}>Kaly Tao</Text>
            <Text style={styles.captionText} numberOfLines={5}>
              {lastAssistant.content}
            </Text>
          </View>
        ) : null}

        {error ? <Text style={styles.errorText}>{error}</Text> : null}
      </View>

      <View style={styles.bottomArea}>
        {showInput ? (
          <View style={styles.inputRow}>
            <TextInput
              ref={inputRef}
              value={draft}
              onChangeText={setDraft}
              placeholder="Dicte avec le micro du clavier, ou écris…"
              placeholderTextColor="rgba(255,255,255,0.4)"
              style={styles.input}
              editable={!busy}
              onSubmitEditing={() => void sendMessage(draft)}
              returnKeyType="send"
            />
            <Pressable
              onPress={() => void sendMessage(draft)}
              disabled={!draft.trim() || busy}
              style={[styles.sendBtn, (!draft.trim() || busy) && { opacity: 0.4 }]}
            >
              <Feather name="arrow-up" size={20} color={BG} />
            </Pressable>
          </View>
        ) : null}

        <Pressable
          onPress={() => void onPressOrb()}
          disabled={busy}
          style={[styles.micBtn, busy && { opacity: 0.6 }]}
        >
          <Feather name={phase === "listening" ? "square" : "mic"} size={24} color={BG} />
          <Text style={styles.micLabel}>
            {phase === "listening" ? "Écoute…" : Platform.OS === "web" ? "Parler" : "Dicter"}
          </Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: BG },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: space.md,
    gap: space.sm,
  },
  headerBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.08)",
    alignItems: "center",
    justifyContent: "center",
  },
  headerCenter: { flex: 1, alignItems: "center", gap: 2 },
  headerTitle: { color: CREAM, fontSize: type.body, fontWeight: "700" },
  locRow: { flexDirection: "row", alignItems: "center", gap: 4 },
  locText: { color: "rgba(255,255,255,0.55)", fontSize: 11, fontWeight: "600" },
  orbArea: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: space.md,
    paddingHorizontal: space.lg,
  },
  glowOuter: {
    position: "absolute",
    width: 320,
    height: 320,
    borderRadius: 160,
    backgroundColor: ORB_GLOW,
    opacity: 0.08,
  },
  glowMid: {
    position: "absolute",
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: ORB_GLOW,
    opacity: 0.14,
  },
  orb: {
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: "rgba(255,255,255,0.06)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.18)",
    alignItems: "center",
    justifyContent: "center",
  },
  speakBadge: {
    flexDirection: "row",
    gap: 6,
    alignItems: "flex-end",
    height: 24,
  },
  speakDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: CREAM,
  },
  statusLabel: { color: "rgba(255,255,255,0.65)", fontSize: type.small, fontWeight: "600" },
  captionCard: {
    width: "100%",
    maxWidth: 340,
    backgroundColor: CARD,
    borderRadius: 16,
    padding: space.md,
    gap: 4,
  },
  captionCardAssistant: { backgroundColor: "rgba(47,107,69,0.22)" },
  captionLabel: {
    color: "rgba(255,255,255,0.5)",
    fontSize: 11,
    fontWeight: "800",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  captionText: { color: CREAM, fontSize: type.body, lineHeight: 21 },
  errorText: {
    color: "#FFD9CF",
    backgroundColor: "rgba(163,59,43,0.35)",
    padding: space.sm,
    borderRadius: 10,
    fontSize: type.small,
    textAlign: "center",
  },
  bottomArea: { padding: space.lg, gap: space.sm, alignItems: "center" },
  inputRow: {
    width: "100%",
    flexDirection: "row",
    gap: space.sm,
    backgroundColor: "rgba(255,255,255,0.08)",
    borderRadius: 999,
    paddingLeft: space.md,
    paddingRight: 6,
    alignItems: "center",
    minHeight: 50,
  },
  input: { flex: 1, color: CREAM, fontSize: type.body },
  sendBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: CREAM,
    alignItems: "center",
    justifyContent: "center",
  },
  micBtn: {
    flexDirection: "row",
    gap: 8,
    minHeight: 56,
    paddingHorizontal: space.xl,
    borderRadius: 999,
    backgroundColor: CREAM,
    alignItems: "center",
    justifyContent: "center",
  },
  micLabel: { color: BG, fontSize: 16, fontWeight: "700" },
});
