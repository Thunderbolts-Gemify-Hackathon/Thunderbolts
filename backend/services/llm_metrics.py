"""Métriques qualité LLM : append JSONL + résumé agrégé."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

EVENTS = frozenset(
    {
        "planning_ok",
        "planning_fail",
        "chat_ok",
        "chat_fail",
        "json_parse_ok",
        "json_parse_fail",
        "tool_ok",
        "tool_fail",
        "ce_soir",
    }
)

LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "llm_metrics.jsonl"

# Paires ok/fail pour rates
_RATE_PAIRS = (
    ("planning_ok", "planning_fail"),
    ("chat_ok", "chat_fail"),
    ("json_parse_ok", "json_parse_fail"),
    ("tool_ok", "tool_fail"),
)


def record_event(
    event: str,
    *,
    profil_id: str | None = None,
    latency_ms: float | None = None,
    detail: Any = None,
    path: Path | None = None,
) -> dict[str, Any]:
    if event not in EVENTS:
        raise ValueError(f"event inconnu: {event}")
    entry: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
    }
    if profil_id is not None:
        entry["profil_id"] = profil_id
    if latency_ms is not None:
        entry["latency_ms"] = float(latency_ms)
    if detail is not None:
        entry["detail"] = detail

    target = path or LOG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    return entry


def summarize(
    hours: float = 24,
    *,
    path: Path | None = None,
) -> dict[str, Any]:
    target = path or LOG_PATH
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    counts: Counter[str] = Counter()

    if target.exists():
        with target.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts_raw = row.get("ts")
                if not ts_raw:
                    continue
                try:
                    ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
                except ValueError:
                    continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    continue
                ev = row.get("event")
                if ev in EVENTS:
                    counts[ev] += 1

    rates: dict[str, float | None] = {}
    for ok_key, fail_key in _RATE_PAIRS:
        ok = counts.get(ok_key, 0)
        fail = counts.get(fail_key, 0)
        total = ok + fail
        base = ok_key.removesuffix("_ok")
        rates[f"{base}_ok_rate"] = (ok / total) if total else None

    return {
        "hours": hours,
        "counts": {k: counts.get(k, 0) for k in sorted(EVENTS)},
        "rates": rates,
    }
