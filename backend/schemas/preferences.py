from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SeveriteAllergie = Literal["legere", "moderee", "severe"]
RegimeSpecifique = Literal[
    "aucun", "vegetarien", "vegan", "sans_porc", "halal", "sans_gluten"
]


class PreferencesCreate(BaseModel):
    tabous: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    severite_allergie: Optional[SeveriteAllergie] = None
    regime_specifique: Optional[RegimeSpecifique] = None
    aliments_aimes: list[str] = Field(default_factory=list)
    aliments_detestes: list[str] = Field(default_factory=list)


class PreferencesUpdate(BaseModel):
    tabous: Optional[list[str]] = None
    allergies: Optional[list[str]] = None
    severite_allergie: Optional[SeveriteAllergie] = None
    regime_specifique: Optional[RegimeSpecifique] = None
    aliments_aimes: Optional[list[str]] = None
    aliments_detestes: Optional[list[str]] = None


class PreferencesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    tabous: list[str]
    allergies: list[str]
    severite_allergie: Optional[str] = None
    regime_specifique: Optional[str] = None
    aliments_aimes: list[str] = Field(default_factory=list)
    aliments_detestes: list[str]
    planning_invalide: bool = False
