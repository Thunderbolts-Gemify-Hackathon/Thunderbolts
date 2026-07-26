"""Couverture stock d'une recette (partagée planning / « je veux manger »)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.services.stock_service import get_stock_profil
from backend.services.units import quantite_suffisante


def stock_map(db: Session, profil_id: str) -> dict[str, tuple[float, str]]:
    """ingredient_id → (quantité, unité) tels qu'enregistrés en stock."""
    return {
        ligne.ingredient_id: (float(ligne.quantite_disponible), ligne.unite)
        for ligne in get_stock_profil(db, profil_id)
    }


def avec_couverture(
    recette: dict[str, Any],
    stock_dispo: dict[str, tuple[float, str]],
) -> dict[str, Any]:
    """Ajoute `_couverture` (0..1) et `_manquants` (noms) à une recette sérialisée."""
    lignes = recette.get("ingredients") or []
    if not lignes:
        return {**recette, "_couverture": 1.0, "_manquants": []}

    manquants: list[str] = []
    couverts = 0
    for ligne in lignes:
        dispo = stock_dispo.get(ligne["ingredient_id"])
        if dispo and quantite_suffisante(
            dispo[0], dispo[1], float(ligne["poids_requis"]), ligne.get("unite")
        ):
            couverts += 1
        else:
            manquants.append(ligne["nom"])
    return {
        **recette,
        "_couverture": couverts / len(lignes),
        "_manquants": manquants,
    }
