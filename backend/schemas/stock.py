from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.ingredient import Unite


class StockCreate(BaseModel):
    profil_id: str
    lieu_stockage: str = "cuisine"


class StockUpdate(BaseModel):
    lieu_stockage: Optional[str] = None


class StockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    lieu_stockage: str
    derniere_mise_a_jour: datetime


class IngredientStockCreate(BaseModel):
    stock_id: str
    ingredient_id: str
    quantite_disponible: float = Field(ge=0)
    unite: Unite
    date_peremption: Optional[date] = None


class IngredientStockUpdate(BaseModel):
    quantite_disponible: Optional[float] = Field(default=None, ge=0)
    unite: Optional[Unite] = None
    date_peremption: Optional[date] = None


class IngredientStockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    stock_id: str
    ingredient_id: str
    quantite_disponible: float
    unite: str
    date_peremption: Optional[date] = None
