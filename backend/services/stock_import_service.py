from __future__ import annotations

import re

from sqlalchemy.orm import Session

from backend.models.ingredient import Ingredient
from backend.schemas.stock import IngredientStockUpsert
from backend.services import stock_service

_LINE_RE = re.compile(
    r"^\s*(?P<label>.+?)\s+(?P<qty>\d+(?:[.,]\d+)?)\s*(?P<unite>g|kg|ml|l|u|pcs?)?\s*$",
    re.IGNORECASE,
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
            # "tomate" seul
            parts = raw.rsplit(maxsplit=1)
            label = parts[0]
            qty = 1.0
            unite = "unite"
            if len(parts) == 2 and parts[1].replace(",", "").replace(".", "").isdigit():
                qty = float(parts[1].replace(",", "."))
        lines.append({"label": label, "quantite": qty, "unite": unite})
    return lines


def import_text(
    db: Session, profil_id: str, text: str, *, apply: bool = False
) -> dict:
    parsed = parse_import_text(text)
    ingredients = {i.nom.lower(): i for i in db.query(Ingredient).all()}
    result_lines = []
    applied = 0
    for row in parsed:
        key = row["label"].lower()
        ing = ingredients.get(key)
        # fuzzy: substring
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
            unite = row["unite"] if row["unite"] in ("g", "ml", "unite", "kg", "l") else "g"
            if unite == "kg":
                row["quantite"] *= 1000
                unite = "g"
            elif unite == "l":
                row["quantite"] *= 1000
                unite = "ml"
            if unite not in ("g", "ml", "unite"):
                unite = "g"
            stock_service.upsert_ingredient_stock(
                db,
                profil_id,
                IngredientStockUpsert(
                    ingredient_id=ing.id,
                    quantite_disponible=row["quantite"],
                    unite=unite,  # type: ignore[arg-type]
                ),
            )
            applied += 1
    return {"lines": result_lines, "applied": applied}
