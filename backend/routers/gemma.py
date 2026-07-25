"""Endpoints IA : génération de planning via Gemma (+ stretch : suggestion de remède)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_profil_owner
from backend.models.etat_du_jour import EtatDuJour
from backend.models.foyer import Foyer
from backend.models.profil import Profil
from backend.schemas.gemma import ChatRequest, ChatResponse, RemedeResponse
from backend.schemas.planning import PeriodePlanning, PlanningOut
from backend.services import onboarding_suite, planning_generation_service
from backend.services.gemma_agent import run_tool_loop
from backend.services.gemma_client import GemmaClient
from backend.services.prompts import build_system_prompt

router = APIRouter(prefix="/ia", tags=["ia"])


@router.post("/{profil_id}/generer-planning", response_model=PlanningOut, status_code=201)
def generer_planning(
    profil: Profil = Depends(require_profil_owner),
    periode: PeriodePlanning = Query("semaine"),
    date_debut: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
):
    try:
        return planning_generation_service.generer_planning(
            db, profil.id, periode, date_debut
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{profil_id}/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    """Chat libre avec Gemma sur le profil (mêmes règles/outils que la génération de planning)."""
    profil_complet = onboarding_suite.get_profil_complet(db, profil.id)

    messages = [{"role": "system", "content": build_system_prompt(profil_complet)}]
    messages += [{"role": m.role, "content": m.content} for m in payload.historique]
    messages.append({"role": "user", "content": payload.message})

    tool_calls: list[dict] = []
    try:
        reponse = run_tool_loop(db, GemmaClient(), messages, trace=tool_calls)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(reponse=reponse, tool_calls=tool_calls)


@router.post("/{profil_id}/suggestion-remede", response_model=RemedeResponse)
def suggestion_remede(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    """STRETCH : suggère un remède local simple si le foyer est 'un_peu_malade'."""
    profil_complet = onboarding_suite.get_profil_complet(db, profil.id)

    foyer = db.query(Foyer).filter(Foyer.profil_id == profil.id).first()
    if not foyer:
        raise HTTPException(status_code=404, detail="Foyer introuvable pour ce profil")

    etat = (
        db.query(EtatDuJour)
        .filter(EtatDuJour.foyer_id == foyer.id, EtatDuJour.type == "un_peu_malade")
        .order_by(EtatDuJour.date.desc())
        .first()
    )
    if not etat:
        raise HTTPException(
            status_code=404, detail="Aucun état 'un_peu_malade' enregistré pour ce foyer"
        )

    messages = [
        {"role": "system", "content": build_system_prompt(profil_complet)},
        {
            "role": "user",
            "content": (
                "Le foyer se sent un peu malade aujourd'hui. Suggère un remède local simple, "
                "sûr et à base d'ingrédients courants à Madagascar, en respectant strictement "
                "les allergies et tabous du profil. Réponds en texte naturel, sans appel d'outil."
            ),
        },
    ]
    reponse = GemmaClient().chat(messages)["message"]
    return {"remede": reponse.get("content") or ""}
