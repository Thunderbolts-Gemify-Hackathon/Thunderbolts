from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.stock import IngredientStockOut

SourceDepense = Literal["repas", "courses", "manuel"]


class DepenseCreate(BaseModel):
    montant: float = Field(gt=0)
    source: SourceDepense = "manuel"
    label: Optional[str] = Field(default=None, max_length=200)


class DepenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    montant: float
    source: str
    label: Optional[str] = None
    created_at: datetime


class ApprovisionnementItem(BaseModel):
    ingredient_id: str
    quantite: float = Field(gt=0)
    unite: str = "g"
    prix: Optional[float] = Field(default=None, ge=0)


class ApprovisionnementRequest(BaseModel):
    items: list[ApprovisionnementItem] = Field(min_length=1)
    label: Optional[str] = "Courses"


class ApprovisionnementResponse(BaseModel):
    stock: list[IngredientStockOut]
    depense: Optional[DepenseOut] = None
    montant_restant: float
