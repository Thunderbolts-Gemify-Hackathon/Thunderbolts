"""Endpoints IA : génération de planning via Gemma (+ stretch : suggestion de remède)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.etat_du_jour import EtatDuJour
from backend.models.foyer import Foyer
from backend.schemas.gemma import ChatRequest, ChatResponse, RemedeResponse
from backend.schemas.gemma import ChatRequest, ChatResponse, ChatVocalResponse, RemedeResponse
from backend.schemas.planning import PeriodePlanning, PlanningOut
from backend.services import onboarding_suite, planning_generation_service
from backend.services.gemma_agent import parse_json_object, run_tool_loop
from backend.services.gemma_client import GemmaClient
from backend.services.prompts import VOCAL_INSTRUCTION, build_system_prompt

router = APIRouter(prefix="/ia", tags=["ia"])

MAX_AUDIO_BYTES = 15 * 1024 * 1024

@router.post("/{profil_id}/generer-planning", response_model=PlanningOut, status_code=201)
def generer_planning(
    profil_id: str,
    periode: PeriodePlanning = Query("semaine"),
    date_debut: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
):
    try:
        return planning_generation_service.generer_planning(db, profil_id, periode, date_debut)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{profil_id}/chat", response_model=ChatResponse)
def chat(profil_id: str, payload: ChatRequest, db: Session = Depends(get_db)):
    """Chat libre avec Gemma sur le profil (mêmes règles/outils que la génération de planning)."""
    profil_complet = onboarding_suite.get_profil_complet(db, profil_id)

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
def suggestion_remede(profil_id: str, db: Session = Depends(get_db)):
    """STRETCH : suggère un remède local simple si le foyer est 'un_peu_malade' (pas de tool calling)."""
    profil_complet = onboarding_suite.get_profil_complet(db, profil_id)

    foyer = db.query(Foyer).filter(Foyer.profil_id == profil_id).first()
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

@router.post("/{profil_id}/chat-vocal", response_model=ChatVocalResponse)
async def chat_vocal(
    profil_id: str,
    audio: UploadFile = File(...),
    historique: str = Form("[]"),
    db: Session = Depends(get_db),
):
    """Chat vocal : l'utilisateur envoie un enregistrement audio, Gemma le transcrit et
    y répond directement (sans tool-calling — voir /chat pour l'échange texte outillé)."""
    profil_complet = onboarding_suite.get_profil_complet(db, profil_id)

    try:
        historique_data = json.loads(historique)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="historique doit être un JSON valide") from None

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="Fichier audio vide")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Fichier audio trop volumineux")

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(profil_complet) + "\n\n" + VOCAL_INSTRUCTION,
        }
    ]
    messages += [
        {"role": m["role"], "content": m["content"]}
        for m in historique_data
        if isinstance(m, dict) and m.get("role") and m.get("content")
    ]
    messages.append({"role": "user", "content": "[Message vocal joint en pièce jointe audio]"})

    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
    mime_type = audio.content_type or "audio/m4a"

    try:
        result = GemmaClient().chat_audio(messages, audio_b64, mime_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    content = result["message"].get("content") or ""
    parsed = parse_json_object(content)
    if parsed and parsed.get("reponse"):
        return ChatVocalResponse(
            transcription=str(parsed.get("transcription") or ""),
            reponse=str(parsed["reponse"]),
        )
    return ChatVocalResponse(transcription="", reponse=content)
