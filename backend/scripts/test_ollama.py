"""Vérifie qu'Ollama répond avec gemma4:e2b."""

from __future__ import annotations

import os
import sys
import time

import httpx

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")


def main() -> int:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "bonjour, réponds en une phrase"}],
        "stream": False,
        "options": {"num_predict": 50},
    }
    try:
        t0 = time.time()
        with httpx.Client(timeout=30.0) as client:
            r = client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
            r.raise_for_status()
        elapsed = time.time() - t0
        content = (r.json().get("message") or {}).get("content", r.text)
        print(f"OK {MODEL} en {elapsed:.2f}s")
        print(content)
        return 0
    except httpx.ConnectError:
        print(f"Ollama injoignable sur {OLLAMA_HOST} (ollama serve ?)")
        return 1
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            print(f"Modèle introuvable : ollama pull {MODEL}")
        else:
            print(f"HTTP {exc.response.status_code}: {exc.response.text}")
        return 1
    except httpx.TimeoutException:
        print("Timeout Ollama")
        return 1


if __name__ == "__main__":
    sys.exit(main())
