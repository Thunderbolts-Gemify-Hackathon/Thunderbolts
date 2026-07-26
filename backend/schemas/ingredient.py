from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Unite = Literal["g", "ml", "kg", "l", "unite"]
CategorieIngredient = Literal[
    "féculent", "protéine", "légume", "épice", "condiment", "autre"
]


class IngredientCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    unite_defaut: Unite
    categorie: CategorieIngredient = "autre"
    conservation_jours: Optional[int] = Field(default=None, ge=0)
    saison: Optional[list[str]] = None
    prix_moyen_reference: Optional[float] = Field(default=None, ge=0)


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nom: str
    unite_defaut: str
    categorie: str = "autre"
    conservation_jours: Optional[int] = None
    saison: Optional[list[str]] = None
    prix_moyen_reference: Optional[float] = None
