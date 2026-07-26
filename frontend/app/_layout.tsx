import {
  Fredoka_600SemiBold,
  Fredoka_700Bold,
  useFonts,
} from "@expo-google-fonts/fredoka";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { useEffect, useState } from "react";
import { StatusBar } from "expo-status-bar";
import { View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";

import { getMonProfilComplet } from "@/api/onboarding";
import { hydrationFromComplet } from "@/onboarding/hydrate";
import { OnboardingProvider, useOnboarding } from "@/onboarding/store";
import { SessionProvider, useSession } from "@/session/SessionContext";
import { BottomNavBar } from "@/ui/BottomNavBar";
import { colors } from "@/theme";

SplashScreen.preventAutoHideAsync();

/**
 * Réhydrate la session au démarrage/reload de l'app : la session (token,
 * profilId…) survit déjà au refresh via AsyncStorage, mais l'état
 * "onboarding terminé" ne vivait qu'en mémoire et repartait à zéro à chaque
 * reload — d'où le retour forcé à l'onboarding. On revérifie ici la vérité
 * serveur (GET /onboarding/mine/complet) avant d'afficher quoi que ce soit,
 * pour ne jamais montrer un écran "à refaire" alors que la session est
 * toujours valide.
 */
function useAppBoot() {
  const { session, ready: sessionReady, patchSession } = useSession();
  const { hydrate } = useOnboarding();
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    if (!sessionReady) return;
    if (!session?.apiToken) {
      setHydrated(true);
      return;
    }
    let alive = true;
    const timeout = new Promise<null>((resolve) =>
      setTimeout(() => resolve(null), 4000),
    );
    Promise.race([getMonProfilComplet(session.apiToken), timeout])
      .then((complet) => {
        if (!alive || !complet) return;
        const { data, sessionPatch, done, resumeStep } =
          hydrationFromComplet(complet);
        hydrate(data, done, resumeStep);
        void patchSession(sessionPatch);
      })
      .catch(() => {
        /* pas de profil encore (404) ou backend inatteignable : on continue
           avec ce que la session locale sait déjà — les écrans gèrent le
           cas "session incomplète" eux-mêmes. */
      })
      .finally(() => {
        if (alive) setHydrated(true);
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionReady, session?.apiToken]);

  return sessionReady && hydrated;
}

function AppShell({ fontsLoaded }: { fontsLoaded: boolean }) {
  const bootReady = useAppBoot();

  useEffect(() => {
    if (fontsLoaded && bootReady) SplashScreen.hideAsync();
  }, [fontsLoaded, bootReady]);

  if (!bootReady) return null;

  return (
    <>
      <StatusBar style="dark" />
      <View style={{ flex: 1, backgroundColor: colors.bg }}>
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: colors.bg },
          }}
        />
        <BottomNavBar />
      </View>
    </>
  );
}

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    Fredoka_600SemiBold,
    Fredoka_700Bold,
  });

  if (!fontsLoaded) return null;

  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: colors.bg }}>
      <SessionProvider>
        <OnboardingProvider>
          <AppShell fontsLoaded={fontsLoaded} />
        </OnboardingProvider>
      </SessionProvider>
    </GestureHandlerRootView>
  );
}
