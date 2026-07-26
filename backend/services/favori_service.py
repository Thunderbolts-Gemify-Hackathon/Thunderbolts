from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.favori_recette import FavoriRecette
from backend.models.recette import Recette


def list_favoris(db: Session, profil_id: str) -> list[FavoriRecette]:
    return (
        db.query(FavoriRecette)
        .filter(FavoriRecette.profil_id == profil_id)
        .order_by(FavoriRecette.id)
        .all()
    )


def is_favori(db: Session, profil_id: str, recette_id: str) -> bool:
    return (
        db.query(FavoriRecette)
        .filter(
            FavoriRecette.profil_id == profil_id,
            FavoriRecette.recette_id == recette_id,
        )
        .first()
        is not None
    )


def toggle_favori(db: Session, profil_id: str, recette_id: str) -> dict:
    if not db.get(Recette, recette_id):
        raise ValueError("Recette introuvable")
    existing = (
        db.query(FavoriRecette)
        .filter(
            FavoriRecette.profil_id == profil_id,
            FavoriRecette.recette_id == recette_id,
        )
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"favori": False, "recette_id": recette_id}
    fav = FavoriRecette(profil_id=profil_id, recette_id=recette_id)
    db.add(fav)
    db.commit()
    return {"favori": True, "recette_id": recette_id}
