from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ListeCourseItemCreate(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    ingredient_id: Optional[str] = None
    quantite: float = Field(default=1.0, gt=0)
    unite: str = Field(default="u", max_length=20)
    prix_estime: Optional[float] = Field(default=None, ge=0)
    custom: bool = True


class ListeCourseItemUpdate(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1, max_length=200)
    quantite: Optional[float] = Field(default=None, gt=0)
    unite: Optional[str] = Field(default=None, max_length=20)
    prix_estime: Optional[float] = Field(default=None, ge=0)
    coche: Optional[bool] = None


class ListeCourseItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    ingredient_id: Optional[str] = None
    label: str
    quantite: float
    unite: str
    prix_estime: Optional[float] = None
    coche: bool
    custom: bool
    done: bool


class CoursesTerminerRequest(BaseModel):
    item_ids: list[str] = Field(default_factory=list)
    label: Optional[str] = "Courses"


class CoursesTerminerResponse(BaseModel):
    items_termines: int
    stock_approvisionne: int
    montant_restant: float
