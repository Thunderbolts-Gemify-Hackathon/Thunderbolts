import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.foyer import Foyer
    from backend.models.itineraire import Itineraire
    from backend.models.localisation import Localisation
    from backend.models.planning import Planning
    from backend.models.preferences import Preferences
    from backend.models.stock import Stock
    from backend.models.utilisateur import Utilisateur


class Profil(Base):
    __tablename__ = "profils"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    utilisateur_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("utilisateurs.id"), unique=True, nullable=True
    )
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sexe: Mapped[str] = mapped_column(String(20), nullable=False)
    poids: Mapped[float] = mapped_column(Float, nullable=False)
    taille: Mapped[float] = mapped_column(Float, nullable=False)
    niveau_activite: Mapped[str] = mapped_column(String(30), nullable=False)
    objectif: Mapped[str] = mapped_column(String(30), nullable=False)
    condition_sante: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    utilisateur: Mapped[Optional["Utilisateur"]] = relationship(back_populates="profil")
    foyer: Mapped[Optional["Foyer"]] = relationship(back_populates="profil", uselist=False)
    preferences: Mapped[Optional["Preferences"]] = relationship(
        back_populates="profil", uselist=False
    )
    localisation: Mapped[Optional["Localisation"]] = relationship(
        back_populates="profil", uselist=False
    )
    stock: Mapped[Optional["Stock"]] = relationship(back_populates="profil", uselist=False)
    plannings: Mapped[list["Planning"]] = relationship(back_populates="profil")
    itineraires: Mapped[list["Itineraire"]] = relationship(back_populates="profil")
