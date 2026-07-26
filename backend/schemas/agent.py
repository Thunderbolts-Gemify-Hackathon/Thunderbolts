from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    type_action: str
    payload_json: str
    statut: str
    message: Optional[str] = None
    created_at: datetime


class AgentDigestOut(BaseModel):
    alertes_stock: list[dict[str, Any]] = Field(default_factory=list)
    budget: dict[str, Any] = Field(default_factory=dict)
    ce_soir: Optional[dict[str, Any]] = None
    actions: list[AgentActionOut] = Field(default_factory=list)
    memories: list[dict[str, Any]] = Field(default_factory=list)
    resume: str = ""


class AgentActionRespondRequest(BaseModel):
    decision: Literal["accepte", "refuse"]
