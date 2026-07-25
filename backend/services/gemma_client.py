"""Client Gemma : Ollama local avec bascule automatique vers l'API Gemini."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import httpx

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

ROOT_DIR = Path(__file__).resolve().parents[2]
if load_dotenv:
    load_dotenv(ROOT_DIR / ".env")

OLLAMA_TIMEOUT_S = 15.0
TOOL_JSON_INSTRUCTION = (
    "Tu dois répondre UNIQUEMENT avec un JSON valide, sans markdown ni texte autour, "
    'au format : {"tool_call": {"name": "<nom_outil>", "arguments": {<args>}}} '
    "ou, si aucun outil n'est nécessaire : "
    '{"message": "<ta réponse texte>"}.\n\n'
    "Outils disponibles :\n{tools_json}"
)


class GemmaClient:
    """Chat unifié : Ollama (Gemma) en local, fallback Gemini cloud."""

    def __init__(
        self,
        *,
        ollama_host: str | None = None,
        ollama_model: str | None = None,
        gemma4_api_key: str | None = None,
        gemini_model: str | None = None,
        timeout: float = OLLAMA_TIMEOUT_S,
        prefer_native_tools: bool = True,
    ) -> None:
        self.ollama_host = (ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip(
            "/"
        )
        self.ollama_model = ollama_model or os.getenv("OLLAMA_MODEL", "gemma4:e2b")
        self.gemma4_api_key = gemma4_api_key or os.getenv("GEMMA4_API_KEY", "")
        self.gemini_model = gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.timeout = timeout
        self.prefer_native_tools = prefer_native_tools

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Envoie un chat. Essaie Ollama, puis bascule sur Gemini si besoin."""
        try:
            result = self._chat_ollama(messages, tools)
            print("[GemmaClient] backend=local (Ollama)")
            return result
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            print(f"[GemmaClient] Ollama indisponible ({type(exc).__name__}) -> fallback Gemini")
        except httpx.HTTPStatusError as exc:
            print(
                f"[GemmaClient] Ollama HTTP {exc.response.status_code} -> fallback Gemini"
            )
        except httpx.RequestError as exc:
            print(f"[GemmaClient] Ollama erreur reseau ({exc}) -> fallback Gemini")

        result = self._chat_gemini(messages, tools)
        print("[GemmaClient] backend=fallback (Gemini API)")
        return result

    # ------------------------------------------------------------------ Ollama

    def _chat_ollama(self, messages: list[dict], tools: list[dict] | None) -> dict:
        url = f"{self.ollama_host}/api/chat"
        use_native = bool(tools) and self.prefer_native_tools

        if tools and not use_native:
            payload_messages = self._messages_with_tool_prompt(messages, tools)
            payload_tools = None
        else:
            payload_messages = messages
            payload_tools = self._to_openai_tools(tools) if tools else None

        payload: dict[str, Any] = {
            "model": self.ollama_model,
            "messages": payload_messages,
            "stream": False,
        }
        if payload_tools:
            payload["tools"] = payload_tools

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # Modèle sans support tools natif → retry en JSON structuré
            if tools and use_native and exc.response.status_code == 400:
                return self._chat_ollama_json_tools(messages, tools)
            raise

        data = response.json()
        normalized = self._normalize_ollama(data)

        if tools and not normalized["message"].get("tool_calls"):
            parsed = self._parse_tool_json(normalized["message"].get("content") or "")
            if parsed is not None:
                normalized["message"] = parsed

        return normalized

    def _chat_ollama_json_tools(self, messages: list[dict], tools: list[dict]) -> dict:
        payload = {
            "model": self.ollama_model,
            "messages": self._messages_with_tool_prompt(messages, tools),
            "stream": False,
            "format": "json",
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.ollama_host}/api/chat", json=payload)
            response.raise_for_status()

        data = response.json()
        normalized = self._normalize_ollama(data)
        parsed = self._parse_tool_json(normalized["message"].get("content") or "")
        if parsed is not None:
            normalized["message"] = parsed
        return normalized

    def _normalize_ollama(self, data: dict) -> dict:
        msg = data.get("message") or {}
        tool_calls = self._extract_ollama_tool_calls(msg)
        return {
            "backend": "ollama",
            "model": data.get("model", self.ollama_model),
            "message": {
                "role": msg.get("role", "assistant"),
                "content": msg.get("content") or "",
                "tool_calls": tool_calls,
            },
            "raw": data,
        }

    @staticmethod
    def _extract_ollama_tool_calls(msg: dict) -> list[dict] | None:
        raw_calls = msg.get("tool_calls")
        if not raw_calls:
            return None
        parsed: list[dict] = []
        for call in raw_calls:
            fn = call.get("function") or call
            name = fn.get("name")
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"_raw": args}
            if name:
                parsed.append({"name": name, "arguments": args or {}})
        return parsed or None

    # ------------------------------------------------------------------ Gemini

    def _chat_gemini(self, messages: list[dict], tools: list[dict] | None) -> dict:
        if not self.gemma4_api_key:
            raise RuntimeError(
                "GEMMA4_API_KEY manquante dans .env - impossible d'utiliser le fallback API"
            )

        use_native = bool(tools) and self.prefer_native_tools
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.gemini_model}:generateContent"
        )

        if tools and not use_native:
            contents, system = self._to_gemini_contents(
                self._messages_with_tool_prompt(messages, tools)
            )
            gemini_tools = None
        else:
            contents, system = self._to_gemini_contents(messages)
            gemini_tools = self._to_gemini_tools(tools) if tools else None

        body: dict[str, Any] = {"contents": contents}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if gemini_tools:
            body["tools"] = gemini_tools

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                params={"key": self.gemma4_api_key},
                json=body,
            )
            # Gemini peut refuser le format tools → retry JSON
            if tools and use_native and response.status_code >= 400:
                return self._chat_gemini_json_tools(messages, tools)
            response.raise_for_status()
            data = response.json()

        normalized = self._normalize_gemini(data)

        if tools and not normalized["message"].get("tool_calls"):
            parsed = self._parse_tool_json(normalized["message"].get("content") or "")
            if parsed is not None:
                normalized["message"] = parsed

        return normalized

    def _chat_gemini_json_tools(self, messages: list[dict], tools: list[dict]) -> dict:
        contents, system = self._to_gemini_contents(
            self._messages_with_tool_prompt(messages, tools)
        )
        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"responseMimeType": "application/json"},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.gemini_model}:generateContent"
        )
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                params={"key": self.gemma4_api_key},
                json=body,
            )
            response.raise_for_status()
            data = response.json()

        normalized = self._normalize_gemini(data)
        parsed = self._parse_tool_json(normalized["message"].get("content") or "")
        if parsed is not None:
            normalized["message"] = parsed
        return normalized

    def _normalize_gemini(self, data: dict) -> dict:
        candidates = data.get("candidates") or []
        parts: list[dict] = []
        if candidates:
            parts = (candidates[0].get("content") or {}).get("parts") or []

        text_chunks: list[str] = []
        tool_calls: list[dict] = []
        for part in parts:
            if "text" in part:
                text_chunks.append(part["text"])
            fc = part.get("functionCall")
            if fc:
                tool_calls.append(
                    {
                        "name": fc.get("name", ""),
                        "arguments": fc.get("args") or {},
                    }
                )

        return {
            "backend": "gemini",
            "model": self.gemini_model,
            "message": {
                "role": "assistant",
                "content": "".join(text_chunks),
                "tool_calls": tool_calls or None,
            },
            "raw": data,
        }

    @staticmethod
    def _to_gemini_contents(messages: list[dict]) -> tuple[list[dict], str | None]:
        system_parts: list[str] = []
        contents: list[dict] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content") or ""
            if role == "system":
                system_parts.append(content)
                continue
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": content}]})

        # Gemini exige au moins un message user
        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Bonjour"}]})

        system = "\n\n".join(system_parts) if system_parts else None
        return contents, system

    @staticmethod
    def _to_gemini_tools(tools: list[dict]) -> list[dict]:
        declarations: list[dict] = []
        for tool in tools:
            fn = tool.get("function") if tool.get("type") == "function" else tool
            if not fn or not fn.get("name"):
                continue
            decl: dict[str, Any] = {
                "name": fn["name"],
                "description": fn.get("description") or "",
            }
            params = fn.get("parameters")
            if params:
                decl["parameters"] = params
            declarations.append(decl)
        return [{"functionDeclarations": declarations}] if declarations else []

    # --------------------------------------------------------------- helpers

    @staticmethod
    def _to_openai_tools(tools: list[dict]) -> list[dict]:
        """Normalise vers le format OpenAI/Ollama function calling."""
        normalized: list[dict] = []
        for tool in tools:
            if tool.get("type") == "function" and "function" in tool:
                normalized.append(tool)
                continue
            # Déjà plat : {name, description, parameters}
            if "name" in tool:
                normalized.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool.get("description") or "",
                            "parameters": tool.get("parameters")
                            or {"type": "object", "properties": {}},
                        },
                    }
                )
        return normalized

    def _messages_with_tool_prompt(
        self, messages: list[dict], tools: list[dict]
    ) -> list[dict]:
        tools_json = json.dumps(self._to_openai_tools(tools), ensure_ascii=False, indent=2)
        instruction = TOOL_JSON_INSTRUCTION.format(tools_json=tools_json)
        enriched = [dict(m) for m in messages]
        # Préfixe un message system dédié (ou fusionne avec l'existant)
        if enriched and enriched[0].get("role") == "system":
            enriched[0] = {
                **enriched[0],
                "content": f"{enriched[0].get('content', '')}\n\n{instruction}",
            }
        else:
            enriched.insert(0, {"role": "system", "content": instruction})
        return enriched

    @staticmethod
    def _parse_tool_json(content: str) -> dict | None:
        """Parse {"tool_call": {...}} ou {"message": "..."} depuis le contenu texte."""
        if not content or not content.strip():
            return None

        text = content.strip()
        # Enlève éventuels fences markdown
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Tentative : extraire le premier objet JSON
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                return None
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

        if not isinstance(data, dict):
            return None

        tool_call = data.get("tool_call")
        if isinstance(tool_call, dict) and tool_call.get("name"):
            args = tool_call.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"_raw": args}
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"name": tool_call["name"], "arguments": args or {}}],
            }

        if "message" in data and isinstance(data["message"], str):
            return {
                "role": "assistant",
                "content": data["message"],
                "tool_calls": None,
            }

        return None
