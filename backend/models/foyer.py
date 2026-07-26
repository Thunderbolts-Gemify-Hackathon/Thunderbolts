import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.etat_du_jour import EtatDuJour
    from backend.models.profil import Profil


class Foyer(Base):
    __tablename__ = "foyers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profil_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profils.id"), unique=True, nullable=False
    )
    nombre_personnes: Mapped[int] = mapped_column(Integer, nullable=False)

    profil: Mapped["Profil"] = relationship(back_populates="foyer")
    membres: Mapped[list["MembreFoyer"]] = relationship(
        back_populates="foyer", cascade="all, delete-orphan"
    )
    etats_du_jour: Mapped[list["EtatDuJour"]] = relationship(
        back_populates="foyer", cascade="all, delete-orphan"
    )


class MembreFoyer(Base):
    __tablename__ = "membres_foyer"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    foyer_id: Mapped[str] = mapped_column(String(36), ForeignKey("foyers.id"), nullable=False)
    prenom: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lien: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    age_approx: Mapped[int] = mapped_column(Integer, nullable=False)
    regime_aligne: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    restrictions: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    foyer: Mapped["Foyer"] = relationship(back_populates="membres")
