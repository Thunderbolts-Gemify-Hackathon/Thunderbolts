from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.ingredient import Unite


class IngredientStockUpsert(BaseModel):
    ingredient_id: str
    quantite_disponible: float = Field(ge=0)
    unite: Unite
    date_peremption: Optional[date] = None


class StockCreate(BaseModel):
    lieu_stockage: str = Field(default="cuisine", min_length=1, max_length=50)
    ingredients: list[IngredientStockUpsert] = Field(default_factory=list)


class IngredientStockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    stock_id: str
    ingredient_id: str
    quantite_disponible: float
    unite: str
    date_peremption: Optional[date] = None


class StockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    lieu_stockage: str
    derniere_mise_a_jour: datetime
    ingredients: list[IngredientStockOut] = Field(default_factory=list)
