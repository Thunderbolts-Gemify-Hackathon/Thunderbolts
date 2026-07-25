import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.point_de_vente import PointDeVente
    from backend.models.profil import Profil


class Itineraire(Base):
    __tablename__ = "itineraires"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    point_de_vente_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("points_de_vente.id"), nullable=False
    )
    profil_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profils.id"), nullable=True
    )
    distance: Mapped[float] = mapped_column(Float, nullable=False)
    niveau_securite: Mapped[str] = mapped_column(String(20), nullable=False)
    mode_deplacement: Mapped[str] = mapped_column(String(20), nullable=False)

    point_de_vente: Mapped["PointDeVente"] = relationship(back_populates="itineraires")
    profil: Mapped[Optional["Profil"]] = relationship(back_populates="itineraires")
