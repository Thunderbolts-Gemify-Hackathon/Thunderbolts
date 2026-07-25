from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MembreFoyerCreate(BaseModel):
    prenom: Optional[str] = None
    lien: Optional[str] = None
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


class FoyerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    nombre_personnes: int
    membres: list[MembreFoyerOut] = Field(default_factory=list)
