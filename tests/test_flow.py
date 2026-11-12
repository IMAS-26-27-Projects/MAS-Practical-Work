"""The baseline flow runs without an LLM and the router takes the right branch."""

import json
from pathlib import Path

import pytest

from atc_flow.main import CONFLICTS, NO_CONFLICTS, ATCFlow
from atc_flow.tools.conflict_tool import ConflictDetectionTool

SCENARIOS = Path(__file__).resolve().parents[1] / "data" / "scenarios"


@pytest.mark.parametrize(
    ("scenario", "expected_route", "tactical_file"),
    [
        ("sample_no_conflict", NO_CONFLICTS, False),
        ("sample_conflict", CONFLICTS, True),
        ("sample_conflict_2", CONFLICTS, True),
    ],
)
def test_router_branches(tmp_path, scenario, expected_route, tactical_file):
    flow = ATCFlow()
    flow.kickoff(inputs={"scenario_dir": str(SCENARIOS / scenario), "output_dir": str(tmp_path)})
    assert flow.state.route_taken == expected_route
    assert (tmp_path / "02_surveillance.json").exists()
    assert (tmp_path / "03_tactical_resolution.json").exists() is tactical_file
    assert (tmp_path / "report.md").exists()


def test_tool_returns_json():
    out = ConflictDetectionTool().run(scenario_dir=str(SCENARIOS / "sample_conflict"))
    assert len(json.loads(out)["conflicts"]) == 1
