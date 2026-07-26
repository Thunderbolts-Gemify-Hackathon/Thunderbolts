from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.models.agent_action import AgentAction
from backend.models.foyer_memory import FoyerMemory
from backend.models.liste_course_item import ListeCourseItem
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette
from backend.services import budget_service, repas_suggestion_service, stock_alerts


def top_memories(db: Session, profil_id: str, limit: int = 5) -> list[FoyerMemory]:
    return (
        db.query(FoyerMemory)
        .filter(FoyerMemory.profil_id == profil_id)
        .order_by(FoyerMemory.importance.desc(), FoyerMemory.created_at.desc())
        .limit(limit)
        .all()
    )


def upsert_memory(
    db: Session,
    profil_id: str,
    cle: str,
    contenu: str,
    *,
    importance: float = 1.0,
) -> FoyerMemory:
    mem = (
        db.query(FoyerMemory)
        .filter(FoyerMemory.profil_id == profil_id, FoyerMemory.cle == cle)
        .first()
    )
    if mem:
        mem.contenu = contenu
        mem.importance = importance
        mem.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    else:
        mem = FoyerMemory(
            profil_id=profil_id, cle=cle, contenu=contenu, importance=importance
        )
        db.add(mem)
    db.commit()
    db.refresh(mem)
    return mem


def build_digest(db: Session, profil_id: str) -> dict[str, Any]:
    alertes = stock_alerts.check_expiry(db, profil_id, jours=7)
    alertes_payload = [
        {
            "ingredient_nom": a.ingredient.nom if a.ingredient else "?",
            "date_peremption": str(a.date_peremption) if a.date_peremption else None,
            "quantite_disponible": a.quantite_disponible,
            "unite": a.unite,
        }
        for a in alertes
    ]

    try:
        budget = budget_service.get_budget_summary(db, profil_id)
    except Exception:  # noqa: BLE001
        budget = {"montant_restant": 0, "montant": 0}

    try:
        ce_soir = repas_suggestion_service.suggestion_ce_soir(db, profil_id)
        ce_soir_out = {
            "recette_id": ce_soir["recette"].id if ce_soir.get("recette") else None,
            "nom": ce_soir["recette"].nom if ce_soir.get("recette") else None,
            "message": ce_soir.get("message"),
            "cout_estime": ce_soir.get("cout_estime"),
        }
    except Exception:  # noqa: BLE001
        ce_soir_out = None

    # Propose actions si alertes ou budget bas
    actions = (
        db.query(AgentAction)
        .filter(AgentAction.profil_id == profil_id, AgentAction.statut == "propose")
        .order_by(AgentAction.created_at.desc())
        .limit(10)
        .all()
    )
    if not actions and alertes_payload:
        first = alertes_payload[0]
        action = AgentAction(
            profil_id=profil_id,
            type_action="add_shopping_items",
            payload_json=json.dumps(
                {
                    "items": [
                        {
                            "label": first["ingredient_nom"],
                            "quantite": 1,
                            "unite": first.get("unite") or "u",
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            message=f"Ajouter {first['ingredient_nom']} à la liste (péremption proche).",
            statut="propose",
        )
        db.add(action)
        db.commit()
        db.refresh(action)
        actions = [action]

    if ce_soir_out and ce_soir_out.get("recette_id"):
        has_swap = any(a.type_action == "swap_meal" for a in actions)
        if not has_swap and alertes_payload:
            action = AgentAction(
                profil_id=profil_id,
                type_action="swap_meal",
                payload_json=json.dumps(
                    {"recette_id": ce_soir_out["recette_id"], "raison": "utiliser stock"},
                    ensure_ascii=False,
                ),
                message=f"Cuisiner ce soir : {ce_soir_out.get('nom')}",
                statut="propose",
            )
            db.add(action)
            db.commit()
            db.refresh(action)
            actions = [action] + list(actions)

    memories = top_memories(db, profil_id)
    mem_payload = [
        {"cle": m.cle, "contenu": m.contenu, "importance": m.importance} for m in memories
    ]

    parts = []
    if alertes_payload:
        parts.append(f"{len(alertes_payload)} alerte(s) péremption")
    if isinstance(budget, dict) and budget.get("montant_restant") is not None:
        parts.append(f"budget restant {budget.get('montant_restant')} Ar")
    if ce_soir_out and ce_soir_out.get("nom"):
        parts.append(f"ce soir : {ce_soir_out['nom']}")
    resume = " · ".join(parts) if parts else "Rien d'urgent pour le moment."

    return {
        "alertes_stock": alertes_payload,
        "budget": budget if isinstance(budget, dict) else {},
        "ce_soir": ce_soir_out,
        "actions": actions,
        "memories": mem_payload,
        "resume": resume,
    }


def respond_action(
    db: Session, profil_id: str, action_id: str, decision: str
) -> AgentAction:
    action = (
        db.query(AgentAction)
        .filter(AgentAction.id == action_id, AgentAction.profil_id == profil_id)
        .first()
    )
    if not action:
        raise ValueError("Action introuvable")
    if action.statut != "propose":
        raise ValueError("Action déjà traitée")

    action.statut = decision
    action.responded_at = datetime.now(timezone.utc).replace(tzinfo=None)

    if decision == "accepte":
        _apply_action(db, profil_id, action)

    db.commit()
    db.refresh(action)
    return action


def _apply_action(db: Session, profil_id: str, action: AgentAction) -> None:
    try:
        payload = json.loads(action.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}

    if action.type_action == "add_shopping_items":
        for raw in payload.get("items") or []:
            db.add(
                ListeCourseItem(
                    profil_id=profil_id,
                    label=str(raw.get("label") or "article"),
                    quantite=float(raw.get("quantite") or 1),
                    unite=str(raw.get("unite") or "u"),
                    ingredient_id=raw.get("ingredient_id"),
                    custom=True,
                )
            )
        upsert_memory(
            db,
            profil_id,
            "courses_auto",
            "Accepte les suggestions de courses automatiques",
            importance=1.2,
        )
    elif action.type_action == "swap_meal":
        recette_id = payload.get("recette_id")
        if recette_id and db.get(Recette, recette_id):
            planning = (
                db.query(Planning)
                .filter(Planning.profil_id == profil_id)
                .order_by(Planning.date_debut.desc())
                .first()
            )
            if planning:
                repas = (
                    db.query(RepasPlanifie)
                    .filter(
                        RepasPlanifie.planning_id == planning.id,
                        RepasPlanifie.type_repas == "diner",
                    )
                    .order_by(RepasPlanifie.jour.desc())
                    .first()
                )
                if repas:
                    repas.recette_id = recette_id
        upsert_memory(
            db,
            profil_id,
            "swap_meal",
            f"Préférence swap vers recette {recette_id}",
            importance=1.0,
        )


def add_shopping_items_tool(
    db: Session, profil_id: str, items: list[dict[str, Any]]
) -> dict:
    created = []
    for raw in items:
        item = ListeCourseItem(
            profil_id=profil_id,
            label=str(raw.get("label") or raw.get("ingredient_nom") or "article"),
            quantite=float(raw.get("quantite") or 1),
            unite=str(raw.get("unite") or "u"),
            custom=True,
        )
        db.add(item)
        created.append(item.label)
    db.commit()
    return {"ajoutes": created, "count": len(created)}


def swap_meal_tool(
    db: Session, profil_id: str, recette_id: str, jour: str | None = None
) -> dict:
    if not db.get(Recette, recette_id):
        raise ValueError("Recette introuvable")
    planning = (
        db.query(Planning)
        .filter(Planning.profil_id == profil_id)
        .order_by(Planning.date_debut.desc())
        .first()
    )
    if not planning:
        raise ValueError("Aucun planning")
    q = db.query(RepasPlanifie).filter(RepasPlanifie.planning_id == planning.id)
    if jour:
        q = q.filter(RepasPlanifie.jour == jour)
    else:
        q = q.filter(RepasPlanifie.type_repas == "diner")
    repas = q.order_by(RepasPlanifie.jour.desc()).first()
    if not repas:
        raise ValueError("Aucun repas à remplacer")
    old = repas.recette_id
    repas.recette_id = recette_id
    db.commit()
    return {"ancien_recette_id": old, "nouveau_recette_id": recette_id, "repas_id": repas.id}
