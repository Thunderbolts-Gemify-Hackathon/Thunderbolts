"""Boucle tool-calling Gemma + parsing JSON robuste."""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

from backend.services.gemma_client import GemmaClient
from backend.services.gemma_tools import TOOLS, execute_tool_call

MAX_TOOL_ITERATIONS = 5


def run_tool_loop(
    db: Session,
    client: GemmaClient,
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    max_iterations: int = MAX_TOOL_ITERATIONS,
    trace: list[dict[str, Any]] | None = None,
) -> str:
    """Exécute les tool calls jusqu'à une réponse texte finale.

    Si `trace` est fourni, chaque tool call exécuté y est ajouté (name/arguments/result) —
    utile pour afficher côté client quelles données chiffrées viennent bien d'un outil.
    """
    active_tools = tools if tools is not None else TOOLS
    for _ in range(max_iterations):
        message = client.chat(messages, tools=active_tools)["message"]
        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return message.get("content") or ""

        messages.append({"role": "assistant", "content": message.get("content") or ""})
        for tool_call in tool_calls:
            arguments = tool_call.get("arguments") or {}
            resultat = execute_tool_call(db, tool_call["name"], arguments)
            if trace is not None:
                trace.append({"name": tool_call["name"], "arguments": arguments, "result": resultat})
            messages.append(
                {
                    "role": "tool",
                    "name": tool_call["name"],
                    "content": json.dumps(resultat, ensure_ascii=False, default=str),
                }
            )

    raise RuntimeError("Limite d'itérations d'outils atteinte sans réponse finale de Gemma")


def parse_json_list(contenu: str) -> list[Any] | None:
    """Extrait un tableau JSON depuis une réponse (texte brut ou fence markdown)."""
    texte = (contenu or "").strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", texte)
    if fence:
        texte = fence.group(1).strip()

    data = _loads_or_none(texte)
    if data is None:
        match = re.search(r"\[[\s\S]*\]", texte)
        if not match:
            return None
        data = _loads_or_none(match.group(0))

    return data if isinstance(data, list) else None


def _loads_or_none(texte: str) -> Any | None:
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        return None
