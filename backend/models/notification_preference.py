import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.profil import Profil


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profil_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profils.id"), unique=True, nullable=False
    )
    peremption: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ce_soir: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    resume_dimanche: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    profil: Mapped["Profil"] = relationship(back_populates="notification_preference")
