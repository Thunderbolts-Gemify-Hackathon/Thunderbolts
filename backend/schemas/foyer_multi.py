from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FoyerInviteCreate(BaseModel):
    email: Optional[str] = None
    role: str = Field(default="invite", max_length=20)


class FoyerMembreLienOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    utilisateur_id: Optional[str] = None
    foyer_id: str
    role: str
    invite_token: Optional[str] = None
    created_at: datetime


class FoyerInviteOut(BaseModel):
    lien: FoyerMembreLienOut
    invite_url: str
