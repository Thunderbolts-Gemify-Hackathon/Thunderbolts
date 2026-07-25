from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Unite = Literal["g", "ml", "kg", "l", "unite"]


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nom: str
    unite_defaut: str
