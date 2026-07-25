"""Service stock — contrat outils Gemma (implémentation Dev 2)."""

from __future__ import annotations

from sqlalchemy.orm import Session


def check_expiry(db: Session, profil_id: str) -> dict:
    """Liste les ingrédients du stock proches de la péremption."""
    raise NotImplementedError(
        "stock_service.check_expiry - a implementer par Dev 2"
    )


def update_stock(
    db: Session,
    profil_id: str,
    ingredient_id: str,
    quantite_a_deduire: float,
) -> dict:
    """Déduit une quantité exacte du stock après validation d'un repas."""
    raise NotImplementedError(
        "stock_service.update_stock - a implementer par Dev 2"
    )
