from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_utilisateur
from backend.models.utilisateur import Utilisateur
from backend.schemas.ingredient import IngredientOut
from backend.services import ingredient_service

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=list[IngredientOut])
def list_ingredients(
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_utilisateur),
):
    return ingredient_service.list_ingredients(db)
