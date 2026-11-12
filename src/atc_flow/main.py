#!/usr/bin/env python
"""ATC flow - BASELINE PROPOSAL, to be discussed by the team (Task 2).

This file only encodes what the assignment makes mandatory:

    load inputs -> Data Management -> Surveillance & Conflict -> router
        conflicts    -> Tactical Resolution -> Reporting
        no conflicts -> Reporting

None of the crews exist yet: each step is a deterministic placeholder (marked ``TODO(crew)``)
so that the flow already runs end to end without an LLM, the router decides on real data and
``crewai flow plot`` works. Each step writes its intermediate file to ``output/`` so that every
crew can later be developed and tested on its own, as the assignment recommends.

Run:
    crewai run                                  # default scenario
    ATC_SCENARIO=data/scenarios/sample_no_conflict crewai run
    crewai flow plot                            # writes the interactive flow diagram
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from crewai.flow import Flow, listen, or_, router, start
from pydantic import BaseModel, Field

from atc_flow.tools.conflict_detection import DetectionResult, detect_conflicts_in_scenario

DEFAULT_SCENARIO = "data/scenarios/sample_conflict"

CONFLICTS = "conflicts_detected"
NO_CONFLICTS = "no_conflicts"


class ATCState(BaseModel):
    scenario_dir: str = Field(default_factory=lambda: os.getenv("ATC_SCENARIO", DEFAULT_SCENARIO))
    output_dir: str = Field(default_factory=lambda: os.getenv("ATC_OUTPUT", "output"))
    detection: DetectionResult | None = None
    resolutions: list[dict] = Field(default_factory=list)
    route_taken: str = ""


class ATCFlow(Flow[ATCState]):
    def _write(self, name: str, payload: str) -> Path:
        path = Path(self.state.output_dir) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
        return path

    @start()
    def data_management(self):
        """TODO(crew): Data Management Crew - validate and normalise the input files."""
        scenario = Path(self.state.scenario_dir)
        missing = [
            f
            for f in ("airspace.graphml", "aircraft.json", "flight_plans.json")
            if not (scenario / f).exists()
        ]
        if missing:
            raise FileNotFoundError(f"Scenario {scenario} is missing: {', '.join(missing)}")
        self._write(
            "01_data_management.json",
            json.dumps({"scenario_dir": str(scenario), "status": "placeholder"}, indent=2),
        )

    @listen(data_management)
    def surveillance(self):
        """TODO(crew): Surveillance & Conflict Crew - agents call ConflictDetectionTool."""
        self.state.detection = detect_conflicts_in_scenario(self.state.scenario_dir)
        self._write("02_surveillance.json", self.state.detection.model_dump_json(indent=2))

    # `emit` declares the possible outcomes so that `crewai flow plot` can draw both branches.
    @router(surveillance, emit=[CONFLICTS, NO_CONFLICTS])
    def route_on_conflicts(self) -> str:
        """Mandatory dynamic routing: Tactical Resolution only when there are conflicts."""
        has_conflicts = self.state.detection is not None and self.state.detection.has_conflicts
        self.state.route_taken = CONFLICTS if has_conflicts else NO_CONFLICTS
        return self.state.route_taken

    @listen(CONFLICTS)
    def tactical_resolution(self):
        """TODO(crew): Tactical Resolution Crew - propose safe manoeuvres."""
        self.state.resolutions = [
            {"conflict": c.model_dump(), "manoeuvre": "TODO"}
            for c in self.state.detection.conflicts
        ]
        self._write("03_tactical_resolution.json", json.dumps(self.state.resolutions, indent=2))

    @listen(or_(NO_CONFLICTS, tactical_resolution))
    def reporting(self):
        """TODO(crew): Reporting Crew - write the ATC report in Markdown."""
        detection = self.state.detection
        lines = [
            "# ATC Report (placeholder)",
            "",
            f"- Scenario: `{self.state.scenario_dir}`",
            f"- Route taken by the router: `{self.state.route_taken}`",
            f"- Conflicts detected: {len(detection.conflicts)}",
            f"- Invalid flight plans: {len(detection.validation_errors)}",
            "",
        ]
        for c in detection.conflicts:
            lines.append(
                f"- {c.aircraft_1} vs {c.aircraft_2} at t={c.time_s} s: "
                f"{c.horizontal_distance_nm} NM / {c.vertical_distance_ft} ft "
                f"(segments {'-'.join(c.segment_1)} / {'-'.join(c.segment_2)})"
            )
        path = self._write("report.md", "\n".join(lines) + "\n")
        print(f"Report written to {path}")


def kickoff():
    ATCFlow().kickoff()


def plot():
    ATCFlow().plot()


if __name__ == "__main__":
    kickoff()
