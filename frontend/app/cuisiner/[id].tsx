import AsyncStorage from "@react-native-async-storage/async-storage";
import { Feather } from "@expo/vector-icons";
import { CameraView, useCameraPermissions } from "expo-camera";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as Haptics from "expo-haptics";
import { activateKeepAwakeAsync, deactivateKeepAwake } from "expo-keep-awake";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  BackHandler,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { postRepasFeedback } from "@/api/feedback";
import { validerRepas } from "@/api/planning";
import { useHandCoverGesture } from "@/lib/handGesture";
import { getCachedContext, getCachedRecette } from "@/lib/recipeCache";
import { recetteVisual } from "@/lib/recipeVisual";
import { listenOnce, speak } from "@/lib/speech";
import { useEtapesRecette } from "@/lib/useEtapesRecette";
import { useSession } from "@/session/SessionContext";
import { colors, radius, space, type } from "@/theme";

const GUIDE_VU_KEY = "kalitao.cuisine.guideVu";
const TIMER_PRESETS_MIN = [1, 3, 5, 10, 15];

export default function ModeCuisineScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { session } = useSession();

  const recette = useMemo(() => (id ? getCachedRecette(id) : undefined), [id]);
  const context = useMemo(() => (id ? getCachedContext(id) : undefined), [id]);
  const profilId = session?.profilId;
  const token = session?.apiToken;

  const { etapes, loading, error, fetchEtapes } = useEtapesRecette(
    recette?.id,
    profilId,
    token,
    Boolean(recette?.id && profilId && token),
  );

  const [stepIndex, setStepIndex] = useState(0);
  const [handsFree, setHandsFree] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [handPresent, setHandPresent] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const stepIndexRef = useRef(0);
  const totalRef = useRef(0);

  const [showGuide, setShowGuide] = useState(false);
  const [showQuit, setShowQuit] = useState(false);
  const [showDone, setShowDone] = useState(false);
  const [timerOpen, setTimerOpen] = useState(false);
  const [timerLeft, setTimerLeft] = useState<number | null>(null);
  const [timerPaused, setTimerPaused] = useState(false);
  const [listeningCmd, setListeningCmd] = useState(false);

  const etapesList = Array.isArray(etapes) ? etapes : [];
  const total = etapesList.length;
  const isLast = total > 0 && stepIndex === total - 1;
  const step =
    total > 0 ? etapesList[Math.min(stepIndex, total - 1)] : undefined;
  const stepIngredients = Array.isArray(step?.ingredients)
    ? step.ingredients
    : [];
  stepIndexRef.current = stepIndex;
  totalRef.current = total;

  useEffect(() => {
    void activateKeepAwakeAsync("mode-cuisine");
    return () => {
      void deactivateKeepAwake("mode-cuisine");
    };
  }, []);

  const goNext = useCallback(() => {
    setStepIndex((i) => {
      const max = Math.max(totalRef.current - 1, 0);
      const next = Math.min(i + 1, max);
      if (next !== i) {
        void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
        const nextStep = etapesList[next];
        if (nextStep?.titre) {
          speak(`Étape ${nextStep.numero}. ${nextStep.titre}`);
        }
      }
      return next;
    });
  }, [etapesList]);

  const goPrev = useCallback(() => {
    setStepIndex((i) => Math.max(i - 1, 0));
  }, []);

  useHandCoverGesture({
    // Pause la détection tant que le guide est ouvert
    enabled: handsFree && Boolean(permission?.granted) && !showGuide,
    cameraRef,
    cameraReady,
    onHandChange: setHandPresent,
    onTrigger: () => {
      const i = stepIndexRef.current;
      const n = totalRef.current;
      if (n <= 0) return;
      if (i >= n - 1) {
        void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        setShowDone(true);
        speak("Bravo, c'est terminé.");
      } else {
        goNext();
      }
    },
  });

  const enableHandsFree = useCallback(async () => {
    if (!permission?.granted) {
      const res = await requestPermission();
      if (!res.granted) {
        Alert.alert(
          "Caméra indisponible",
          "Sans accès caméra, utilise le bouton « Étape suivante » en bas.",
        );
        return false;
      }
    }
    setCameraReady(false);
    setHandsFree(true);
    setShowGuide(true);
    await AsyncStorage.setItem(GUIDE_VU_KEY, "1");
    return true;
  }, [permission, requestPermission]);

  const toggleHandsFree = useCallback(async () => {
    if (handsFree) {
      setHandsFree(false);
      setCameraReady(false);
      return;
    }
    await enableHandsFree();
  }, [handsFree, enableHandsFree]);

  // Remet à l'étape 1 quand une nouvelle liste d'étapes arrive
  useEffect(() => {
    setStepIndex(0);
  }, [etapes, recette?.id]);

  const requestQuit = useCallback(() => {
    setShowQuit(true);
  }, []);

  useEffect(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => {
      requestQuit();
      return true;
    });
    return () => sub.remove();
  }, [requestQuit]);

  useEffect(() => {
    if (timerLeft == null || timerPaused) return;
    if (timerLeft <= 0) {
      void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      speak("Le minuteur est terminé.");
      setTimerLeft(null);
      setTimerPaused(false);
      return;
    }
    const t = setTimeout(
      () => setTimerLeft((s) => (s == null ? null : s - 1)),
      1000,
    );
    return () => clearTimeout(t);
  }, [timerLeft, timerPaused]);

  const startTimer = (minutes: number) => {
    setTimerLeft(minutes * 60);
    setTimerPaused(false);
    setTimerOpen(false);
    speak(`Minuteur ${minutes} minutes.`);
  };

  const repeatStep = useCallback(() => {
    const cur = etapesList[stepIndexRef.current];
    if (cur?.titre) {
      speak(`Étape ${cur.numero}. ${cur.titre}`);
    }
  }, [etapesList]);

  const handleVoiceCommand = useCallback(async () => {
    if (listeningCmd) return;
    setListeningCmd(true);
    speak("Commande ?");
    const result = await listenOnce();
    setListeningCmd(false);
    if ("error" in result) {
      Alert.alert("Voix", result.error);
      return;
    }
    const t = result.text.toLowerCase();
    if (/\b(suivant|next|avance)\b/.test(t)) {
      goNext();
    } else if (/\b(répète|repete|repeat)\b/.test(t)) {
      repeatStep();
    } else if (/\b(pause|stop)\b/.test(t)) {
      setTimerPaused((p) => !p);
      speak(timerPaused ? "Minuteur repris." : "Minuteur en pause.");
    } else if (/\b(précédent|precedent|retour)\b/.test(t)) {
      goPrev();
    } else {
      speak("Dis suivant, répète ou pause.");
    }
  }, [listeningCmd, goNext, goPrev, repeatStep, timerPaused]);

  const onFinish = async () => {
    setShowDone(false);
    if (context?.repasId && token) {
      try {
        await validerRepas(context.repasId, token);
      } catch {
        // pas bloquant : la recette reste marquable "Cuisiné ?" depuis l'écran détail
      }
    }
    router.back();
  };

  const onFeedback = async (note: 1 | -1) => {
    if (profilId && token && recette?.id) {
      try {
        await postRepasFeedback(profilId, token, {
          recette_id: recette.id,
          note,
        });
      } catch {
        /* non bloquant */
      }
    }
    await onFinish();
  };

  if (!recette) {
    return (
      <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
        <View style={styles.center}>
          <Text style={styles.errorText}>Recette indisponible.</Text>
          <Pressable onPress={() => router.back()} style={styles.retryBtn}>
            <Text style={styles.retryLabel}>Retour</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  const visual = recetteVisual(recette);

  return (
    <SafeAreaView
      style={[styles.safe, { backgroundColor: visual.bg }]}
      edges={["top", "bottom"]}
    >
      <View style={styles.header}>
        <Pressable onPress={requestQuit} style={styles.headerBtn} hitSlop={8}>
          <Feather name="x" size={22} color={colors.ink} />
        </Pressable>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle} numberOfLines={1}>
            {recette.nom}
          </Text>
          {total > 0 ? (
            <Text style={styles.headerStep}>
              Étape {stepIndex + 1} / {total}
            </Text>
          ) : null}
        </View>
        <Pressable
          onPress={() => void toggleHandsFree()}
          style={styles.headerBtn}
          hitSlop={8}
        >
          <Feather
            name={handsFree ? "video" : "video-off"}
            size={20}
            color={colors.ink}
          />
        </Pressable>
      </View>

      {total > 0 ? (
        <View style={styles.dotsRow}>
          {etapesList.map((_, i) => (
            <View
              key={i}
              style={[
                styles.dot,
                i === stepIndex && styles.dotActive,
                i < stepIndex && styles.dotDone,
              ]}
            />
          ))}
        </View>
      ) : null}

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {!profilId || !token ? (
          <View style={styles.center}>
            <Text style={styles.errorText}>
              Session incomplète. Reconnecte-toi, puis rouvre la recette depuis
              le planning.
            </Text>
            <Pressable
              onPress={() => router.replace("/signin")}
              style={styles.retryBtn}
            >
              <Text style={styles.retryLabel}>Se connecter</Text>
            </Pressable>
          </View>
        ) : loading ? (
          <View style={styles.center}>
            <ActivityIndicator color={colors.brand} size="large" />
            <Text style={styles.meta}>Kaly Tao prépare les étapes…</Text>
            <Text style={styles.metaHint}>
              Ça peut prendre 10–30 s (Gemma / Ollama).
            </Text>
          </View>
        ) : error ? (
          <View style={styles.center}>
            <Text style={styles.errorText}>{error}</Text>
            <Pressable
              onPress={() => void fetchEtapes()}
              style={styles.retryBtn}
            >
              <Text style={styles.retryLabel}>Réessayer</Text>
            </Pressable>
          </View>
        ) : step ? (
          <>
            <Text style={styles.stepLabel}>ÉTAPE {step.numero}</Text>
            <Text style={styles.stepTitle}>{step.titre}</Text>
            {stepIngredients.length > 0 ? (
              <View style={styles.chipsRow}>
                {stepIngredients.map((ing) => (
                  <View key={ing} style={styles.chip}>
                    <Text style={styles.chipText}>{ing}</Text>
                  </View>
                ))}
              </View>
            ) : null}
            {!handsFree ? (
              <Pressable
                onPress={() => void enableHandsFree()}
                style={styles.handsFreeCta}
              >
                <Text style={styles.handsFreeEmoji}>✋</Text>
                <Text style={styles.handsFreeCtaLabel}>
                  Activer le mode mains libres
                </Text>
                <Text style={styles.handsFreeCtaHint}>
                  Mets ta main devant le haut du téléphone (caméra selfie) pour
                  passer à l’étape suivante — sans toucher l’écran
                </Text>
              </Pressable>
            ) : (
              <View style={[styles.handsFreeActive, handPresent && styles.handsFreeActiveHot]}>
                <Text style={styles.handsFreeEmoji}>{handPresent ? "✋" : "👋"}</Text>
                <Text style={styles.handsFreeCtaLabel}>
                  {handPresent ? "Main détectée…" : "Mode mains libres"}
                </Text>
                <Text style={styles.handsFreeCtaHint}>
                  {!cameraReady
                    ? "Préparation de la caméra…"
                    : handPresent
                      ? "Garde la main un instant — l’étape va passer"
                      : "Approche ta main du haut du téléphone (là où est la caméra selfie)"}
                </Text>
              </View>
            )}
          </>
        ) : (
          <View style={styles.center}>
            <Text style={styles.errorText}>
              Aucune étape disponible pour cette recette.
            </Text>
            <Pressable
              onPress={() => void fetchEtapes()}
              style={styles.retryBtn}
            >
              <Text style={styles.retryLabel}>Générer les étapes</Text>
            </Pressable>
          </View>
        )}
      </ScrollView>

      {/* Caméra cachée : capteur uniquement (plus de pastille qui flash). */}
      {handsFree && permission?.granted ? (
        <View style={styles.cameraSensor} pointerEvents="none" collapsable={false}>
          <CameraView
            ref={cameraRef}
            style={styles.cameraHidden}
            facing="front"
            onCameraReady={() => setCameraReady(true)}
          />
        </View>
      ) : null}

      {/* Cible visuelle fixe — pas une preview caméra. */}
      {handsFree && permission?.granted ? (
        <View style={styles.cameraDock} pointerEvents="none">
          <View style={[styles.targetOrb, handPresent && styles.targetOrbHot]}>
            <Text style={styles.targetEmoji}>🤳</Text>
          </View>
          <Text style={styles.cameraHint}>
            {handPresent ? "Main vue !" : "Main devant ici"}
          </Text>
        </View>
      ) : null}

      {timerLeft != null ? (
        <Pressable
          style={styles.timerBadge}
          onPress={() => setTimerPaused((p) => !p)}
          onLongPress={() => setTimerOpen(true)}
        >
          <Feather name={timerPaused ? "pause" : "clock"} size={14} color="#F7F3EA" />
          <Text style={styles.timerBadgeText}>
            {timerPaused ? "Pause " : ""}
            {formatMmSs(timerLeft)}
          </Text>
        </Pressable>
      ) : null}

      <View style={styles.bottomBar}>
        <Pressable
          onPress={() => void handleVoiceCommand()}
          style={styles.iconBtn}
          hitSlop={8}
          disabled={listeningCmd}
        >
          <Feather
            name={listeningCmd ? "radio" : "mic"}
            size={20}
            color={colors.ink}
          />
        </Pressable>
        <Pressable
          onPress={() => setTimerOpen(true)}
          style={styles.iconBtn}
          hitSlop={8}
        >
          <Feather name="clock" size={20} color={colors.ink} />
        </Pressable>
        <Pressable
          onPress={goPrev}
          disabled={stepIndex === 0}
          style={[styles.iconBtn, stepIndex === 0 && styles.iconBtnDisabled]}
          hitSlop={8}
        >
          <Feather name="chevron-left" size={22} color={colors.ink} />
        </Pressable>
        <Pressable
          onPress={() => (isLast ? setShowDone(true) : goNext())}
          style={styles.nextBtn}
          disabled={!step}
        >
          <Text style={styles.nextLabel}>
            {isLast ? "Terminer" : "Étape suivante"}
          </Text>
          <Feather
            name={isLast ? "check" : "chevron-right"}
            size={20}
            color="#F7F3EA"
          />
        </Pressable>
      </View>

      <Modal visible={showGuide} transparent animationType="fade">
        <View style={styles.modalBackdrop}>
          <View style={styles.guideCard}>
            <View style={styles.guideIcon}>
              <Text style={styles.guideEmoji}>✋</Text>
            </View>
            <Text style={styles.guideTitle}>Mains libres</Text>
            <Text style={styles.guideBody}>
              1. Place le téléphone face à toi, un peu en retrait.{"\n"}
              2. Mets ta main devant le haut du téléphone (caméra selfie).{"\n"}
              3. Dès que la main est détectée, l’étape avance toute seule.{"\n"}
              4. Retire la main, puis recommence pour l’étape suivante.{"\n\n"}
              Tu n’as pas besoin de toucher l’écran (mains mouillées OK).
            </Text>
            <Pressable
              onPress={() => setShowGuide(false)}
              style={styles.guideBtn}
            >
              <Text style={styles.guideBtnLabel}>Compris</Text>
            </Pressable>
          </View>
        </View>
      </Modal>

      <Modal visible={showQuit} transparent animationType="fade">
        <View style={styles.modalBackdrop}>
          <View style={styles.quitCard}>
            <Text style={styles.quitTitle}>Quitter le mode cuisine ?</Text>
            <Text style={styles.guideBody}>
              Ta progression dans les étapes ne sera pas gardée.
            </Text>
            <View style={styles.quitActions}>
              <Pressable
                onPress={() => setShowQuit(false)}
                style={styles.quitCancelBtn}
              >
                <Text style={styles.quitCancelLabel}>Continuer</Text>
              </Pressable>
              <Pressable
                onPress={() => {
                  setShowQuit(false);
                  router.back();
                }}
                style={styles.quitConfirmBtn}
              >
                <Text style={styles.quitConfirmLabel}>Quitter</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={showDone} transparent animationType="fade">
        <View style={styles.modalBackdrop}>
          <View style={styles.guideCard}>
            <View style={styles.guideIcon}>
              <Feather name="check-circle" size={28} color={colors.brand} />
            </View>
            <Text style={styles.guideTitle}>Bravo, c'est prêt !</Text>
            <Text style={styles.guideBody}>
              {recette.nom} est cuisiné. Bon appétit ! Tu as aimé ce plat ?
            </Text>
            <View style={styles.feedbackRow}>
              <Pressable
                onPress={() => void onFeedback(1)}
                style={styles.feedbackBtn}
              >
                <Text style={styles.feedbackLabel}>J'aime</Text>
              </Pressable>
              <Pressable
                onPress={() => void onFeedback(-1)}
                style={[styles.feedbackBtn, styles.feedbackBtnGhost]}
              >
                <Text style={[styles.feedbackLabel, { color: colors.brand }]}>
                  Pas top
                </Text>
              </Pressable>
            </View>
            <Pressable onPress={() => void onFinish()} style={styles.guideBtn}>
              <Text style={styles.guideBtnLabel}>Terminer</Text>
            </Pressable>
          </View>
        </View>
      </Modal>

      <Modal visible={timerOpen} transparent animationType="slide">
        <View style={styles.modalBackdrop}>
          <View style={styles.timerCard}>
            <Text style={styles.quitTitle}>Minuteur</Text>
            {timerLeft != null ? (
              <>
                <Text style={styles.timerDisplay}>{formatMmSs(timerLeft)}</Text>
                <Pressable
                  onPress={() => setTimerPaused((p) => !p)}
                  style={styles.quitConfirmBtn}
                >
                  <Text style={styles.quitConfirmLabel}>
                    {timerPaused ? "Reprendre" : "Pause"}
                  </Text>
                </Pressable>
                <Pressable
                  onPress={() => {
                    setTimerLeft(null);
                    setTimerPaused(false);
                  }}
                  style={styles.quitCancelBtn}
                >
                  <Text style={styles.quitCancelLabel}>Arrêter</Text>
                </Pressable>
              </>
            ) : (
              <View style={styles.timerPresets}>
                {TIMER_PRESETS_MIN.map((m) => (
                  <Pressable
                    key={m}
                    onPress={() => startTimer(m)}
                    style={styles.timerPresetBtn}
                  >
                    <Text style={styles.timerPresetLabel}>{m} min</Text>
                  </Pressable>
                ))}
              </View>
            )}
            <Pressable
              onPress={() => setTimerOpen(false)}
              style={styles.quitCancelBtn}
            >
              <Text style={styles.quitCancelLabel}>Fermer</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function formatMmSs(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: {
    alignItems: "center",
    justifyContent: "center",
    gap: space.sm,
    paddingVertical: space.xl,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: space.md,
    paddingTop: space.sm,
    gap: space.sm,
  },
  headerBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.6)",
    alignItems: "center",
    justifyContent: "center",
  },
  headerCenter: { flex: 1, alignItems: "center" },
  headerTitle: { fontSize: type.body, fontWeight: "700", color: colors.ink },
  headerStep: { fontSize: type.small, color: colors.muted, fontWeight: "600" },
  dotsRow: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 6,
    paddingVertical: space.sm,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "rgba(0,0,0,0.15)",
  },
  dotActive: { backgroundColor: colors.brand, width: 20 },
  dotDone: { backgroundColor: colors.brandSoft },
  content: {
    flexGrow: 1,
    paddingHorizontal: space.lg,
    paddingTop: space.lg,
    paddingBottom: space.xl * 2,
  },
  stepLabel: {
    fontSize: type.small,
    fontWeight: "800",
    color: colors.muted,
    letterSpacing: 1,
  },
  stepTitle: {
    fontSize: 28,
    fontWeight: "800",
    color: colors.ink,
    marginTop: space.sm,
    lineHeight: 36,
  },
  chipsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: space.lg,
  },
  chip: {
    backgroundColor: "rgba(255,255,255,0.75)",
    borderRadius: 999,
    paddingHorizontal: space.md,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: colors.line,
  },
  chipText: { fontSize: type.body, color: colors.ink, fontWeight: "600" },
  meta: { fontSize: type.body, color: colors.muted, textAlign: "center" },
  metaHint: {
    fontSize: type.small,
    color: colors.muted,
    textAlign: "center",
    opacity: 0.8,
  },
  errorText: { fontSize: type.body, color: colors.danger, textAlign: "center" },
  retryBtn: { paddingHorizontal: space.lg, paddingVertical: space.sm },
  retryLabel: {
    color: colors.brand,
    fontWeight: "700",
    textDecorationLine: "underline",
  },
  handsFreeCta: {
    marginTop: space.xl,
    backgroundColor: "rgba(255,255,255,0.8)",
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: space.lg,
    alignItems: "center",
    gap: 4,
  },
  handsFreeActive: {
    marginTop: space.xl,
    backgroundColor: "rgba(31,61,43,0.1)",
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.brandSoft,
    padding: space.lg,
    alignItems: "center",
    gap: 6,
  },
  handsFreeActiveHot: {
    backgroundColor: "rgba(47,107,69,0.18)",
    borderColor: colors.ok,
  },
  handsFreeEmoji: { fontSize: 28 },
  handsFreeCtaLabel: {
    fontSize: type.body,
    fontWeight: "800",
    color: colors.ink,
  },
  handsFreeCtaHint: {
    fontSize: type.small,
    color: colors.muted,
    textAlign: "center",
    lineHeight: 18,
  },
  cameraSensor: {
    position: "absolute",
    width: 120,
    height: 120,
    opacity: 0.01,
    overflow: "hidden",
    left: -160,
    top: 0,
  },
  cameraHidden: { width: 120, height: 120 },
  cameraDock: {
    position: "absolute",
    top: 56,
    alignSelf: "center",
    left: 0,
    right: 0,
    alignItems: "center",
    gap: 6,
  },
  targetOrb: {
    width: 64,
    height: 64,
    borderRadius: 32,
    borderWidth: 3,
    borderColor: colors.brand,
    backgroundColor: "rgba(255,255,255,0.92)",
    alignItems: "center",
    justifyContent: "center",
  },
  targetOrbHot: {
    borderColor: colors.ok,
    backgroundColor: "#E7F3EA",
    transform: [{ scale: 1.08 }],
  },
  targetEmoji: { fontSize: 28 },
  cameraHint: {
    fontSize: 11,
    fontWeight: "700",
    color: colors.ink,
    backgroundColor: "rgba(255,255,255,0.9)",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    overflow: "hidden",
  },
  timerBadge: {
    position: "absolute",
    left: space.lg,
    bottom: 140,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: colors.ink,
    paddingHorizontal: space.md,
    paddingVertical: 8,
    borderRadius: 999,
  },
  timerBadgeText: { color: "#F7F3EA", fontWeight: "700", fontSize: type.small },
  bottomBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.sm,
    padding: space.lg,
  },
  iconBtn: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: "rgba(255,255,255,0.75)",
    alignItems: "center",
    justifyContent: "center",
  },
  iconBtnDisabled: { opacity: 0.4 },
  nextBtn: {
    flex: 1,
    flexDirection: "row",
    gap: space.sm,
    minHeight: 56,
    borderRadius: 999,
    backgroundColor: colors.brand,
    alignItems: "center",
    justifyContent: "center",
  },
  nextLabel: { fontSize: 16, fontWeight: "700", color: "#F7F3EA" },
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    alignItems: "center",
    justifyContent: "center",
    padding: space.lg,
  },
  guideCard: {
    width: "100%",
    maxWidth: 340,
    backgroundColor: colors.bg,
    borderRadius: radius.lg,
    padding: space.lg,
    alignItems: "center",
    gap: space.sm,
  },
  guideIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.brandSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  guideEmoji: { fontSize: 28 },
  guideTitle: {
    fontSize: type.title,
    fontWeight: "800",
    color: colors.ink,
    textAlign: "center",
  },
  guideBody: {
    fontSize: type.body,
    color: colors.muted,
    textAlign: "center",
    lineHeight: 20,
  },
  guideBtn: {
    marginTop: space.sm,
    width: "100%",
    minHeight: 50,
    borderRadius: 999,
    backgroundColor: colors.brand,
    alignItems: "center",
    justifyContent: "center",
  },
  guideBtnLabel: { fontSize: 16, fontWeight: "700", color: "#F7F3EA" },
  feedbackRow: { flexDirection: "row", gap: space.sm, width: "100%" },
  feedbackBtn: {
    flex: 1,
    minHeight: 46,
    borderRadius: 999,
    backgroundColor: colors.brand,
    alignItems: "center",
    justifyContent: "center",
  },
  feedbackBtnGhost: { backgroundColor: colors.brandSoft },
  feedbackLabel: { fontSize: 15, fontWeight: "700", color: "#F7F3EA" },
  quitCard: {
    width: "100%",
    maxWidth: 340,
    backgroundColor: colors.bg,
    borderRadius: radius.lg,
    padding: space.lg,
    gap: space.sm,
  },
  quitTitle: {
    fontSize: type.title,
    fontWeight: "800",
    color: colors.ink,
    textAlign: "center",
  },
  quitActions: { flexDirection: "row", gap: space.sm, marginTop: space.sm },
  quitCancelBtn: {
    flex: 1,
    minHeight: 50,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: "center",
    justifyContent: "center",
  },
  quitCancelLabel: {
    fontSize: type.body,
    fontWeight: "700",
    color: colors.ink,
  },
  quitConfirmBtn: {
    flex: 1,
    minHeight: 50,
    borderRadius: 999,
    backgroundColor: colors.danger,
    alignItems: "center",
    justifyContent: "center",
  },
  quitConfirmLabel: {
    fontSize: type.body,
    fontWeight: "700",
    color: "#F7F3EA",
  },
  timerCard: {
    width: "100%",
    maxWidth: 340,
    backgroundColor: colors.bg,
    borderRadius: radius.lg,
    padding: space.lg,
    gap: space.md,
  },
  timerDisplay: {
    fontSize: 48,
    fontWeight: "800",
    color: colors.ink,
    textAlign: "center",
  },
  timerPresets: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: space.sm,
    justifyContent: "center",
  },
  timerPresetBtn: {
    paddingHorizontal: space.lg,
    paddingVertical: space.md,
    borderRadius: 999,
    backgroundColor: colors.brandSoft,
  },
  timerPresetLabel: {
    fontSize: type.body,
    fontWeight: "700",
    color: colors.brand,
  },
});
