from pydantic import BaseModel, ConfigDict


class NotificationPreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    peremption: bool
    ce_soir: bool
    resume_dimanche: bool
    enabled: bool


class NotificationPreferenceUpdate(BaseModel):
    peremption: bool | None = None
    ce_soir: bool | None = None
    resume_dimanche: bool | None = None
    enabled: bool | None = None
