from sqlalchemy.orm import Session

from backend.models.ingredient import Ingredient


def list_ingredients(db: Session) -> list[Ingredient]:
    return db.query(Ingredient).order_by(Ingredient.nom.asc()).all()
