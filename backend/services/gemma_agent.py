"""Boucle tool-calling Gemma + parsing JSON robuste."""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

from backend.services import llm_metrics
from backend.services.gemma_client import GemmaClient
from backend.services.gemma_tools import TOOLS, execute_tool_call

MAX_TOOL_ITERATIONS = 5

_FORCE_ANSWER = (
    "Tu as déjà les résultats d'outils dans l'historique. "
    "Réponds maintenant à l'utilisateur en français, de façon claire et utile, "
    "sans appeler d'outil. Si une info manque (ex. quel produit), pose une question courte."
)

_FALLBACK_ANSWER = (
    "Je n'ai pas pu formuler une réponse complète. "
    "Reformule plus simplement, par exemple : « marché le plus proche » "
    "ou « où acheter du riz »."
)


def _tool_signature(tool_calls: list[dict[str, Any]]) -> str:
    payload = [
        {
            "name": tc.get("name"),
            "arguments": tc.get("arguments") or {},
        }
        for tc in tool_calls
    ]
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)


def _force_final_answer(
    client: GemmaClient,
    messages: list[dict[str, Any]],
) -> str:
    """Dernier tour sans outils : les petits modèles bouclent sinon sans jamais répondre."""
    messages.append({"role": "user", "content": _FORCE_ANSWER})
    try:
        message = client.chat(messages, tools=None)["message"]
    except Exception:
        return _FALLBACK_ANSWER
    content = (message.get("content") or "").strip()
    return content or _FALLBACK_ANSWER


def run_tool_loop(
    db: Session,
    client: GemmaClient,
    messages: list[dict[str, Any]],
    *,
    profil_id: str,
    tools: list[dict[str, Any]] | None = None,
    max_iterations: int = MAX_TOOL_ITERATIONS,
    trace: list[dict[str, Any]] | None = None,
) -> str:
    """Exécute les tool calls jusqu'à une réponse texte finale.

    Si `trace` est fourni, chaque tool call exécuté y est ajouté (name/arguments/result) —
    utile pour afficher côté client quelles données chiffrées viennent bien d'un outil.

    Les petits modèles (ex. gemma2:2b) rappellent parfois le même outil en boucle :
    on coupe dès qu'un appel est répété, puis on force une réponse sans outils.
    """
    active_tools = tools if tools is not None else TOOLS
    # Planning / modes sans outils : un seul tour suffit.
    if not active_tools:
        message = client.chat(messages, tools=None)["message"]
        return (message.get("content") or "").strip()

    seen_signatures: set[str] = set()
    for _ in range(max_iterations):
        message = client.chat(messages, tools=active_tools)["message"]
        tool_calls = message.get("tool_calls")
        if not tool_calls:
            content = (message.get("content") or "").strip()
            if content:
                return content
            # Contenu vide sans outil → forcer une réponse plutôt qu'échouer.
            return _force_final_answer(client, messages)

        sig = _tool_signature(tool_calls)
        if sig in seen_signatures:
            llm_metrics.record_event(
                "tool_loop_repeat",
                profil_id=profil_id,
                detail={"signature": sig[:200]},
            )
            return _force_final_answer(client, messages)
        seen_signatures.add(sig)

        messages.append(
            {
                "role": "assistant",
                "content": message.get("content") or "",
                "tool_calls": [
                    {
                        "function": {
                            "name": tc["name"],
                            "arguments": tc.get("arguments") or {},
                        }
                    }
                    for tc in tool_calls
                ],
            }
        )
        for tool_call in tool_calls:
            arguments = tool_call.get("arguments") or {}
            resultat = execute_tool_call(db, profil_id, tool_call["name"], arguments)
            if trace is not None:
                trace.append(
                    {
                        "name": tool_call["name"],
                        "arguments": arguments,
                        "result": resultat,
                    }
                )
            messages.append(
                {
                    "role": "tool",
                    "name": tool_call["name"],
                    "content": json.dumps(resultat, ensure_ascii=False, default=str),
                }
            )

    llm_metrics.record_event("tool_loop_max", profil_id=profil_id)
    return _force_final_answer(client, messages)


def parse_json_list(contenu: str) -> list[Any] | None:
    """Extrait un tableau JSON depuis une réponse (texte brut ou fence markdown).

    Sur un planning à 1 jour (3 repas ou moins), les petits modèles (ex. gemma2:2b)
    renvoient parfois un unique objet JSON au lieu d'un tableau à un élément :
    on normalise ce cas plutôt que de rejeter une réponse par ailleurs valide.
    """
    texte = (contenu or "").strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", texte)
    if fence:
        texte = fence.group(1).strip()

    data = _loads_or_none(texte)
    if data is None:
        match = re.search(r"\[[\s\S]*\]", texte)
        if match:
            data = _loads_or_none(match.group(0))
    if data is None:
        match = re.search(r"\{[\s\S]*\}", texte)
        if match:
            data = _loads_or_none(match.group(0))

    if isinstance(data, list):
        llm_metrics.record_event("json_parse_ok")
        return data
    if isinstance(data, dict):
        llm_metrics.record_event("json_parse_ok")
        return [data]
    llm_metrics.record_event("json_parse_fail", detail={"preview": (contenu or "")[:120]})
    return None


def _loads_or_none(texte: str) -> Any | None:
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        return None
