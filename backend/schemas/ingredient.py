from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


Unite = Literal["g", "ml", "kg", "l", "unite"]


class IngredientCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    unite_defaut: Unite


class IngredientUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=120)
    unite_defaut: Optional[Unite] = None


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nom: str
    unite_defaut: str
