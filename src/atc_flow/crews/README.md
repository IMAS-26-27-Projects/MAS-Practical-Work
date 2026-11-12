# Crews

One folder per crew, created with the CrewAI layout once the design (Task 1) is agreed:

```
crews/<crew_name>/
├── config/
│   ├── agents.yaml
│   └── tasks.yaml
└── <crew_name>.py
```

Mandatory crews (assignment): `data_management_crew`, `surveillance_crew`,
`tactical_resolution_crew`, `reporting_crew`. Extra crews are allowed.

Rules agreed for all crews:

- Each crew writes its result to an intermediate file in `output/` and reads its input
  from the previous crew's file, so it can be run and tested on its own.
- Structured outputs use Pydantic models (`output_pydantic`). Reuse the models in
  `tools/conflict_detection.py` when possible.
- Agents never compute separations by themselves: they call `ConflictDetectionTool`.
