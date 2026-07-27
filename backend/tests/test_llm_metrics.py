from pathlib import Path

from backend.services import llm_metrics


def test_record_event_and_summarize_counts(tmp_path: Path):
    log = tmp_path / "llm_metrics.jsonl"
    llm_metrics.record_event("planning_ok", profil_id="p1", path=log)
    llm_metrics.record_event("planning_ok", profil_id="p1", path=log)
    llm_metrics.record_event("planning_fail", profil_id="p1", path=log)
    llm_metrics.record_event("tool_ok", path=log)
    llm_metrics.record_event("ce_soir", profil_id="p1", path=log)
    llm_metrics.record_event(
        "json_parse_fail", detail={"preview": "nope"}, path=log
    )

    summary = llm_metrics.summarize(hours=24, path=log)
    assert summary["counts"]["planning_ok"] == 2
    assert summary["counts"]["planning_fail"] == 1
    assert summary["counts"]["tool_ok"] == 1
    assert summary["counts"]["ce_soir"] == 1
    assert summary["counts"]["json_parse_fail"] == 1
    assert summary["rates"]["planning_ok_rate"] == 2 / 3
    assert summary["rates"]["tool_ok_rate"] == 1.0
    assert summary["rates"]["json_parse_ok_rate"] == 0.0


def test_record_event_rejects_unknown():
    try:
        llm_metrics.record_event("not_a_real_event")
        assert False, "should raise"
    except ValueError:
        pass
