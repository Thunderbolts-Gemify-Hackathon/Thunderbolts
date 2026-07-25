"""Service budget — contrat outils Gemma (implémentation Dev 2)."""

from __future__ import annotations

from sqlalchemy.orm import Session


def check_budget(db: Session, profil_id: str, cout_estime: float) -> dict:
    """Vérifie si cout_estime est disponible dans le budget du profil."""
    raise NotImplementedError(
        "budget_service.check_budget - a implementer par Dev 2"
    )
