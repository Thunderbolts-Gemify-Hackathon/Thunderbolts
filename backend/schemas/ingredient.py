from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

Unite = Literal["g", "ml", "kg", "l", "unite"]
CategorieIngredient = Literal[
    "féculent", "protéine", "légume", "épice", "condiment", "autre"
]


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nom: str
    unite_defaut: str
    categorie: str = "autre"
    conservation_jours: Optional[int] = None
    saison: Optional[list[str]] = None
    prix_moyen_reference: Optional[float] = None
