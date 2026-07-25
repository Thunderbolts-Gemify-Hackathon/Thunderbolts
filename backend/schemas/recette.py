from datetime import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.ingredient import IngredientOut


class RecetteIngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient: IngredientOut
    poids_requis: float
    unite: str


class RecetteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nom: str
    heure_conseillee: Optional[time] = None
    kcal_total: float
    proteines: float
    glucides: float
    lipides: float
    tags: list[str]
    instructions: Optional[str] = None
    ingredients: list[RecetteIngredientOut] = Field(default_factory=list)
