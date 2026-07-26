from typing import Optional

from pydantic import BaseModel, Field


class PanierItemIn(BaseModel):
    ingredient_nom: str
    quantite: float = Field(gt=0)
    unite: str = "g"


class PanierCheckRequest(BaseModel):
    items: list[PanierItemIn] = Field(min_length=1)
    budget: float = Field(gt=0)
    quartier: Optional[str] = None


class PanierSwapSuggestion(BaseModel):
    ingredient_nom: str
    alternative: str
    economie_estimee: float
    raison: str


class PanierCheckResponse(BaseModel):
    cout_estime: float
    budget: float
    ecart: float
    statut: str  # sous_budget | au_budget | over_budget
    swaps: list[PanierSwapSuggestion] = Field(default_factory=list)
