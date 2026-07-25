from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

LOG_FILE = Path(__file__).resolve().parents[2] / "logs" / "tool_calls.log"

TOOLS: list[dict[str, Any]] = [
    {
        "name": "check_budget",
        "description": "Vérifie si un montant est disponible dans le budget du profil",
        "parameters": {
            "type": "object",
            "properties": {
                "profil_id": {"type": "string"},
                "cout_estime": {"type": "number"},
            },
            "required": ["profil_id", "cout_estime"],
        },
    },
    {
        "name": "find_nearby_market",
        "description": "Points de vente pour un ingrédient, triés par prix et sécurité",
        "parameters": {
            "type": "object",
            "properties": {
                "ingredient_id": {"type": "string"},
                "lat": {"type": "number"},
                "lon": {"type": "number"},
            },
            "required": ["ingredient_id", "lat", "lon"],
        },
    },
    {
        "name": "check_expiry",
        "description": "Ingrédients du stock proches de la péremption",
        "parameters": {
            "type": "object",
            "properties": {"profil_id": {"type": "string"}},
            "required": ["profil_id"],
        },
    },
    {
        "name": "update_stock",
        "description": "Déduit une quantité exacte du stock après validation d'un repas",
        "parameters": {
            "type": "object",
            "properties": {
                "profil_id": {"type": "string"},
                "ingredient_id": {"type": "string"},
                "quantite_a_deduire": {"type": "number"},
            },
            "required": ["profil_id", "ingredient_id", "quantite_a_deduire"],
        },
    },
]


def execute_tool_call(db: Session, tool_name: str, arguments: dict) -> dict:
    args = dict(arguments or {})
    try:
        result = _dispatch(db, tool_name, args)
        payload = _to_jsonable(result)
        _log_tool_call(tool_name, args, payload)
        return payload if isinstance(payload, dict) else {"result": payload}
    except Exception as exc:  # noqa: BLE001
        error = {"error": str(exc), "tool": tool_name}
        _log_tool_call(tool_name, args, error)
        return error


def _dispatch(db: Session, tool_name: str, arguments: dict) -> Any:
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
        from backend.services.stock_alerts import check_expiry

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
