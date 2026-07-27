from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_profil_owner
from backend.models.profil import Profil
from backend.schemas.notification_pref import (
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
)
from backend.services import notification_pref_service, notification_preview_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/{profil_id}/preferences", response_model=NotificationPreferenceOut)
def get_preferences(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return notification_pref_service.get_or_create(db, profil.id)


@router.put("/{profil_id}/preferences", response_model=NotificationPreferenceOut)
def update_preferences(
    payload: NotificationPreferenceUpdate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return notification_pref_service.update_prefs(db, profil.id, payload)


@router.get("/{profil_id}/preview")
def preview_notifications(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    """Suggestions de payloads (péremption avec noms + hint ce soir)."""
    return notification_preview_service.build_preview(db, profil.id)
