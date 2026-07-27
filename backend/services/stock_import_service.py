from __future__ import annotations

import base64
import binascii
import re

from sqlalchemy.orm import Session

from backend.models.ingredient import Ingredient
from backend.schemas.stock import IngredientStockUpsert
from backend.services import stock_service

_LINE_RE = re.compile(
    r"^\s*(?P<label>.+?)\s+(?P<qty>\d+(?:[.,]\d+)?)\s*(?P<unite>g|kg|ml|l|u|pcs?)?\s*$",
    re.IGNORECASE,
)

_OCR_PROMPT = (
    "Extrais la liste d'ingrédients visibles sur l'image, une ligne par item, "
    "format exact: « nom quantite unite » (ex: tomate 500g). "
    "Réponds uniquement avec les lignes, sans autre texte."
)


def parse_import_text(text: str) -> list[dict]:
    lines = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        m = _LINE_RE.match(raw)
        if m:
            label = m.group("label").strip()
            qty = float(m.group("qty").replace(",", "."))
            unite = (m.group("unite") or "g").lower()
            if unite in ("kg",):
                qty *= 1000
                unite = "g"
            elif unite in ("l",):
                qty *= 1000
                unite = "ml"
            elif unite in ("pc", "pcs", "u"):
                unite = "unite"
        else:
            parts = raw.rsplit(maxsplit=1)
            label = parts[0]
            qty = 1.0
            unite = "unite"
            if len(parts) == 2 and parts[1].replace(",", "").replace(".", "").isdigit():
                qty = float(parts[1].replace(",", "."))
        lines.append({"label": label, "quantite": qty, "unite": unite})
    return lines


def decode_image_payload(image_base64: str) -> tuple[bytes, str | None]:
    """Décode base64 (data URL ok). Retourne (raw_bytes, text_hook_or_none).

    Hook de test : si le contenu décodé commence par ``text:`` (insensible à la casse),
    le reste est traité comme texte d'import (sans OCR réel).
    """
    raw = image_base64.strip()
    if "," in raw and raw.lower().startswith("data:"):
        raw = raw.split(",", 1)[1]
    try:
        data = base64.b64decode(raw, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("image_base64 invalide") from exc

    try:
        as_text = data.decode("utf-8")
    except UnicodeDecodeError:
        as_text = None

    if as_text is not None:
        stripped = as_text.lstrip()
        lower = stripped.lower()
        if lower.startswith("text:"):
            return data, stripped[5:].lstrip()
        if "\n" in stripped or _LINE_RE.match(stripped):
            return data, stripped

    return data, None


def extract_text_via_gemma(image_base64: str) -> str | None:
    """Tente Gemma vision si une clé API est dispo ; sinon None."""
    try:
        from backend.services.gemma_client import GemmaClient

        client = GemmaClient()
        if not getattr(client, "gemma4_api_key", None):
            return None
        b64 = image_base64.strip()
        if "," in b64 and b64.lower().startswith("data:"):
            b64 = b64.split(",", 1)[1]
        messages = [{"role": "user", "content": _OCR_PROMPT}]
        chat_image = getattr(client, "chat_image", None)
        if callable(chat_image):
            out = chat_image(messages, b64, "image/jpeg")
            content = (out or {}).get("content") or ""
            return content.strip() or None
        return None
    except Exception:
        return None


def resolve_import_text(
    *, text: str | None = None, image_base64: str | None = None
) -> tuple[str, str]:
    """Retourne (texte_à_parser, source)."""
    if text and text.strip():
        return text.strip(), "text"
    if not image_base64 or not image_base64.strip():
        raise ValueError("text ou image_base64 requis")

    _data, hook = decode_image_payload(image_base64)
    if hook:
        return hook, "image_text_hook"

    gemma_text = extract_text_via_gemma(image_base64)
    if gemma_text:
        return gemma_text, "gemma_vision"

    raise ValueError(
        "OCR indisponible pour cette image — utilise import-text ou "
        "passe image_base64 décodable en « text:… » (tests)."
    )


def import_text(
    db: Session,
    profil_id: str,
    text: str,
    *,
    apply: bool = False,
    source: str = "text",
) -> dict:
    parsed = parse_import_text(text)
    ingredients = {i.nom.lower(): i for i in db.query(Ingredient).all()}
    result_lines = []
    applied = 0
    for row in parsed:
        key = row["label"].lower()
        ing = ingredients.get(key)
        if not ing:
            for nom, candidate in ingredients.items():
                if key in nom or nom in key:
                    ing = candidate
                    break
        line = {
            "label": row["label"],
            "quantite": row["quantite"],
            "unite": row["unite"],
            "ingredient_id": ing.id if ing else None,
            "matched": ing is not None,
        }
        result_lines.append(line)
        if apply and ing:
            unite = (
                row["unite"] if row["unite"] in ("g", "ml", "unite", "kg", "l") else "g"
            )
            qty = row["quantite"]
            if unite == "kg":
                qty *= 1000
                unite = "g"
            elif unite == "l":
                qty *= 1000
                unite = "ml"
            if unite not in ("g", "ml", "unite"):
                unite = "g"
            stock_service.upsert_ingredient_stock(
                db,
                profil_id,
                IngredientStockUpsert(
                    ingredient_id=ing.id,
                    quantite_disponible=qty,
                    unite=unite,  # type: ignore[arg-type]
                ),
            )
            applied += 1
    return {"lines": result_lines, "applied": applied, "source": source}


def import_image(
    db: Session,
    profil_id: str,
    *,
    image_base64: str | None = None,
    text: str | None = None,
    apply: bool = False,
) -> dict:
    resolved, source = resolve_import_text(text=text, image_base64=image_base64)
    return import_text(db, profil_id, resolved, apply=apply, source=source)
