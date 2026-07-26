from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.notification_preference import NotificationPreference
from backend.schemas.notification_pref import NotificationPreferenceUpdate


def get_or_create(db: Session, profil_id: str) -> NotificationPreference:
    pref = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.profil_id == profil_id)
        .first()
    )
    if pref:
        return pref
    pref = NotificationPreference(profil_id=profil_id)
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


def update_prefs(
    db: Session, profil_id: str, payload: NotificationPreferenceUpdate
) -> NotificationPreference:
    pref = get_or_create(db, profil_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(pref, key, value)
    db.commit()
    db.refresh(pref)
    return pref
