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
 * STT appareil :
 * - web : Web Speech API
 * - natif Expo Go : le micro du clavier système (appelant focus l'input)
 *   Ici on tente aussi webkit si dispo (rare hors web).
 */
export function listenOnce(lang = "fr-FR"): Promise<ListenResult> {
  if (Platform.OS !== "web") {
    return Promise.resolve({
      error:
        "Sur telephone, utilise le micro du clavier puis Envoyer. La reponse sera lue a voix haute.",
    });
  }

  const SpeechRecognition =
    (globalThis as unknown as {
      SpeechRecognition?: new () => SpeechRecognitionLike;
      webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    }).SpeechRecognition ||
    (globalThis as unknown as {
      webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    }).webkitSpeechRecognition;

  if (!SpeechRecognition) {
    return Promise.resolve({
      error: "Reconnaissance vocale indisponible sur ce navigateur.",
    });
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

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((event: { results?: { [i: number]: { [j: number]: { transcript?: string } } } }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
};
