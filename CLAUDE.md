# CLAUDE.md

Claude Code loads this file and ignores `AGENTS.md`. The import below pulls in the
shared CrewAI guidance so every coding assistant works from the same instructions.
Keep shared conventions in `AGENTS.md`; add Claude-specific notes under the import.

@AGENTS.md

## Project notes (Team 11, MAS ATC)

- CrewAI is pinned to 1.15.22 (course version). Do not upgrade it.
- The conflict detector in `src/atc_flow/tools/conflict_detection.py` is deterministic and is
  the single source of truth for separations. Agents call the tool; they never compute distances.
- Every crew reads its input from, and writes its output to, an intermediate file in `output/`.
- No test may call an LLM unless it is marked `@pytest.mark.llm`.
- Run `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` before proposing a PR.
