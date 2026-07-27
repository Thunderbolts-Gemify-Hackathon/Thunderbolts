from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

LOG_FILE = Path(__file__).resolve().parents[2] / "logs" / "tool_calls.log"

# profil_id, ingredient UUID et coordonnées ne sont jamais fournis par le modèle :
# il ne les connaît pas et les invente sinon (ex. "user_1"), ce qui fait échouer
# silencieusement l'outil ou boucler jusqu'à MAX_TOOL_ITERATIONS. On les relie côté
# serveur (profil authentifié, nom d'ingrédient -> id, localisation du profil).
TOOLS: list[dict[str, Any]] = [
    {
        "name": "check_budget",
        "description": "Vérifie si un montant est disponible dans le budget du profil",
        "parameters": {
            "type": "object",
            "properties": {
                "cout_estime": {"type": "number"},
            },
            "required": ["cout_estime"],
        },
    },
    {
        "name": "find_nearby_market",
        "description": "Points de vente pour un ingrédient (par nom), triés par prix et sécurité",
        "parameters": {
            "type": "object",
            "properties": {
                "ingredient_nom": {"type": "string"},
            },
            "required": ["ingredient_nom"],
        },
    },
    {
        "name": "find_nearest_supermarkets",
        "description": (
            "Points de vente les plus proches de la localisation du profil, sans filtre "
            "par ingrédient — à utiliser quand l'utilisateur demande juste où se trouve "
            "le marché/supermarché le plus proche, ou comment y aller, sans produit précis."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "type_souhaite": {
                    "type": "string",
                    "description": "Optionnel : grande_surface, epicerie, marche, grossiste",
                },
            },
        },
    },
    {
        "name": "check_expiry",
        "description": "Ingrédients du stock proches de la péremption",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "update_stock",
        "description": "Déduit une quantité exacte du stock après validation d'un repas",
        "parameters": {
            "type": "object",
            "properties": {
                "ingredient_nom": {"type": "string"},
                "quantite_a_deduire": {"type": "number"},
            },
            "required": ["ingredient_nom", "quantite_a_deduire"],
        },
    },
    {
        "name": "add_shopping_items",
        "description": "Ajoute des articles à la liste de courses du profil",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "quantite": {"type": "number"},
                            "unite": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["items"],
        },
    },
    {
        "name": "swap_meal",
        "description": "Remplace le prochain dîner du planning par une recette (id connu)",
        "parameters": {
            "type": "object",
            "properties": {
                "recette_id": {"type": "string"},
                "jour": {"type": "string"},
            },
            "required": ["recette_id"],
        },
    },
    {
        "name": "get_local_price",
        "description": "Prix local crowd/catalogue pour un ingrédient (par nom)",
        "parameters": {
            "type": "object",
            "properties": {
                "ingredient_nom": {"type": "string"},
                "quartier": {"type": "string"},
            },
            "required": ["ingredient_nom"],
        },
    },
]


def execute_tool_call(
    db: Session, profil_id: str, tool_name: str, arguments: dict
) -> dict:
    from backend.services import llm_metrics

    args = dict(arguments or {})
    try:
        result = _dispatch(db, profil_id, tool_name, args)
        payload = _to_jsonable(result)
        _log_tool_call(tool_name, args, payload)
        llm_metrics.record_event(
            "tool_ok",
            profil_id=profil_id,
            detail={"tool": tool_name},
        )
        return payload if isinstance(payload, dict) else {"result": payload}
    except Exception as exc:  # noqa: BLE001
        error = {"error": str(exc), "tool": tool_name}
        _log_tool_call(tool_name, args, error)
        llm_metrics.record_event(
            "tool_fail",
            profil_id=profil_id,
            detail={"tool": tool_name, "error": str(exc)},
        )
        return error


def _resolve_ingredient_id(db: Session, ingredient_nom: str) -> str:
    from backend.models.ingredient import Ingredient

    nom = (ingredient_nom or "").strip()
    ingredient = db.query(Ingredient).filter(Ingredient.nom.ilike(nom)).first()
    if not ingredient:
        raise ValueError(f"Ingrédient introuvable: {ingredient_nom}")
    return ingredient.id


def _dispatch(db: Session, profil_id: str, tool_name: str, arguments: dict) -> Any:
    if tool_name == "check_budget":
        from backend.services.budget_service import check_budget

        return check_budget(
            db,
            profil_id=profil_id,
            cout_estime=float(arguments["cout_estime"]),
        )

    if tool_name == "find_nearby_market":
        from backend.models.localisation import Localisation
        from backend.services.market_service import find_nearby_market

        loc = db.query(Localisation).filter(Localisation.profil_id == profil_id).first()
        if not loc:
            raise ValueError("Localisation manquante pour ce profil")
        ingredient_id = _resolve_ingredient_id(db, arguments["ingredient_nom"])
        return find_nearby_market(
            db,
            ingredient_id=ingredient_id,
            lat=loc.latitude,
            lon=loc.longitude,
            profil_id=profil_id,
        )

    if tool_name == "find_nearest_supermarkets":
        from backend.models.localisation import Localisation
        from backend.services.market_service import find_nearest_points_de_vente

        loc = db.query(Localisation).filter(Localisation.profil_id == profil_id).first()
        if not loc:
            raise ValueError("Localisation manquante pour ce profil")
        return find_nearest_points_de_vente(
            db,
            lat=loc.latitude,
            lon=loc.longitude,
            type_souhaite=arguments.get("type_souhaite"),
            profil_id=profil_id,
        )

    if tool_name == "check_expiry":
        from backend.services.stock_alerts import check_expiry

        lignes = check_expiry(db, profil_id=profil_id)
        return [
            {
                "ingredient_nom": ligne.ingredient.nom,
                "quantite_disponible": ligne.quantite_disponible,
                "unite": ligne.unite,
                "date_peremption": ligne.date_peremption,
            }
            for ligne in lignes
        ]

    if tool_name == "update_stock":
        from backend.services.stock_service import update_stock

        ingredient_id = _resolve_ingredient_id(db, arguments["ingredient_nom"])
        return update_stock(
            db,
            profil_id=profil_id,
            ingredient_id=ingredient_id,
            quantite_a_deduire=float(arguments["quantite_a_deduire"]),
        )

    if tool_name == "add_shopping_items":
        from backend.services.foyer_agent_service import add_shopping_items_tool

        return add_shopping_items_tool(db, profil_id, list(arguments.get("items") or []))

    if tool_name == "swap_meal":
        from backend.services.foyer_agent_service import swap_meal_tool

        return swap_meal_tool(
            db,
            profil_id,
            str(arguments["recette_id"]),
            jour=arguments.get("jour"),
        )

    if tool_name == "get_local_price":
        from backend.models.localisation import Localisation
        from backend.services.price_service import get_local_price

        quartier = arguments.get("quartier")
        if not quartier:
            loc = db.query(Localisation).filter(Localisation.profil_id == profil_id).first()
            quartier = loc.quartier if loc else None
        return get_local_price(db, arguments["ingredient_nom"], quartier=quartier)

    raise ValueError(f"Outil inconnu: {tool_name}")


def _log_tool_call(tool_name: str, arguments: dict, result: Any) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = (
        f"{datetime.now(timezone.utc).isoformat()} | {tool_name} | "
        f"args={json.dumps(arguments, ensure_ascii=False)} | "
        f"result={json.dumps(result, ensure_ascii=False, default=str)}\n"
    )
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line)


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if hasattr(value, "model_dump"):
        return _to_jsonable(value.model_dump())
    if hasattr(value, "__table__"):
        return {c.name: _to_jsonable(getattr(value, c.name)) for c in value.__table__.columns}
    return str(value)
