import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.profil import Profil


class Localisation(Base):
    __tablename__ = "localisations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profil_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profils.id"), unique=True, nullable=False
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    quartier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    saison: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    profil: Mapped["Profil"] = relationship(back_populates="localisation")
