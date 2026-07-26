from datetime import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.ingredient import IngredientOut


class RecetteIngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient: IngredientOut
    poids_requis: float
    unite: str


class RecetteIngredientIn(BaseModel):
    ingredient_id: str
    poids_requis: float = Field(gt=0)
    unite: str = "g"


class RecetteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nom: str
    heure_conseillee: Optional[time] = None
    kcal_total: float
    proteines: float
    glucides: float
    lipides: float
    duree_minutes: Optional[int] = None
    tags: list[str]
    instructions: Optional[str] = None
    owner_profil_id: Optional[str] = None
    ingredients: list[RecetteIngredientOut] = Field(default_factory=list)


class RecetteCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    kcal_total: float = 0
    proteines: float = 0
    glucides: float = 0
    lipides: float = 0
    duree_minutes: Optional[int] = None
    tags: list[str] = Field(default_factory=list)
    instructions: Optional[str] = None
    ingredients: list[RecetteIngredientIn] = Field(default_factory=list)
