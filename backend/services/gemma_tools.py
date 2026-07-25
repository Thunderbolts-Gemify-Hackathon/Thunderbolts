"""Schémas d'outils Gemma (contrat Dev 2) + routeur d'exécution."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"
LOG_FILE = LOG_DIR / "tool_calls.log"

# Format JSON Schema / function calling (compatible OpenAI, Ollama, Gemini).
TOOLS: list[dict[str, Any]] = [
    {
        "name": "check_budget",
        "description": (
            "Vérifie si un montant est disponible dans le budget du profil "
            "avant de suggérer un achat"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "profil_id": {
                    "type": "string",
                    "description": "Identifiant du profil utilisateur",
                },
                "cout_estime": {
                    "type": "number",
                    "description": "Coût estimé de l'achat à valider",
                },
            },
            "required": ["profil_id", "cout_estime"],
        },
    },
    {
        "name": "find_nearby_market",
        "description": (
            "Trouve les points de vente proposant un ingrédient donné, "
            "triés par prix, avec niveau de sécurité"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ingredient_id": {
                    "type": "string",
                    "description": "Identifiant de l'ingrédient recherché",
                },
                "lat": {
                    "type": "number",
                    "description": "Latitude de l'utilisateur",
                },
                "lon": {
                    "type": "number",
                    "description": "Longitude de l'utilisateur",
                },
            },
            "required": ["ingredient_id", "lat", "lon"],
        },
    },
    {
        "name": "check_expiry",
        "description": "Liste les ingrédients du stock proches de la péremption",
        "parameters": {
            "type": "object",
            "properties": {
                "profil_id": {
                    "type": "string",
                    "description": "Identifiant du profil utilisateur",
                },
            },
            "required": ["profil_id"],
        },
    },
    {
        "name": "update_stock",
        "description": (
            "Déduit une quantité du stock après validation d'un repas "
            "(ne jamais appeler avec une estimation, toujours avec le poids "
            "exact de la recette)"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "profil_id": {
                    "type": "string",
                    "description": "Identifiant du profil utilisateur",
                },
                "ingredient_id": {
                    "type": "string",
                    "description": "Identifiant de l'ingrédient à déduire",
                },
                "quantite_a_deduire": {
                    "type": "number",
                    "description": "Quantité exacte à déduire du stock",
                },
            },
            "required": ["profil_id", "ingredient_id", "quantite_a_deduire"],
        },
    },
]


def execute_tool_call(db: Session, tool_name: str, arguments: dict) -> dict:
    """Route un tool call Gemma vers les services backend (Dev 2), sans réimplémenter."""
    args = dict(arguments or {})
    try:
        result = _dispatch(db, tool_name, args)
        payload = _to_jsonable(result)
        _log_tool_call(tool_name, args, payload)
        return payload if isinstance(payload, dict) else {"result": payload}
    except Exception as exc:  # noqa: BLE001 — log + surface à Gemma
        error_payload = {"error": str(exc), "tool": tool_name}
        _log_tool_call(tool_name, args, error_payload)
        return error_payload


def _dispatch(db: Session, tool_name: str, arguments: dict) -> Any:
    # Imports locaux : même code que Dev 2 (pas de logique dupliquée ici).
    if tool_name == "check_budget":
        from backend.services.budget_service import check_budget

        return check_budget(
            db,
            profil_id=arguments["profil_id"],
            cout_estime=float(arguments["cout_estime"]),
        )

    if tool_name == "find_nearby_market":
        from backend.services.market_service import find_nearby_market

        return find_nearby_market(
            db,
            ingredient_id=arguments["ingredient_id"],
            lat=float(arguments["lat"]),
            lon=float(arguments["lon"]),
        )

    if tool_name == "check_expiry":
        from backend.services.stock_service import check_expiry

        return check_expiry(db, profil_id=arguments["profil_id"])

    if tool_name == "update_stock":
        from backend.services.stock_service import update_stock

        return update_stock(
            db,
            profil_id=arguments["profil_id"],
            ingredient_id=arguments["ingredient_id"],
            quantite_a_deduire=float(arguments["quantite_a_deduire"]),
        )

    raise ValueError(f"Outil inconnu: {tool_name}")


def _log_tool_call(tool_name: str, arguments: dict, result: Any) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    line = (
        f"{ts} | {tool_name} | args={json.dumps(arguments, ensure_ascii=False)} "
        f"| result={json.dumps(result, ensure_ascii=False, default=str)}\n"
    )
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line)
    print(f"[tool_call] {tool_name} args={arguments} result={result}")


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
        # SQLAlchemy ORM → dict colonnes
        return {c.name: _to_jsonable(getattr(value, c.name)) for c in value.__table__.columns}
    return str(value)
