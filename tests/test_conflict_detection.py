"""Golden tests: the ported detector must reproduce the notebook outputs exactly."""

from pathlib import Path

import pytest

from atc_flow.tools.conflict_detection import (
    Aircraft,
    FlightPlan,
    detect_conflicts,
    detect_conflicts_in_scenario,
    load_airspace_graph,
)

SCENARIOS = Path(__file__).resolve().parents[1] / "data" / "scenarios"


def test_no_conflict_when_vertically_separated():
    result = detect_conflicts_in_scenario(SCENARIOS / "sample_no_conflict")
    assert result.conflicts == []
    assert result.validation_errors == []


def test_head_on_conflict_matches_notebook():
    result = detect_conflicts_in_scenario(SCENARIOS / "sample_conflict")
    assert len(result.conflicts) == 1
    c = result.conflicts[0]
    assert (c.aircraft_1, c.aircraft_2) == ("AC1", "AC2")
    assert c.time_s == pytest.approx(112.5)
    assert c.horizontal_distance_nm == 0.0
    assert c.vertical_distance_ft == 0.0
    assert (c.segment_1, c.segment_2) == (["A", "B"], ["B", "A"])


def test_two_crossings_give_two_conflicts():
    result = detect_conflicts_in_scenario(SCENARIOS / "sample_conflict_2")
    assert [c.time_s for c in result.conflicts] == pytest.approx([112.5, 337.5])


def test_thresholds_are_configurable():
    # 2000 ft apart: no conflict with 1000 ft minimum, conflict with a 3000 ft minimum.
    assert not detect_conflicts_in_scenario(SCENARIOS / "sample_no_conflict").has_conflicts
    assert detect_conflicts_in_scenario(
        SCENARIOS / "sample_no_conflict", vertical_threshold_ft=3000
    ).has_conflicts


def test_invalid_plans_are_reported_not_raised():
    graph = load_airspace_graph(SCENARIOS / "sample_conflict" / "airspace.graphml")
    plans = [
        FlightPlan(aircraft_id="GHOST", route=["A", "B"], departure_time_s=0, cruise_altitude_ft=1),
        FlightPlan(aircraft_id="AC1", route=["A", "Z"], departure_time_s=0, cruise_altitude_ft=1),
    ]
    result = detect_conflicts([Aircraft(id="AC1", speed_kt=480)], plans, graph)
    assert result.conflicts == []
    errors = {e.aircraft_id: e.errors for e in result.validation_errors}
    assert errors["GHOST"] == ["unknown aircraft_id: GHOST"]
    assert "unknown route node: Z" in errors["AC1"]


@pytest.mark.parametrize("scenario", sorted(p.name for p in SCENARIOS.iterdir() if p.is_dir()))
def test_every_scenario_is_valid(scenario):
    """Data contract: every scenario folder loads and all its flight plans are valid."""
    result = detect_conflicts_in_scenario(SCENARIOS / scenario)
    assert result.validation_errors == []
