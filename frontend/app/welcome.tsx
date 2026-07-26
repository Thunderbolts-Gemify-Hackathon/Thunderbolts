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
import { Button } from "@/ui/Button";
import { colors, space, type } from "@/theme";

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

export default function WelcomeTourScreen() {
  const router = useRouter();
  const { width: screenWidth, height: screenHeight } = useWindowDimensions();
  const scrollRef = useRef<ScrollView>(null);
  const [index, setIndex] = useState(0);

  const isLast = index === SLIDES.length - 1;
  const illustrationSize = Math.min(screenWidth * 0.58, screenHeight * 0.3);

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
          hitSlop={8}
          style={[styles.backBtn, index === 0 && styles.backBtnHidden]}
        >
          <Feather name="arrow-left" size={20} color={colors.ink} />
        </Pressable>
      </View>

      <ScrollView
        ref={scrollRef}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={onMomentumEnd}
        scrollEventThrottle={16}
        style={{ maxHeight: illustrationSize }}
      >
        {SLIDES.map((slide) => (
          <View
            key={slide.title}
            style={[styles.slide, { width: screenWidth, height: illustrationSize }]}
          >
            <Image
              source={slide.image}
              style={{ width: illustrationSize, height: illustrationSize }}
              resizeMode="contain"
            />
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
        <Button
          label={isLast ? "Commencer" : "Continuer"}
          onPress={() => (isLast ? finish() : goTo(index + 1))}
          rounded
        />
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
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "flex-start",
  },
  backBtnHidden: { opacity: 0 },
  slide: {
    alignItems: "center",
    justifyContent: "center",
  },
  dots: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 6,
    marginTop: space.md,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.line,
  },
  dotActive: {
    width: 20,
    backgroundColor: colors.brand,
  },
  content: {
    flex: 1,
    gap: space.sm,
    paddingHorizontal: space.lg,
    paddingTop: space.lg,
    alignItems: "center",
    justifyContent: "flex-start",
  },
  title: {
    fontSize: type.title,
    fontWeight: "700",
    color: colors.ink,
    letterSpacing: -0.3,
    textAlign: "center",
  },
  subtitle: {
    fontSize: type.body,
    color: colors.muted,
    lineHeight: 22,
    textAlign: "center",
  },
  actions: {
    paddingHorizontal: space.lg,
    paddingBottom: space.lg,
    gap: space.sm,
  },
  skip: { color: colors.muted, fontWeight: "600", fontSize: type.body, textAlign: "center" },
});
