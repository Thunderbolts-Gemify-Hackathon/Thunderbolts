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
from backend.schemas.gemma import (
    ChatRequest,
    ChatResponse,
    DirectiveCoursesRequest,
    DirectiveCoursesResponse,
    EtapesRecetteResponse,
    RemedeResponse,
    SuggestionRepasRequest,
    SuggestionRepasResponse,
)
from backend.schemas.planning import PeriodePlanning, PlanningOut
from backend.services import (
    onboarding_suite,
    planning_generation_service,
    recette_etapes_service,
    repas_suggestion_service,
)
from backend.schemas.agent import AgentActionOut, AgentActionRespondRequest, AgentDigestOut
from backend.schemas.anti_gaspi import AntiGaspiOut
from backend.schemas.feedback import RepasFeedbackCreate, RepasFeedbackOut
from backend.services import anti_gaspi_service, feedback_service, foyer_agent_service
from backend.services.directive_courses_service import build_directive_courses
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
    memories = [
        {"cle": m.cle, "contenu": m.contenu, "importance": m.importance}
        for m in foyer_agent_service.top_memories(db, profil.id)
    ]

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(
                profil_complet, voice=payload.voice, memories=memories
            ),
        }
    ]
    messages += [{"role": m.role, "content": m.content} for m in payload.historique]
    messages.append({"role": "user", "content": payload.message})

    tool_calls: list[dict] = []
    try:
        reponse = run_tool_loop(
            db, GemmaClient(), messages, profil_id=profil.id, trace=tool_calls
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(reponse=reponse, tool_calls=tool_calls)


@router.post(
    "/{profil_id}/directive-courses",
    response_model=DirectiveCoursesResponse,
)
def directive_courses(
    payload: DirectiveCoursesRequest,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    """Directive courses structurée (seed KaliTao) pour lecture vocale."""
    return build_directive_courses(
        db,
        profil.id,
        ingredient_id=payload.ingredient_id,
        ingredient_nom=payload.ingredient_nom,
        rayon_km=payload.rayon_km,
    )


@router.post("/{profil_id}/suggestion-repas", response_model=SuggestionRepasResponse)
def suggestion_repas(
    payload: SuggestionRepasRequest,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    """"Je veux manger quelque chose" : choix parmi les recettes du creneau, favorisant
    le stock actuel. Le choix final vient toujours des candidats calcules, jamais de Gemma seul."""
    try:
        resultat = repas_suggestion_service.suggerer_repas(
            db, profil.id, payload.type_repas, payload.duree_max_minutes
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return resultat


@router.get("/{profil_id}/ce-soir")
def ce_soir(
    profil: Profil = Depends(require_profil_owner),
    mode: str | None = Query(default=None, description="stock|rapide"),
    duree_max_minutes: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    """Card dashboard « Ce soir » : suggestion déterministe sans Gemma."""
    try:
        return repas_suggestion_service.suggestion_ce_soir(
            db, profil.id, mode=mode, duree_max_minutes=duree_max_minutes
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{profil_id}/recette/{recette_id}/etapes", response_model=EtapesRecetteResponse)
def etapes_recette(
    recette_id: str,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    """Explique une recette existante en étapes courtes (Gemma, sans outils)."""
    try:
        etapes = recette_etapes_service.generer_etapes(db, recette_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return EtapesRecetteResponse(etapes=etapes)


@router.get("/{profil_id}/agent/digest", response_model=AgentDigestOut)
def agent_digest(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    data = foyer_agent_service.build_digest(db, profil.id)
    return AgentDigestOut(
        alertes_stock=data["alertes_stock"],
        budget=data["budget"],
        ce_soir=data["ce_soir"],
        actions=[AgentActionOut.model_validate(a) for a in data["actions"]],
        memories=data["memories"],
        resume=data["resume"],
    )


@router.post(
    "/{profil_id}/agent/actions/{action_id}/respond",
    response_model=AgentActionOut,
)
def agent_respond(
    action_id: str,
    payload: AgentActionRespondRequest,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    try:
        return foyer_agent_service.respond_action(
            db, profil.id, action_id, payload.decision
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{profil_id}/anti-gaspi", response_model=AntiGaspiOut)
def anti_gaspi(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return anti_gaspi_service.compute_anti_gaspi(db, profil.id)


@router.post(
    "/{profil_id}/feedback",
    response_model=RepasFeedbackOut,
    status_code=201,
)
def repas_feedback(
    payload: RepasFeedbackCreate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    try:
        return feedback_service.upsert_feedback(db, profil.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
