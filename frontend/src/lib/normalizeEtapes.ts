import type { EtapeRecette } from "@/api/chat";

/**
 * Normalise n'importe quelle forme de réponse `/etapes` en tableau sûr.
 * Gemma / proxies renvoient parfois le tableau à la racine, parfois
 * `{ etapes: [...] }`, parfois un objet malformé — sans ça le mode cuisine
 * plante sur `etapes.map is not a function`.
 */
export function normalizeEtapes(payload: unknown): EtapeRecette[] {
  const raw = extractRawList(payload);
  if (!raw) return [];

  const etapes: EtapeRecette[] = [];
  for (let i = 0; i < raw.length; i++) {
    const item = raw[i];
    if (typeof item === "string" && item.trim()) {
      etapes.push({ numero: etapes.length + 1, titre: item.trim(), ingredients: [] });
      continue;
    }
    if (!item || typeof item !== "object") continue;
    const obj = item as Record<string, unknown>;
    const titre = String(
      obj.titre ?? obj.titre_etape ?? obj.etape ?? obj.instruction ?? obj.description ?? ""
    ).trim();
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

function extractRawList(payload: unknown): unknown[] | null {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return null;
  const obj = payload as Record<string, unknown>;
  if (Array.isArray(obj.etapes)) return obj.etapes;
  // Double enveloppe occasionnelle : { etapes: { etapes: [...] } }
  if (obj.etapes && typeof obj.etapes === "object" && !Array.isArray(obj.etapes)) {
    const inner = obj.etapes as Record<string, unknown>;
    if (Array.isArray(inner.etapes)) return inner.etapes;
  }
  return null;
}
