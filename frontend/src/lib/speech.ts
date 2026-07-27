import { Platform } from "react-native";
import * as Speech from "expo-speech";

type ListenResult = { text: string } | { error: string };

/** Lit une directive / réponse assistant à voix haute. */
export function speak(text: string, lang = "fr-FR") {
  Speech.stop();
  Speech.speak(text, { language: lang, rate: 0.95 });
}

export function stopSpeaking() {
  Speech.stop();
}

/**
 * Variante suivie : callbacks de début/fin utiles pour animer une UI vocale
 * (ex. orbe qui pulse pendant que l'assistant parle) sans deviner une durée.
 */
export function speakTracked(
  text: string,
  { onStart, onDone }: { onStart?: () => void; onDone?: () => void },
  lang = "fr-FR"
) {
  Speech.stop();
  Speech.speak(text, {
    language: lang,
    rate: 0.95,
    onStart,
    onDone,
    onStopped: onDone,
    onError: onDone,
  });
}

/** Message de repli si STT natif indisponible (testable sans module natif). */
export function fallbackListenError(platform: string = Platform.OS): string {
  if (platform === "web") {
    return "Reconnaissance vocale indisponible sur ce navigateur.";
  }
  return "Sur telephone, utilise le micro du clavier puis Envoyer.";
}

export function isListenSuccess(
  result: ListenResult
): result is { text: string } {
  return "text" in result && typeof result.text === "string";
}

type ExpoSpeechRecognitionModule = {
  requestPermissionsAsync?: () => Promise<{ granted?: boolean; status?: string }>;
  start?: (opts: Record<string, unknown>) => void;
  stop?: () => void;
  addListener?: (
    event: string,
    cb: (ev: { transcript?: string; error?: string; isFinal?: boolean }) => void
  ) => { remove: () => void };
};

function tryNativeSpeechRecognition(): ExpoSpeechRecognitionModule | null {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const mod = require("expo-speech-recognition");
    return (
      mod?.ExpoSpeechRecognitionModule ||
      mod?.default ||
      mod ||
      null
    );
  } catch {
    // Package absent ou non lié au build natif — repli clavier.
    return null;
  }
}

function listenWeb(lang: string): Promise<ListenResult> {
  const SpeechRecognition =
    (globalThis as unknown as {
      SpeechRecognition?: new () => SpeechRecognitionLike;
      webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    }).SpeechRecognition ||
    (globalThis as unknown as {
      webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    }).webkitSpeechRecognition;

  if (!SpeechRecognition) {
    return Promise.resolve({ error: fallbackListenError("web") });
  }

  return new Promise((resolve) => {
    const recognition = new SpeechRecognition();
    recognition.lang = lang;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const text = event.results?.[0]?.[0]?.transcript?.trim() || "";
      resolve(text ? { text } : { error: "Rien entendu." });
    };
    recognition.onerror = () => resolve({ error: "Ecoute interrompue." });
    recognition.onend = () => undefined;
    try {
      recognition.start();
    } catch {
      resolve({ error: "Impossible de demarrer le micro." });
    }
  });
}

function listenNativeModule(
  mod: ExpoSpeechRecognitionModule,
  lang: string
): Promise<ListenResult> {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (result: ListenResult) => {
      if (settled) return;
      settled = true;
      try {
        mod.stop?.();
      } catch {
        /* ignore */
      }
      resolve(result);
    };

    const timer = setTimeout(
      () => finish({ error: "Temps d'écoute dépassé." }),
      8000
    );

    void (async () => {
      try {
        if (mod.requestPermissionsAsync) {
          const perm = await mod.requestPermissionsAsync();
          if (perm && perm.granted === false && perm.status !== "granted") {
            clearTimeout(timer);
            finish({
              error: "Micro refusé. Utilise le clavier puis Envoyer.",
            });
            return;
          }
        }
        const subResult = mod.addListener?.("result", (ev) => {
          if (ev?.isFinal === false) return;
          const text = (ev?.transcript || "").trim();
          clearTimeout(timer);
          subResult?.remove();
          subError?.remove();
          finish(text ? { text } : { error: "Rien entendu." });
        });
        const subError = mod.addListener?.("error", () => {
          clearTimeout(timer);
          subResult?.remove();
          subError?.remove();
          finish({ error: "Ecoute interrompue." });
        });
        mod.start?.({
          lang,
          interimResults: false,
          continuous: false,
        });
      } catch {
        clearTimeout(timer);
        finish({ error: fallbackListenError("native") });
      }
    })();
  });
}

/**
 * STT appareil :
 * - web : Web Speech API
 * - natif : expo-speech-recognition (plugin app.json) si le module est lié
 * - sinon : message clavier via fallbackListenError
 */
export function listenOnce(lang = "fr-FR"): Promise<ListenResult> {
  if (Platform.OS === "web") {
    return listenWeb(lang);
  }
  const native = tryNativeSpeechRecognition();
  if (native?.start) {
    return listenNativeModule(native, lang);
  }
  return Promise.resolve({ error: fallbackListenError(Platform.OS) });
}

/** Push-to-talk : même chemin que listenOnce. */
export async function pushToTalk(lang = "fr-FR"): Promise<ListenResult> {
  return listenOnce(lang);
}

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult:
    | ((event: {
        results?: {
          [i: number]: { [j: number]: { transcript?: string } };
        };
      }) => void)
    | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
};
