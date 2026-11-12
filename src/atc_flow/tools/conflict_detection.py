"""Deterministic conflict detection (no LLM).

Ported from the course notebook ``docs/reference/ConflictDetection.ipynb`` with two changes:

* The data classes are Pydantic models, so the crews can reuse them as structured outputs.
* ``detect_conflicts`` returns the validation errors together with the conflicts (the notebook
  computed them but discarded them).

The algorithm is unchanged: every aircraft follows its route at constant speed and cruise
altitude, positions are projected to a local plane in nautical miles, and for every pair of
route segments that overlap in time we compute the closest point of approach. A conflict is a
pair of aircraft that are simultaneously within ``lateral_threshold_nm`` horizontally AND
``vertical_threshold_ft`` vertically.
"""

from __future__ import annotations

import json
import math
from itertools import combinations
from pathlib import Path

import networkx as nx
from pydantic import BaseModel, Field

LATERAL_SEPARATION_NM = 5.0
VERTICAL_SEPARATION_FT = 1000.0


# --------------------------------------------------------------------------- models


class Aircraft(BaseModel):
    id: str
    speed_kt: float = Field(gt=0, description="Cruise ground speed in knots")


class FlightPlan(BaseModel):
    aircraft_id: str
    route: list[str] = Field(description="Ordered waypoint ids (graph nodes)")
    departure_time_s: float = Field(ge=0)
    cruise_altitude_ft: float = Field(ge=0)


class TrajectoryPoint(BaseModel):
    node_id: str
    time_s: float
    x_nm: float
    y_nm: float
    altitude_ft: float


class Conflict(BaseModel):
    aircraft_1: str
    aircraft_2: str
    time_s: float
    horizontal_distance_nm: float
    vertical_distance_ft: float
    segment_1: list[str]
    segment_2: list[str]


class PlanValidationError(BaseModel):
    aircraft_id: str
    errors: list[str]


class DetectionResult(BaseModel):
    conflicts: list[Conflict] = Field(default_factory=list)
    validation_errors: list[PlanValidationError] = Field(default_factory=list)
    lateral_threshold_nm: float = LATERAL_SEPARATION_NM
    vertical_threshold_ft: float = VERTICAL_SEPARATION_FT

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


# --------------------------------------------------------------------------- loading


def load_airspace_graph(graphml_path: str | Path) -> nx.DiGraph:
    """Load the airspace graph and check the attributes the detector needs."""
    graph = nx.read_graphml(graphml_path)
    for node_id, data in graph.nodes(data=True):
        if "latitude" not in data or "longitude" not in data:
            raise ValueError(f"Node {node_id} missing latitude/longitude attributes")
    for source, target, data in graph.edges(data=True):
        if "distance_nm" not in data:
            raise ValueError(f"Edge {source}->{target} missing distance_nm attribute")
    return graph


def load_aircraft(path: str | Path) -> list[Aircraft]:
    return [Aircraft(**item) for item in json.loads(Path(path).read_text())]


def load_flight_plans(path: str | Path) -> list[FlightPlan]:
    return [FlightPlan(**item) for item in json.loads(Path(path).read_text())]


# --------------------------------------------------------------------------- geometry


def build_trajectory(
    plan: FlightPlan, aircraft: Aircraft, graph: nx.Graph
) -> list[TrajectoryPoint]:
    """Time-stamped trajectory: constant speed and altitude, straight segments,
    equirectangular projection centred on the mean of all graph nodes."""
    latitudes = [float(n["latitude"]) for n in graph.nodes.values()]
    longitudes = [float(n["longitude"]) for n in graph.nodes.values()]
    lat0 = sum(latitudes) / len(latitudes)
    lon0 = sum(longitudes) / len(longitudes)

    trajectory: list[TrajectoryPoint] = []
    current_time = plan.departure_time_s
    for i, node_id in enumerate(plan.route):
        node = graph.nodes[node_id]
        lat, lon = float(node["latitude"]), float(node["longitude"])
        trajectory.append(
            TrajectoryPoint(
                node_id=node_id,
                time_s=current_time,
                x_nm=(lon - lon0) * 60.0 * math.cos(math.radians(lat0)),
                y_nm=(lat - lat0) * 60.0,
                altitude_ft=plan.cruise_altitude_ft,
            )
        )
        if i < len(plan.route) - 1:
            distance_nm = float(graph[node_id][plan.route[i + 1]]["distance_nm"])
            current_time += distance_nm / aircraft.speed_kt * 3600.0
    return trajectory


def position_at(p0: TrajectoryPoint, p1: TrajectoryPoint, time_s: float) -> tuple[float, ...]:
    """Linear interpolation between two trajectory points."""
    if abs(p1.time_s - p0.time_s) < 1e-9:
        ratio = 0.0
    else:
        ratio = (time_s - p0.time_s) / (p1.time_s - p0.time_s)
    return (
        p0.x_nm + ratio * (p1.x_nm - p0.x_nm),
        p0.y_nm + ratio * (p1.y_nm - p0.y_nm),
        p0.altitude_ft + ratio * (p1.altitude_ft - p0.altitude_ft),
    )


def closest_approach(
    a0: TrajectoryPoint,
    a1: TrajectoryPoint,
    b0: TrajectoryPoint,
    b1: TrajectoryPoint,
    t0: float,
    t1: float,
) -> tuple[float, float, float]:
    """Closest approach of two segments in the time window [t0, t1].

    Returns (time_s, horizontal_distance_nm, vertical_distance_ft).
    """
    candidates = [t0, t1]
    ax0, ay0, _ = position_at(a0, a1, t0)
    bx0, by0, _ = position_at(b0, b1, t0)
    ax1, ay1, _ = position_at(a0, a1, t1)
    bx1, by1, _ = position_at(b0, b1, t1)

    rx0, ry0 = ax0 - bx0, ay0 - by0
    vx, vy = (ax1 - bx1) - rx0, (ay1 - by1) - ry0
    denominator = vx * vx + vy * vy
    if denominator > 1e-12:
        u = -(rx0 * vx + ry0 * vy) / denominator
        if 0.0 <= u <= 1.0:
            candidates.append(t0 + u * (t1 - t0))

    best = (candidates[0], float("inf"), float("inf"))
    for t in candidates:
        ax, ay, aa = position_at(a0, a1, t)
        bx, by, ba = position_at(b0, b1, t)
        horizontal = math.hypot(ax - bx, ay - by)
        if horizontal < best[1]:
            best = (t, horizontal, abs(aa - ba))
    return best


# --------------------------------------------------------------------------- detection


def validate_plan(plan: FlightPlan, aircraft_ids: set[str], graph: nx.Graph) -> list[str]:
    errors: list[str] = []
    if plan.aircraft_id not in aircraft_ids:
        errors.append(f"unknown aircraft_id: {plan.aircraft_id}")
    if len(plan.route) < 2:
        errors.append("route must contain at least two nodes")
        return errors
    errors += [f"unknown route node: {n}" for n in plan.route if n not in graph]
    errors += [
        f"missing graph edge: {s} -> {t}"
        for s, t in zip(plan.route[:-1], plan.route[1:], strict=False)
        if not graph.has_edge(s, t)
    ]
    return errors


def detect_conflicts(
    aircraft_list: list[Aircraft],
    flight_plans: list[FlightPlan],
    graph: nx.Graph,
    lateral_threshold_nm: float = LATERAL_SEPARATION_NM,
    vertical_threshold_ft: float = VERTICAL_SEPARATION_FT,
) -> DetectionResult:
    """Detect every loss of separation between pairs of planned trajectories."""
    aircraft_by_id = {a.id: a for a in aircraft_list}
    result = DetectionResult(
        lateral_threshold_nm=lateral_threshold_nm, vertical_threshold_ft=vertical_threshold_ft
    )

    trajectories: dict[str, list[TrajectoryPoint]] = {}
    for plan in flight_plans:
        errors = validate_plan(plan, set(aircraft_by_id), graph)
        if errors:
            result.validation_errors.append(
                PlanValidationError(aircraft_id=plan.aircraft_id, errors=errors)
            )
        else:
            trajectories[plan.aircraft_id] = build_trajectory(
                plan, aircraft_by_id[plan.aircraft_id], graph
            )

    for ac1, ac2 in combinations(sorted(trajectories), 2):
        traj1, traj2 = trajectories[ac1], trajectories[ac2]
        for p1_start, p1_end in zip(traj1[:-1], traj1[1:], strict=False):
            for p2_start, p2_end in zip(traj2[:-1], traj2[1:], strict=False):
                overlap_start = max(p1_start.time_s, p2_start.time_s)
                overlap_end = min(p1_end.time_s, p2_end.time_s)
                if overlap_start > overlap_end:
                    continue
                time_s, horizontal_nm, vertical_ft = closest_approach(
                    p1_start, p1_end, p2_start, p2_end, overlap_start, overlap_end
                )
                if horizontal_nm <= lateral_threshold_nm and vertical_ft <= vertical_threshold_ft:
                    result.conflicts.append(
                        Conflict(
                            aircraft_1=ac1,
                            aircraft_2=ac2,
                            time_s=round(time_s, 3),
                            horizontal_distance_nm=round(horizontal_nm, 3),
                            vertical_distance_ft=round(vertical_ft, 1),
                            segment_1=[p1_start.node_id, p1_end.node_id],
                            segment_2=[p2_start.node_id, p2_end.node_id],
                        )
                    )
    return result


def detect_conflicts_in_scenario(scenario_dir: str | Path, **thresholds: float) -> DetectionResult:
    """Run the detector on a folder with airspace.graphml, aircraft.json, flight_plans.json."""
    scenario_dir = Path(scenario_dir)
    return detect_conflicts(
        load_aircraft(scenario_dir / "aircraft.json"),
        load_flight_plans(scenario_dir / "flight_plans.json"),
        load_airspace_graph(scenario_dir / "airspace.graphml"),
        **thresholds,
    )
