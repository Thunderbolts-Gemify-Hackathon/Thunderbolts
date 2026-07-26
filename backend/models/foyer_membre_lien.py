import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.foyer import Foyer
    from backend.models.utilisateur import Utilisateur


class FoyerMembreLien(Base):
    """Lien multi-utilisateurs vers un foyer (owner / membre / invite)."""

    __tablename__ = "foyer_membre_liens"
    __table_args__ = (
        UniqueConstraint("utilisateur_id", "foyer_id", name="uq_foyer_membre_utilisateur"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    utilisateur_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("utilisateurs.id"), nullable=True
    )
    foyer_id: Mapped[str] = mapped_column(String(36), ForeignKey("foyers.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="membre")
    # owner | membre | invite
    invite_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    utilisateur: Mapped["Utilisateur"] = relationship()
    foyer: Mapped["Foyer"] = relationship()
