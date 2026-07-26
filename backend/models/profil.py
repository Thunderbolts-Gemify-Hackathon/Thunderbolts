import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.agent_action import AgentAction
    from backend.models.depense import Depense
    from backend.models.favori_recette import FavoriRecette
    from backend.models.foyer import Foyer
    from backend.models.foyer_memory import FoyerMemory
    from backend.models.itineraire import Itineraire
    from backend.models.liste_course_item import ListeCourseItem
    from backend.models.localisation import Localisation
    from backend.models.notification_preference import NotificationPreference
    from backend.models.planning import Planning
    from backend.models.preferences import Preferences
    from backend.models.price_report import PriceReport
    from backend.models.recette import Recette
    from backend.models.repas_feedback import RepasFeedback
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
    depenses: Mapped[list["Depense"]] = relationship(back_populates="profil")
    liste_course_items: Mapped[list["ListeCourseItem"]] = relationship(
        back_populates="profil"
    )
    favoris_recettes: Mapped[list["FavoriRecette"]] = relationship(back_populates="profil")
    notification_preference: Mapped[Optional["NotificationPreference"]] = relationship(
        back_populates="profil", uselist=False
    )
    foyer_memories: Mapped[list["FoyerMemory"]] = relationship(back_populates="profil")
    agent_actions: Mapped[list["AgentAction"]] = relationship(back_populates="profil")
    price_reports: Mapped[list["PriceReport"]] = relationship(back_populates="profil")
    recettes_creees: Mapped[list["Recette"]] = relationship(back_populates="owner")
    repas_feedbacks: Mapped[list["RepasFeedback"]] = relationship(back_populates="profil")
