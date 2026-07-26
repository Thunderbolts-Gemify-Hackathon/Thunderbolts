import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.profil import Profil
    from backend.models.recette import Recette


class FavoriRecette(Base):
    __tablename__ = "favoris_recettes"
    __table_args__ = (UniqueConstraint("profil_id", "recette_id", name="uq_favori_profil_recette"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profil_id: Mapped[str] = mapped_column(String(36), ForeignKey("profils.id"), nullable=False)
    recette_id: Mapped[str] = mapped_column(String(36), ForeignKey("recettes.id"), nullable=False)

    profil: Mapped["Profil"] = relationship(back_populates="favoris_recettes")
    recette: Mapped["Recette"] = relationship()
