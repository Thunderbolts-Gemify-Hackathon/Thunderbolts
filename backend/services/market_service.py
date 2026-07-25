"""Service marchés / points de vente — contrat outils Gemma (implémentation Dev 2)."""

from __future__ import annotations

from sqlalchemy.orm import Session


def find_nearby_market(
    db: Session,
    ingredient_id: str,
    lat: float,
    lon: float,
) -> dict:
    """Points de vente pour un ingrédient, triés par prix + niveau de sécurité."""
    raise NotImplementedError(
        "market_service.find_nearby_market - a implementer par Dev 2"
    )
