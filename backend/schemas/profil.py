from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

NiveauActivite = Literal["sedentaire", "leger", "modere", "actif", "tres_actif"]
Objectif = Literal["perte_poids", "maintien", "prise_masse"]


class ProfilCreate(BaseModel):
    utilisateur_id: str
    age: Optional[int] = Field(default=None, ge=1, le=120)
    sexe: str
    poids: float = Field(gt=0)
    taille: float = Field(gt=0)
    niveau_activite: NiveauActivite
    objectif: Objectif
    condition_sante: Optional[str] = None


class ProfilOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    utilisateur_id: Optional[str] = None
    age: int
    sexe: str
    poids: float
    taille: float
    niveau_activite: str
    objectif: str
    condition_sante: Optional[str] = None
    imc: Optional[float] = None
    besoin_calorique: Optional[float] = None
