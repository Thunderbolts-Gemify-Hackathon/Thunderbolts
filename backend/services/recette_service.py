from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from backend.models.ingredient import Ingredient
from backend.models.recette import Recette, RecetteIngredient
from backend.schemas.recette import RecetteCreate


def list_recettes(
    db: Session,
    *,
    q: str | None = None,
    tags: list[str] | None = None,
    max_duree: int | None = None,
    profil_id: str | None = None,
) -> list[Recette]:
    query = db.query(Recette).options(
        joinedload(Recette.ingredients).joinedload(RecetteIngredient.ingredient)
    )
    # Catalogue global + recettes user du profil
    if profil_id:
        from sqlalchemy import or_

        query = query.filter(
            or_(Recette.owner_profil_id.is_(None), Recette.owner_profil_id == profil_id)
        )
    else:
        query = query.filter(Recette.owner_profil_id.is_(None))

    if q:
        query = query.filter(Recette.nom.ilike(f"%{q.strip()}%"))
    if max_duree is not None:
        query = query.filter(Recette.duree_minutes.isnot(None))
        query = query.filter(Recette.duree_minutes <= max_duree)
    rows = query.order_by(Recette.nom).all()
    if tags:
        wanted = {t.strip().lower() for t in tags if t.strip()}
        rows = [
            r
            for r in rows
            if wanted.intersection({str(t).lower() for t in (r.tags or [])})
        ]
    return rows


def get_recette(db: Session, recette_id: str) -> Recette | None:
    return (
        db.query(Recette)
        .options(joinedload(Recette.ingredients).joinedload(RecetteIngredient.ingredient))
        .filter(Recette.id == recette_id)
        .first()
    )


def create_user_recette(
    db: Session, profil_id: str, payload: RecetteCreate
) -> Recette:
    for line in payload.ingredients:
        if not db.get(Ingredient, line.ingredient_id):
            raise ValueError(f"Ingrédient introuvable: {line.ingredient_id}")
    recette = Recette(
        nom=payload.nom.strip(),
        kcal_total=payload.kcal_total,
        proteines=payload.proteines,
        glucides=payload.glucides,
        lipides=payload.lipides,
        duree_minutes=payload.duree_minutes,
        tags=payload.tags or [],
        instructions=payload.instructions,
        owner_profil_id=profil_id,
    )
    db.add(recette)
    db.flush()
    for line in payload.ingredients:
        db.add(
            RecetteIngredient(
                recette_id=recette.id,
                ingredient_id=line.ingredient_id,
                poids_requis=line.poids_requis,
                unite=line.unite,
            )
        )
    db.commit()
    return get_recette(db, recette.id)  # type: ignore[return-value]
