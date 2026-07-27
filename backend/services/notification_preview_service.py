"""Prévisualisation de notifications contextuelles (péremption + ce soir)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.services import notification_pref_service, repas_suggestion_service, stock_alerts


def build_preview(db: Session, profil_id: str) -> dict:
    prefs = notification_pref_service.get_or_create(db, profil_id)
    notifications: list[dict] = []

    if prefs.peremption:
        alertes = stock_alerts.check_expiry(db, profil_id, jours=3)
        noms = []
        for a in alertes[:5]:
            nom = None
            if getattr(a, "ingredient", None) is not None:
                nom = a.ingredient.nom
            elif hasattr(a, "ingredient_id"):
                nom = str(a.ingredient_id)[:8]
            if nom:
                noms.append(nom)
        if noms:
            notifications.append(
                {
                    "kind": "peremption",
                    "title": "Péremption",
                    "body": f"À utiliser bientôt : {', '.join(noms)}.",
                    "hour": 9,
                    "minute": 0,
                }
            )
        else:
            notifications.append(
                {
                    "kind": "peremption",
                    "title": "Péremption",
                    "body": "Vérifie les produits qui approchent de la date limite.",
                    "hour": 9,
                    "minute": 0,
                }
            )

    if prefs.ce_soir:
        body = "Une idée de repas t'attend sur le tableau de bord."
        try:
            suggestion = repas_suggestion_service.suggestion_ce_soir(db, profil_id)
            recette = suggestion.get("recette") if suggestion else None
            if recette is not None and getattr(recette, "nom", None):
                body = f"Ce soir : {recette.nom}."
            elif suggestion and suggestion.get("message"):
                body = str(suggestion["message"])
        except Exception:
            pass
        notifications.append(
            {
                "kind": "ce_soir",
                "title": "Ce soir sur KaliTao",
                "body": body,
                "hour": 17,
                "minute": 30,
            }
        )

    if prefs.resume_dimanche:
        notifications.append(
            {
                "kind": "resume_dimanche",
                "title": "Résumé dimanche",
                "body": "Budget, stock et anti-gaspi de la semaine.",
                "hour": 10,
                "minute": 0,
                "weekday": 1,
            }
        )

    return {
        "profil_id": profil_id,
        "enabled": prefs.enabled,
        "notifications": notifications if prefs.enabled else [],
    }
