from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

LienMembre = Literal["conjoint", "enfant", "parent", "autre"]


class MembreFoyerCreate(BaseModel):
    prenom: Optional[str] = None
    lien: Optional[LienMembre] = None
    age_approx: int = Field(ge=0, le=120)
    regime_aligne: bool = True
    restrictions: Optional[str] = None


class MembreFoyerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    foyer_id: str
    prenom: Optional[str] = None
    lien: Optional[str] = None
    age_approx: int
    regime_aligne: bool
    restrictions: Optional[str] = None


class FoyerCreate(BaseModel):
    nombre_personnes: int = Field(ge=1)
    membres: list[MembreFoyerCreate] = Field(default_factory=list)


class FoyerUpdate(BaseModel):
    nombre_personnes: Optional[int] = Field(default=None, ge=1)
    membres: Optional[list[MembreFoyerCreate]] = None


class FoyerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    nombre_personnes: int
    membres: list[MembreFoyerOut] = Field(default_factory=list)
    planning_invalide: bool = False
