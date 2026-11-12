"""CrewAI custom tool that wraps the deterministic detector.

The agents never compute separations themselves: they call this tool and reason about its
output (severity, priorities, which aircraft to move). Improvements planned by the team
(weather, restricted areas, wake-turbulence categories...) should be added to
``conflict_detection.py`` and exposed here.
"""

from __future__ import annotations

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from atc_flow.tools.conflict_detection import (
    LATERAL_SEPARATION_NM,
    VERTICAL_SEPARATION_FT,
    detect_conflicts_in_scenario,
)


class ConflictDetectionInput(BaseModel):
    scenario_dir: str = Field(
        ...,
        description="Folder containing airspace.graphml, aircraft.json and flight_plans.json",
    )
    lateral_threshold_nm: float = Field(LATERAL_SEPARATION_NM, description="Lateral minimum (NM)")
    vertical_threshold_ft: float = Field(
        VERTICAL_SEPARATION_FT, description="Vertical minimum (ft)"
    )


class ConflictDetectionTool(BaseTool):
    name: str = "conflict_detection"
    description: str = (
        "Detects losses of separation between the planned trajectories of a scenario. "
        "Returns JSON with the list of conflicts (aircraft pair, time in seconds, horizontal "
        "distance in NM, vertical distance in ft, route segments) and any invalid flight plans."
    )
    args_schema: type[BaseModel] = ConflictDetectionInput

    def _run(
        self,
        scenario_dir: str,
        lateral_threshold_nm: float = LATERAL_SEPARATION_NM,
        vertical_threshold_ft: float = VERTICAL_SEPARATION_FT,
    ) -> str:
        result = detect_conflicts_in_scenario(
            scenario_dir,
            lateral_threshold_nm=lateral_threshold_nm,
            vertical_threshold_ft=vertical_threshold_ft,
        )
        return result.model_dump_json(indent=2)
