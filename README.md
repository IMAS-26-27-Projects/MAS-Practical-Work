# ATC Conflict Detection & Resolution - Multi-Agent System

Practical work of *Multi-Agent Systems* (ETSE-URV / MAI, 2026-27), **Team 11**.

A [CrewAI](https://docs.crewai.com) flow that receives an air traffic scenario (airspace graph,
aircraft and flight plans), detects losses of separation, proposes resolution manoeuvres and
writes an ATC report in Markdown. It is not a real-time system: it reads the inputs, analyses
them, writes the report and ends.

> **Status:** Task 1 (design). The flow in `src/atc_flow/main.py` is a baseline that only
> encodes the mandatory structure, with deterministic placeholders instead of crews. It already
> runs end to end without an LLM.

## How it works

```
inputs ─► Data Management ─► Surveillance & Conflict ─► router ─┬─ conflicts ─► Tactical Resolution ─┐
                                                                 └─ no conflicts ─────────────────────┴─► Reporting ─► report.md
```

Each step writes an intermediate file to `output/` (`01_data_management.json`,
`02_surveillance.json`, `03_tactical_resolution.json`, `report.md`) so that every crew can be
developed and tested on its own.

Conflicts are detected by a deterministic custom tool (`ConflictDetectionTool`, ported from the
course notebook): two aircraft are in conflict when they are simultaneously within **5 NM**
horizontally **and 1000 ft** vertically. Agents use the tool and reason about its output; they
never compute separations themselves.

## Setup

Requirements: Python 3.10-3.13, [uv](https://docs.astral.sh/uv/) and, to run the agents,
[Ollama](https://ollama.com) with the model used in the labs (`qwen3.5:4b`).

```bash
git clone <repo-url> && cd <repo>
uv sync                      # creates .venv with crewai 1.15.22 and the dev tools
cp .env.example .env         # choose the model / scenario
uv run pre-commit install    # git hooks (once per clone)
```

## Running

```bash
uv run crewai run                                       # default scenario (sample_conflict)
ATC_SCENARIO=data/scenarios/sample_no_conflict uv run crewai run
uv run crewai flow plot                                 # interactive diagram of the flow
```

## Inputs

A scenario is a folder in `data/scenarios/` with three files:

| File | Content |
|---|---|
| `airspace.graphml` | Directed graph. Nodes = waypoints (`latitude`, `longitude`); edges = airways (`distance_nm`). |
| `aircraft.json` | `[{"id": "AC1", "speed_kt": 480}, ...]` |
| `flight_plans.json` | `[{"aircraft_id": "AC1", "route": ["A", "B"], "departure_time_s": 0, "cruise_altitude_ft": 30000}, ...]` |

Included: the three examples from the Campus Virtual (`sample_no_conflict`, `sample_conflict`,
`sample_conflict_2`). Our own scenarios will be added here.

## Repository layout

```
src/atc_flow/
├── main.py                 # flow + router
├── crews/                  # one folder per crew (agents.yaml, tasks.yaml, crew.py)
└── tools/
    ├── conflict_detection.py   # deterministic detector (no LLM)
    └── conflict_tool.py        # CrewAI custom tool wrapper
data/scenarios/             # input scenarios
docs/task1/                 # Task 1 report plan and sources
docs/minutes/               # agendas and minutes (copy of the Campus Virtual forum)
docs/reference/             # course notebook (original)
tests/                      # pytest (no LLM in CI)
```

## Team workflow

1. Every piece of work is an issue. Comment `request` on an issue to assign it to yourself.
2. Branch from an up-to-date `main`: `git switch main && git pull && git switch -c feat/<name>`.
3. Small commits. The pre-commit hooks lint and format automatically.
4. Open a PR with `Closes #n`. CI (ruff + pytest + flow run) must be green before merging.

`main` is protected: nobody pushes to it directly.

Checks to run before pushing:

```bash
uv run ruff check . && uv run ruff format --check . && uv run pytest -q
```

Tests that need a real LLM are marked `@pytest.mark.llm` and skipped by default
(`uv run pytest -m llm` to run them locally with Ollama).

### Automation

| Bot | When | What it does |
|---|---|---|
| CI | Every PR and push to `main` | ruff, pytest, runs the flow on every scenario and uploads `output/` as an artefact. |
| PR checks | Every PR | Warns if no issue is linked; labels by folder and size (S/M/L). |
| Stale reminder | Weekdays | Comments on PRs idle for 2 days (never closes). `wip` label or draft to skip. |
| Daily digest | Weekdays 09:00 | Updates the "Team digest" issue with open PRs and the next milestone; pings only when something is stuck. |
| Self-assign | Issue comments | `request` assigns you, `/unassign` removes you. |

## Deliveries

| Milestone | Deadline | Weight |
|---|---|---|
| Task 1 - Design (report + 8-10 slides) | 22/11/2026 | 15% |
| Task 2 - Flow skeleton (ZIP + flow plot) | 16/12/2026 | 5% |
| Final (code ZIP + report + 10-12 slides) | 10/01/2027 | 35% |
| Teamwork (minutes + Git) | continuous | 5% |
