import type { EtapeRecette } from "@/api/chat";

/**
 * Normalise n'importe quelle forme de réponse `/etapes` en tableau sûr.
 * Filtre aussi les titres JSON bruts (`{`, `"titre"`, etc.) qui rendaient
 * l'écran cuisine illisible.
 */
export function normalizeEtapes(payload: unknown): EtapeRecette[] {
  const raw = extractRawList(payload);
  if (!raw) return [];

  const etapes: EtapeRecette[] = [];
  for (let i = 0; i < raw.length; i++) {
    const item = raw[i];
    if (typeof item === "string") {
      const titre = cleanTitre(item);
      if (titre) etapes.push({ numero: etapes.length + 1, titre, ingredients: [] });
      continue;
    }
    if (!item || typeof item !== "object") continue;
    const obj = item as Record<string, unknown>;
    const titre = cleanTitre(
      obj.titre ?? obj.titre_etape ?? obj.etape ?? obj.instruction ?? obj.description ?? ""
    );
    if (!titre) continue;
    const ingredients = Array.isArray(obj.ingredients)
      ? obj.ingredients.map((x) => String(x).trim()).filter(Boolean)
      : [];
    const numero = Number(obj.numero);
    etapes.push({
      numero: Number.isFinite(numero) && numero > 0 ? numero : etapes.length + 1,
      titre,
      ingredients,
    });
  }
  return etapes;
}

export function cleanTitre(value: unknown): string {
  let titre = String(value ?? "").trim();
  if (!titre) return "";
  if (titre.startsWith("{") || titre.startsWith("[")) return "";
  if (titre.includes('"titre"') || titre.includes("'titre'")) return "";
  titre = titre.replace(/^\s*(?:\d+[.)]|[-*])\s*/, "").replace(/^["'\s]+|["'\s]+$/g, "");
  if (titre.length < 2 || titre.length > 180) return "";
  return titre;
}

function extractRawList(payload: unknown): unknown[] | null {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return null;
  const obj = payload as Record<string, unknown>;
  if (Array.isArray(obj.etapes)) return obj.etapes;
  if (obj.etapes && typeof obj.etapes === "object" && !Array.isArray(obj.etapes)) {
    const inner = obj.etapes as Record<string, unknown>;
    if (Array.isArray(inner.etapes)) return inner.etapes;
  }
  return null;
}
