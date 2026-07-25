import uuid
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.profil import Profil


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    date_naissance: Mapped[date] = mapped_column(Date, nullable=False)
    api_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex
    )

    profil: Mapped[Optional["Profil"]] = relationship(back_populates="utilisateur", uselist=False)
