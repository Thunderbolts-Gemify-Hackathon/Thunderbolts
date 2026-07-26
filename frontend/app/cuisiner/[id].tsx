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

import { validerRepas } from "@/api/planning";
import { useHandCoverGesture } from "@/lib/handGesture";
import { getCachedContext, getCachedRecette } from "@/lib/recipeCache";
import { recetteVisual } from "@/lib/recipeVisual";
import { speak } from "@/lib/speech";
import { useEtapesRecette } from "@/lib/useEtapesRecette";
import { useSession } from "@/session/SessionContext";
import { colors, radius, space, type } from "@/theme";

const ORANGE = "#E58F16";
const GUIDE_VU_KEY = "kalitao.cuisine.guideVu";
const TIMER_PRESETS_MIN = [1, 3, 5, 10];

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
    Boolean(recette?.id && profilId && token)
  );

  const [stepIndex, setStepIndex] = useState(0);
  const [handsFree, setHandsFree] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const autoHandsFreeTried = useRef(false);

  const [showGuide, setShowGuide] = useState(false);
  const [showQuit, setShowQuit] = useState(false);
  const [showDone, setShowDone] = useState(false);
  const [timerOpen, setTimerOpen] = useState(false);
  const [timerLeft, setTimerLeft] = useState<number | null>(null);

  const total = etapes?.length ?? 0;
  const isLast = total > 0 && stepIndex === total - 1;
  const step = etapes?.[stepIndex];

  useEffect(() => {
    void activateKeepAwakeAsync("mode-cuisine");
    return () => {
      void deactivateKeepAwake("mode-cuisine");
    };
  }, []);

  const goNext = useCallback(() => {
    setStepIndex((i) => {
      const next = Math.min(i + 1, Math.max(total - 1, 0));
      if (next !== i) {
        void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      }
      return next;
    });
  }, [total]);

  const goPrev = useCallback(() => {
    setStepIndex((i) => Math.max(i - 1, 0));
  }, []);

  const { coverProgress } = useHandCoverGesture({
    enabled: handsFree && Boolean(permission?.granted),
    cameraRef,
    cameraReady,
    onTrigger: () => {
      if (isLast) {
        setShowDone(true);
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
          "Sans accès caméra, utilise les boutons pour changer d'étape."
        );
        return false;
      }
    }
    setCameraReady(false);
    setHandsFree(true);
    const vu = await AsyncStorage.getItem(GUIDE_VU_KEY);
    if (!vu) {
      setShowGuide(true);
      await AsyncStorage.setItem(GUIDE_VU_KEY, "1");
    }
    return true;
  }, [permission, requestPermission]);

  const toggleHandsFree = useCallback(async () => {
    if (handsFree) {
      setHandsFree(false);
      return;
    }
    await enableHandsFree();
  }, [handsFree, enableHandsFree]);

  // Dès que les étapes sont prêtes, active le mode mains libres une fois
  // (demande caméra + guide) pour que le geste soit testable sans chercher
  // l'icône discrète en haut à droite.
  useEffect(() => {
    if (autoHandsFreeTried.current) return;
    if (!etapes?.length || loading || handsFree) return;
    autoHandsFreeTried.current = true;
    void enableHandsFree();
  }, [etapes, loading, handsFree, enableHandsFree]);

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
    if (timerLeft == null) return;
    if (timerLeft <= 0) {
      void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      speak("Le minuteur est terminé.");
      setTimerLeft(null);
      return;
    }
    const t = setTimeout(() => setTimerLeft((s) => (s == null ? null : s - 1)), 1000);
    return () => clearTimeout(t);
  }, [timerLeft]);

  const startTimer = (minutes: number) => {
    setTimerLeft(minutes * 60);
    setTimerOpen(false);
  };

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
    <SafeAreaView style={[styles.safe, { backgroundColor: visual.bg }]} edges={["top", "bottom"]}>
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
        <Pressable onPress={() => void toggleHandsFree()} style={styles.headerBtn} hitSlop={8}>
          <Feather name={handsFree ? "video" : "video-off"} size={20} color={colors.ink} />
        </Pressable>
      </View>

      {total > 0 ? (
        <View style={styles.dotsRow}>
          {etapes!.map((_, i) => (
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

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {!profilId || !token ? (
          <View style={styles.center}>
            <Text style={styles.errorText}>
              Session incomplète. Reconnecte-toi, puis rouvre la recette depuis le planning.
            </Text>
            <Pressable onPress={() => router.replace("/signin")} style={styles.retryBtn}>
              <Text style={styles.retryLabel}>Se connecter</Text>
            </Pressable>
          </View>
        ) : loading ? (
          <View style={styles.center}>
            <ActivityIndicator color={colors.brand} size="large" />
            <Text style={styles.meta}>Kaly Tao prépare les étapes…</Text>
            <Text style={styles.metaHint}>Ça peut prendre 10–30 s (Gemma / Ollama).</Text>
          </View>
        ) : error ? (
          <View style={styles.center}>
            <Text style={styles.errorText}>{error}</Text>
            <Pressable onPress={() => void fetchEtapes()} style={styles.retryBtn}>
              <Text style={styles.retryLabel}>Réessayer</Text>
            </Pressable>
          </View>
        ) : step ? (
          <>
            <Text style={styles.stepLabel}>ÉTAPE {step.numero}</Text>
            <Text style={styles.stepTitle}>{step.titre}</Text>
            {step.ingredients.length > 0 ? (
              <View style={styles.chipsRow}>
                {step.ingredients.map((ing) => (
                  <View key={ing} style={styles.chip}>
                    <Text style={styles.chipText}>{ing}</Text>
                  </View>
                ))}
              </View>
            ) : null}
            {!handsFree ? (
              <Pressable onPress={() => void enableHandsFree()} style={styles.handsFreeCta}>
                <Text style={styles.handsFreeEmoji}>✋</Text>
                <Text style={styles.handsFreeCtaLabel}>Activer le mode mains libres</Text>
                <Text style={styles.handsFreeCtaHint}>
                  Recouvre la caméra pour passer à l’étape suivante
                </Text>
              </Pressable>
            ) : null}
          </>
        ) : (
          <View style={styles.center}>
            <Text style={styles.errorText}>Aucune étape disponible pour cette recette.</Text>
            <Pressable onPress={() => void fetchEtapes()} style={styles.retryBtn}>
              <Text style={styles.retryLabel}>Générer les étapes</Text>
            </Pressable>
          </View>
        )}
      </ScrollView>

      {handsFree && permission?.granted ? (
        <View style={styles.cameraDock}>
          <CameraView
            ref={cameraRef}
            style={styles.cameraPreview}
            facing="back"
            onCameraReady={() => setCameraReady(true)}
          />
          <Text style={styles.cameraHint}>Recouvre l'objectif pour avancer</Text>
        </View>
      ) : null}

      {timerLeft != null ? (
        <Pressable style={styles.timerBadge} onPress={() => setTimerOpen(true)}>
          <Feather name="clock" size={14} color="#F7F3EA" />
          <Text style={styles.timerBadgeText}>{formatMmSs(timerLeft)}</Text>
        </Pressable>
      ) : null}

      <View pointerEvents="none" style={[styles.coverOverlay, { opacity: coverProgress }]} />

      <View style={styles.bottomBar}>
        <Pressable onPress={() => setTimerOpen(true)} style={styles.iconBtn} hitSlop={8}>
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
          <Text style={styles.nextLabel}>{isLast ? "Terminer" : "Étape suivante"}</Text>
          <Feather name={isLast ? "check" : "chevron-right"} size={20} color="#1A1207" />
        </Pressable>
      </View>

      <Modal visible={showGuide} transparent animationType="fade">
        <View style={styles.modalBackdrop}>
          <View style={styles.guideCard}>
            <View style={styles.guideIcon}>
              <Text style={styles.guideEmoji}>✋</Text>
            </View>
            <Text style={styles.guideTitle}>Mode mains libres activé</Text>
            <Text style={styles.guideBody}>
              Recouvre l'objectif de la caméra avec ta main et maintiens jusqu'à ce que l'écran
              s'assombrisse : l'étape suivante s'affiche automatiquement.
            </Text>
            <Pressable onPress={() => setShowGuide(false)} style={styles.guideBtn}>
              <Text style={styles.guideBtnLabel}>Compris</Text>
            </Pressable>
          </View>
        </View>
      </Modal>

      <Modal visible={showQuit} transparent animationType="fade">
        <View style={styles.modalBackdrop}>
          <View style={styles.quitCard}>
            <Text style={styles.quitTitle}>Quitter le mode cuisine ?</Text>
            <Text style={styles.guideBody}>Ta progression dans les étapes ne sera pas gardée.</Text>
            <View style={styles.quitActions}>
              <Pressable onPress={() => setShowQuit(false)} style={styles.quitCancelBtn}>
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
            <Text style={styles.guideBody}>{recette.nom} est cuisiné. Bon appétit !</Text>
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
                <Pressable onPress={() => setTimerLeft(null)} style={styles.quitConfirmBtn}>
                  <Text style={styles.quitConfirmLabel}>Arrêter</Text>
                </Pressable>
              </>
            ) : (
              <View style={styles.timerPresets}>
                {TIMER_PRESETS_MIN.map((m) => (
                  <Pressable key={m} onPress={() => startTimer(m)} style={styles.timerPresetBtn}>
                    <Text style={styles.timerPresetLabel}>{m} min</Text>
                  </Pressable>
                ))}
              </View>
            )}
            <Pressable onPress={() => setTimerOpen(false)} style={styles.quitCancelBtn}>
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
  center: { alignItems: "center", justifyContent: "center", gap: space.sm, paddingVertical: space.xl },
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
  dotsRow: { flexDirection: "row", justifyContent: "center", gap: 6, paddingVertical: space.sm },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: "rgba(0,0,0,0.15)" },
  dotActive: { backgroundColor: ORANGE, width: 20 },
  dotDone: { backgroundColor: colors.brand },
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
  chipsRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: space.lg },
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
  metaHint: { fontSize: type.small, color: colors.muted, textAlign: "center", opacity: 0.8 },
  errorText: { fontSize: type.body, color: colors.danger, textAlign: "center" },
  retryBtn: { paddingHorizontal: space.lg, paddingVertical: space.sm },
  retryLabel: { color: colors.brand, fontWeight: "700", textDecorationLine: "underline" },
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
  handsFreeEmoji: { fontSize: 28 },
  handsFreeCtaLabel: { fontSize: type.body, fontWeight: "800", color: colors.ink },
  handsFreeCtaHint: { fontSize: type.small, color: colors.muted, textAlign: "center" },
  cameraDock: {
    position: "absolute",
    right: space.lg,
    bottom: 140,
    alignItems: "center",
    gap: 6,
  },
  cameraPreview: {
    width: 72,
    height: 72,
    borderRadius: 36,
    overflow: "hidden",
    borderWidth: 3,
    borderColor: ORANGE,
  },
  cameraHint: {
    fontSize: 11,
    fontWeight: "700",
    color: colors.ink,
    backgroundColor: "rgba(255,255,255,0.85)",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
    maxWidth: 120,
    textAlign: "center",
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
  coverOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "#000",
  },
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
    backgroundColor: ORANGE,
    alignItems: "center",
    justifyContent: "center",
  },
  nextLabel: { fontSize: 16, fontWeight: "700", color: "#1A1207" },
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
  guideTitle: { fontSize: type.title, fontWeight: "800", color: colors.ink, textAlign: "center" },
  guideBody: { fontSize: type.body, color: colors.muted, textAlign: "center", lineHeight: 20 },
  guideBtn: {
    marginTop: space.sm,
    width: "100%",
    minHeight: 50,
    borderRadius: 999,
    backgroundColor: ORANGE,
    alignItems: "center",
    justifyContent: "center",
  },
  guideBtnLabel: { fontSize: 16, fontWeight: "700", color: "#1A1207" },
  quitCard: {
    width: "100%",
    maxWidth: 340,
    backgroundColor: colors.bg,
    borderRadius: radius.lg,
    padding: space.lg,
    gap: space.sm,
  },
  quitTitle: { fontSize: type.title, fontWeight: "800", color: colors.ink, textAlign: "center" },
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
  quitCancelLabel: { fontSize: type.body, fontWeight: "700", color: colors.ink },
  quitConfirmBtn: {
    flex: 1,
    minHeight: 50,
    borderRadius: 999,
    backgroundColor: colors.danger,
    alignItems: "center",
    justifyContent: "center",
  },
  quitConfirmLabel: { fontSize: type.body, fontWeight: "700", color: "#F7F3EA" },
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
  timerPresets: { flexDirection: "row", flexWrap: "wrap", gap: space.sm, justifyContent: "center" },
  timerPresetBtn: {
    paddingHorizontal: space.lg,
    paddingVertical: space.md,
    borderRadius: 999,
    backgroundColor: colors.brandSoft,
  },
  timerPresetLabel: { fontSize: type.body, fontWeight: "700", color: colors.brand },
});
