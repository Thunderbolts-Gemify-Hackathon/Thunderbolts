from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock, Stock
from backend.schemas.composites import RuptureOut
from backend.schemas.ingredient import IngredientOut


def get_stock_profil(db: Session, profil_id: str) -> list[IngredientStock]:
    stock = (
        db.query(Stock)
        .options(joinedload(Stock.ingredients).joinedload(IngredientStock.ingredient))
        .filter(Stock.profil_id == profil_id)
        .first()
    )
    return list(stock.ingredients) if stock else []


def _get_ingredient_stock(
    db: Session, profil_id: str, ingredient_id: str
) -> IngredientStock:
    ligne = (
        db.query(IngredientStock)
        .join(Stock)
        .filter(Stock.profil_id == profil_id, IngredientStock.ingredient_id == ingredient_id)
        .first()
    )
    if not ligne:
        raise HTTPException(status_code=404, detail="Ingrédient introuvable dans le stock du profil")
    return ligne


def _ajuster_stock(
    db: Session,
    profil_id: str,
    ingredient_id: str,
    delta: float,
    *,
    commit: bool = True,
    clamp_zero: bool = False,
) -> IngredientStock:
    ligne = _get_ingredient_stock(db, profil_id, ingredient_id)
    nouvelle = ligne.quantite_disponible + delta
    ligne.quantite_disponible = max(0.0, nouvelle) if clamp_zero else nouvelle
    ligne.stock.derniere_mise_a_jour = datetime.now(timezone.utc).replace(tzinfo=None)
    if commit:
        db.commit()
        db.refresh(ligne)
    else:
        db.flush()
    return ligne


def update_stock(
    db: Session,
    profil_id: str,
    ingredient_id: str,
    quantite_a_deduire: float,
    *,
    commit: bool = True,
) -> IngredientStock:
    if quantite_a_deduire < 0:
        raise HTTPException(status_code=400, detail="quantite_a_deduire doit être >= 0")
    return _ajuster_stock(
        db, profil_id, ingredient_id, -quantite_a_deduire, commit=commit, clamp_zero=True
    )


def recrediter_stock(
    db: Session,
    profil_id: str,
    ingredient_id: str,
    quantite: float,
    *,
    commit: bool = True,
) -> IngredientStock:
    if quantite < 0:
        raise HTTPException(status_code=400, detail="quantite doit être >= 0")
    return _ajuster_stock(db, profil_id, ingredient_id, quantite, commit=commit)


def detecter_ruptures(db: Session, profil_id: str, planning_id: str) -> list[RuptureOut]:
    planning = (
        db.query(Planning)
        .options(
            joinedload(Planning.repas)
            .joinedload(RepasPlanifie.recette)
            .joinedload(Recette.ingredients)
            .joinedload(RecetteIngredient.ingredient)
        )
        .filter(Planning.id == planning_id, Planning.profil_id == profil_id)
        .first()
    )
    if not planning:
        raise HTTPException(status_code=404, detail="Planning introuvable pour ce profil")

    requis: dict[str, float] = defaultdict(float)
    ingredients_map: dict[str, Ingredient] = {}
    for repas in planning.repas:
        if repas.statut == "annule":
            continue
        for ligne in repas.recette.ingredients:
            requis[ligne.ingredient_id] += ligne.poids_requis
            ingredients_map[ligne.ingredient_id] = ligne.ingredient

    stock_dispo = {
        ligne.ingredient_id: ligne.quantite_disponible
        for ligne in get_stock_profil(db, profil_id)
    }

    ruptures = []
    for ingredient_id, poids_requis in requis.items():
        manquant = poids_requis - stock_dispo.get(ingredient_id, 0.0)
        if manquant > 0:
            ruptures.append(
                RuptureOut(
                    ingredient=IngredientOut.model_validate(ingredients_map[ingredient_id]),
                    quantite_manquante=round(manquant, 2),
                )
            )
    return ruptures


def check_expiry(db: Session, profil_id: str, jours: int = 7) -> list[IngredientStock]:
    limite = date.today() + timedelta(days=jours)
    return [
        ligne
        for ligne in get_stock_profil(db, profil_id)
        if ligne.date_peremption is not None and ligne.date_peremption <= limite
    ]
