from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RepasFeedbackCreate(BaseModel):
    recette_id: str
    note: int = Field(ge=-1, le=1)
    commentaire: Optional[str] = Field(default=None, max_length=500)


class RepasFeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    recette_id: str
    note: int
    commentaire: Optional[str] = None
    created_at: datetime
