import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.profil import Profil
    from backend.models.recette import Recette


class RepasFeedback(Base):
    __tablename__ = "repas_feedbacks"
    __table_args__ = (
        UniqueConstraint("profil_id", "recette_id", name="uq_feedback_profil_recette"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profil_id: Mapped[str] = mapped_column(String(36), ForeignKey("profils.id"), nullable=False)
    recette_id: Mapped[str] = mapped_column(String(36), ForeignKey("recettes.id"), nullable=False)
    note: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # -1 dislike, 1 like
    commentaire: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    profil: Mapped["Profil"] = relationship(back_populates="repas_feedbacks")
    recette: Mapped["Recette"] = relationship()
