import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.profil import Profil
    from backend.models.recette import Recette


class Planning(Base):
    __tablename__ = "plannings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profil_id: Mapped[str] = mapped_column(String(36), ForeignKey("profils.id"), nullable=False)
    periode: Mapped[str] = mapped_column(String(20), nullable=False)
    date_debut: Mapped[date] = mapped_column(Date, nullable=False)

    profil: Mapped["Profil"] = relationship(back_populates="plannings")
    repas: Mapped[list["RepasPlanifie"]] = relationship(
        back_populates="planning", cascade="all, delete-orphan"
    )


class RepasPlanifie(Base):
    __tablename__ = "repas_planifies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    planning_id: Mapped[str] = mapped_column(String(36), ForeignKey("plannings.id"), nullable=False)
    recette_id: Mapped[str] = mapped_column(String(36), ForeignKey("recettes.id"), nullable=False)
    jour: Mapped[date] = mapped_column(Date, nullable=False)
    type_repas: Mapped[str] = mapped_column(String(30), nullable=False)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="planifie")

    planning: Mapped["Planning"] = relationship(back_populates="repas")
    recette: Mapped["Recette"] = relationship(back_populates="repas_planifies")
