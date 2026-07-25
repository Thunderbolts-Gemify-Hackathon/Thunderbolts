from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class IngredientStockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    stock_id: str
    ingredient_id: str
    quantite_disponible: float
    unite: str
    date_peremption: Optional[date] = None
