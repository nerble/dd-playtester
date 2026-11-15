from types import SimpleNamespace

import pytest

from dd4tester.hunt_efficiency import load_bounded_hunt_visits


def visit(segment_id, phase="hunt"):
    return {"id": segment_id, "phase": phase, "run_id": segment_id + 100}


def test_visit_lookup_reaches_old_win_without_loading_unrelated_snapshots():
    rows = {10: visit(10), 20: visit(20)}
    calls = []

    def headers(campaign_id, *, limit):
        calls.append(("headers", campaign_id, limit))
        return [rows[20], visit(21, "supply"), rows[10]]

    def load(campaign_id, segment_id):
        calls.append(("load", campaign_id, segment_id))
        return rows[segment_id]

    storage = SimpleNamespace(list_recent_campaign_segment_headers=headers,
        get_campaign_segment_by_id=load, get_run_summary=lambda run_id: {"run": {"id": run_id}})
    recent = [visit(30, "supply"), visit(31, "recovery")]
    result = load_bounded_hunt_visits(storage, 7, "hunt", recent)
    assert [row["id"] for row, _ in result] == [20, 10]
    assert calls == [("headers", 7, 256), ("load", 7, 20), ("load", 7, 10)]


def test_visit_lookup_orders_and_caps_eight_and_reuses_known_boundary():
    rows = {i: visit(i) for i in range(1, 13)}
    loaded = []

    def load(campaign_id, segment_id):
        loaded.append(segment_id)
        return rows[segment_id]

    storage = SimpleNamespace(
        list_recent_campaign_segment_headers=lambda *_a, **_kw: list(rows.values()),
        get_campaign_segment_by_id=load,
        get_run_summary=lambda run_id: {"run": {"id": run_id}},
    )
    result = load_bounded_hunt_visits(storage, 7, "hunt", [rows[12]], rows[11])
    assert [row["id"] for row, _ in result] == list(range(12, 4, -1))
    assert loaded == list(range(10, 4, -1))


@pytest.mark.parametrize("case", ["missing", "foreign-run", "foreign-phase", "missing-summary"])
def test_unknown_visit_cannot_inflate_older_measured_win(case):
    def load(_campaign_id, segment_id):
        if segment_id == 2 and case == "missing":
            return None
        row = visit(segment_id)
        if segment_id == 2 and case == "foreign-run":
            row["run_id"] = 999
        if segment_id == 2 and case == "foreign-phase":
            row["phase"] = "another-hunt"
        return row

    storage = SimpleNamespace(
        list_recent_campaign_segment_headers=lambda *_a, **_kw: [visit(1), visit(2)],
        get_campaign_segment_by_id=load,
        get_run_summary=lambda run_id: None if case == "missing-summary" and run_id == 102 else {},
    )
    assert load_bounded_hunt_visits(storage, 7, "hunt", []) == []


def test_headerless_reader_retains_bounded_recent_and_latest_compatibility():
    storage = SimpleNamespace(get_run_summary=lambda run_id: {"run": {"id": run_id}})
    result = load_bounded_hunt_visits(storage, 7, "hunt", [visit(10)], visit(20))
    assert [row["id"] for row, _ in result] == [20, 10]
