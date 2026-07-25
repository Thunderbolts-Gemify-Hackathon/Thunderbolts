from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.ingredient import IngredientOut
from backend.services import ingredient_service

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=list[IngredientOut])
def list_ingredients(db: Session = Depends(get_db)):
    return ingredient_service.list_ingredients(db)
