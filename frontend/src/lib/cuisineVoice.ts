/**
 * Parsing des commandes vocales mode cuisine (testable sans micro).
 * Tolère accents, typos fréquents et formulations courtes.
 */

export type CuisineVoiceAction =
  | "next"
  | "prev"
  | "repeat"
  | "pause"
  | "unknown";

function normalize(raw: string): string {
  return raw
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function parseCuisineVoiceCommand(raw: string): CuisineVoiceAction {
  const t = normalize(raw);
  if (!t) return "unknown";

  if (
    /\b(suivant|next|avance|apres|continuer|continue|ok suivant)\b/.test(t) ||
    t === "suivant" ||
    t === "next"
  ) {
    return "next";
  }
  if (
    /\b(precedent|retour|avant|back|previous)\b/.test(t) ||
    t === "retour"
  ) {
    return "prev";
  }
  if (
    /\b(repete|repeat|encore|redis|relire)\b/.test(t) ||
    t === "repete"
  ) {
    return "repeat";
  }
  if (/\b(pause|stop|arrete|reprendre|resume)\b/.test(t)) {
    return "pause";
  }
  return "unknown";
}
