import { Feather } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useRef, useState } from "react";
import {
  Image,
  type ImageSourcePropType,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { STEP_IDS } from "@/onboarding/steps";
import { colors, space } from "@/theme";

type Slide = {
  image: ImageSourcePropType;
  title: string;
  subtitle: string;
};

const SLIDES: Slide[] = [
  {
    image: require("../assets/welcome-1.png"),
    title: "Un planning de repas pensé pour toi",
    subtitle:
      "Choisis les repas de ta semaine en quelques minutes, adaptés à ton budget et à ton foyer.",
  },
  {
    image: require("../assets/welcome-2.png"),
    title: "Des courses simples, sans stress",
    subtitle:
      "Fais tes courses une fois par semaine grâce à une liste prête à l'emploi et aux marchés les plus proches.",
  },
  {
    image: require("../assets/welcome-3.png"),
    title: "Des repas sains, faciles à cuisiner",
    subtitle:
      "Prépare des plats délicieux et équilibrés en moins de 30 minutes, du début à la fin.",
  },
];

/** Palette dédiée à cet écran, calquée pixel pour pixel sur la maquette fournie. */
const BLOB = "#FEE4C3";
const ORANGE = "#E58F16";
const ORANGE_DOT = "#F28600";
const DOT_INACTIVE = "#E6E6E6";

export default function WelcomeTourScreen() {
  const router = useRouter();
  const { width: screenWidth, height: screenHeight } = useWindowDimensions();
  const scrollRef = useRef<ScrollView>(null);
  const [index, setIndex] = useState(0);

  const isLast = index === SLIDES.length - 1;
  const illustrationAreaHeight = screenHeight * 0.4;
  const blobSize = screenWidth * 0.82;
  const imageSize = screenWidth * 0.68;

  const goTo = (next: number) => {
    scrollRef.current?.scrollTo({ x: next * screenWidth, animated: true });
    setIndex(next);
  };

  const onMomentumEnd = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const next = Math.round(e.nativeEvent.contentOffset.x / screenWidth);
    setIndex(next);
  };

  const finish = () => router.replace(`/onboarding/${STEP_IDS[0]}`);

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={styles.topBar}>
        <Pressable
          onPress={() => index > 0 && goTo(index - 1)}
          hitSlop={12}
          style={index === 0 && styles.backBtnHidden}
        >
          <Feather name="arrow-left" size={24} color={colors.ink} />
        </Pressable>
      </View>

      <ScrollView
        ref={scrollRef}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={onMomentumEnd}
        scrollEventThrottle={16}
        style={{ height: illustrationAreaHeight }}
      >
        {SLIDES.map((slide) => (
          <View
            key={slide.title}
            style={[styles.slide, { width: screenWidth, height: illustrationAreaHeight }]}
          >
            <View style={[styles.blob, { width: blobSize, height: blobSize, borderRadius: blobSize / 2 }]}>
              <Image
                source={slide.image}
                style={{ width: imageSize, height: imageSize }}
                resizeMode="contain"
              />
            </View>
          </View>
        ))}
      </ScrollView>

      <View style={styles.dots}>
        {SLIDES.map((_, i) => (
          <View key={i} style={[styles.dot, i === index && styles.dotActive]} />
        ))}
      </View>

      <View style={styles.content}>
        <Text style={styles.title}>{SLIDES[index].title}</Text>
        <Text style={styles.subtitle}>{SLIDES[index].subtitle}</Text>
      </View>

      <View style={styles.actions}>
        <Pressable
          onPress={() => (isLast ? finish() : goTo(index + 1))}
          style={({ pressed }) => [styles.continueBtn, pressed && { opacity: 0.85 }]}
        >
          <Text style={styles.continueLabel}>{isLast ? "Commencer" : "Continuer"}</Text>
        </Pressable>
        <Pressable onPress={finish} hitSlop={8}>
          <Text style={styles.skip}>Passer</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  topBar: {
    paddingHorizontal: space.lg,
    paddingTop: space.sm,
    paddingBottom: space.xs,
  },
  backBtnHidden: { opacity: 0 },
  slide: {
    alignItems: "center",
    justifyContent: "center",
  },
  blob: {
    backgroundColor: BLOB,
    alignItems: "center",
    justifyContent: "center",
  },
  dots: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 8,
    marginTop: space.md,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: DOT_INACTIVE,
  },
  dotActive: {
    backgroundColor: ORANGE_DOT,
  },
  content: {
    gap: space.sm,
    paddingHorizontal: space.lg,
    paddingTop: space.lg,
    alignItems: "center",
  },
  title: {
    fontSize: 28,
    fontWeight: "800",
    color: colors.ink,
    letterSpacing: -0.3,
    textAlign: "center",
    lineHeight: 34,
  },
  subtitle: {
    fontSize: 15,
    color: colors.muted,
    lineHeight: 21,
    textAlign: "center",
  },
  actions: {
    flex: 1,
    justifyContent: "flex-end",
    paddingHorizontal: space.lg,
    paddingBottom: space.lg,
    paddingTop: space.lg,
    gap: space.sm,
  },
  continueBtn: {
    minHeight: 56,
    borderRadius: 999,
    backgroundColor: ORANGE,
    alignItems: "center",
    justifyContent: "center",
  },
  continueLabel: { fontSize: 17, fontWeight: "700", color: "#1A1207" },
  skip: { color: colors.ink, fontWeight: "600", fontSize: 15, textAlign: "center" },
});
