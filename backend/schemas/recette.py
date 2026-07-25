from datetime import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.ingredient import Unite


class RecetteCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    heure_conseillee: Optional[time] = None
    kcal_total: float = Field(ge=0, default=0.0)
    proteines: float = Field(ge=0, default=0.0)
    glucides: float = Field(ge=0, default=0.0)
    lipides: float = Field(ge=0, default=0.0)
    tags: list[str] = Field(default_factory=list)


class RecetteUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=200)
    heure_conseillee: Optional[time] = None
    kcal_total: Optional[float] = Field(default=None, ge=0)
    proteines: Optional[float] = Field(default=None, ge=0)
    glucides: Optional[float] = Field(default=None, ge=0)
    lipides: Optional[float] = Field(default=None, ge=0)
    tags: Optional[list[str]] = None


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


class RecetteIngredientCreate(BaseModel):
    recette_id: str
    ingredient_id: str
    poids_requis: float = Field(gt=0)
    unite: Unite


class RecetteIngredientUpdate(BaseModel):
    poids_requis: Optional[float] = Field(default=None, gt=0)
    unite: Optional[Unite] = None


class RecetteIngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recette_id: str
    ingredient_id: str
    poids_requis: float
    unite: str
