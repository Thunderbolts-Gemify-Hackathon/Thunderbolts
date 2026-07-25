from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UtilisateurCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    date_naissance: date

    @field_validator("date_naissance")
    @classmethod
    def date_naissance_dans_le_passe(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("La date de naissance doit être dans le passé")
        return v


class UtilisateurOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nom: str
    prenom: str
    email: str
    date_naissance: date
    api_token: str
