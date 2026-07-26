"""Explication d'une recette en étapes, via un simple appel Gemma (sans outils).

Volontairement séparé de `run_tool_loop` / `/ia/{profil_id}/chat` : cette question
n'a besoin d'aucun outil (stock, marché, planning...), et sur un petit modèle local
(gemma2:2b) le laisser voir la liste complète des outils le fait parfois boucler
sans jamais produire de réponse finale (`RuntimeError`), ou répondre à côté.
Un appel direct, ciblé, est plus rapide et bien plus fiable pour ce cas précis.
"""

from __future__ import annotations

import httpx
from sqlalchemy.orm import Session, joinedload

from backend.models.recette import Recette, RecetteIngredient
from backend.services.gemma_client import GemmaClient
from backend.services.prompts import build_etapes_system_prompt, build_etapes_user_prompt


def generer_etapes(
    db: Session,
    recette_id: str,
    client: GemmaClient | None = None,
) -> str:
    recette = (
        db.query(Recette)
        .options(joinedload(Recette.ingredients).joinedload(RecetteIngredient.ingredient))
        .filter(Recette.id == recette_id)
        .first()
    )
    if recette is None:
        raise ValueError("Recette introuvable")

    noms = [ligne.ingredient.nom for ligne in recette.ingredients]
    messages = [
        {"role": "system", "content": build_etapes_system_prompt()},
        {"role": "user", "content": build_etapes_user_prompt(recette.nom, noms)},
    ]

    try:
        resultat = (client or GemmaClient()).chat(messages)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise RuntimeError("Gemma indisponible (Ollama / API distante)") from exc

    contenu = (resultat.get("message") or {}).get("content") or ""
    contenu = contenu.strip()
    if not contenu:
        raise RuntimeError("Gemma n'a pas produit d'étapes pour cette recette")
    return contenu
