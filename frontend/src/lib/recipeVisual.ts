import type { Recette } from "@/api/repas";

/**
 * Aucune recette n'a de photo en base — on dérive une identité visuelle
 * stable (emoji + couleur) à partir de ses tags/nom plutôt que d'inventer
 * une image qui n'existe pas.
 */
type Visual = { emoji: string; bg: string };

const PALETTE: Record<string, Visual> = {
  petit_dejeuner: { emoji: "☀️", bg: "#FBEBC7" },
  dejeuner: { emoji: "🍲", bg: "#DCE8DF" },
  diner: { emoji: "🌙", bg: "#DCE4EF" },
};

const FALLBACK: Visual[] = [
  { emoji: "🍚", bg: "#F3E6D8" },
  { emoji: "🥗", bg: "#E1EAE0" },
  { emoji: "🍛", bg: "#F6E2D3" },
  { emoji: "🍜", bg: "#EFE3D0" },
];

function hash(str: string): number {
  let h = 0;
  for (let i = 0; i < str.length; i += 1) {
    h = (h << 5) - h + str.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

export function recetteVisual(recette: Pick<Recette, "nom" | "tags">): Visual {
  const slot = recette.tags.find((t) => PALETTE[t]);
  if (slot) return PALETTE[slot];
  return FALLBACK[hash(recette.nom) % FALLBACK.length];
}
