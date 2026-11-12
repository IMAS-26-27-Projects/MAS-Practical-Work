# Task 1 - Design activity

**Deadline:** Sunday 22/11/2026, 23:55 (Campus Virtual). **Weight:** 15%.
**Deliverables:** (1) PDF report with the analysis, (2) PDF with 8-10 slides for a talk of up to
10 minutes. No code is required.

## Report outline

Every section maps to a criterion of the grading rubric (in brackets).

0. **Cover, index, page numbers** [formal quality]
1. **Introduction** - the ATC conflict detection and resolution problem, inputs, expected
   output, mandatory crews and the router requirement. Half a page.
2. **Environment analysis** [analysis of the environment] - Lecture 2 properties, each with a
   justification grounded in *our* system (not generic definitions):
   - Accessible vs inaccessible
   - Deterministic vs non-deterministic
   - Episodic vs non-episodic
   - Static vs dynamic
   - Discrete vs continuous
   - Summary table (property, value, one-line justification)
3. **Agent selection and definition** [agents selection]
   - Decision on extra crews (if any) and why.
   - Per crew: purpose, input file, output file, process (sequential/hierarchical, to be
     confirmed in the final report).
   - Per agent: who it is (real ATC role it is inspired by), main task, tools. Brief, no long
     backstories (the assignment says so explicitly).
   - Overview diagram: crews, router and intermediate files.
4. **Agent taxonomy** [reasoning of properties + identification of types]
   - Properties per agent (Lecture 3): flexibility, reactivity, proactiveness, social ability,
     rationality, reasoning, learning, autonomy, temporal continuity, mobility.
     Table agents x properties, plus a justification of the non-obvious cells.
   - Architecture per agent: reactive / deliberative / hybrid (Lecture 2).
   - Type by purpose: collaborative, interface, information, facilitator, translator
     (Lecture 3). Note where the deterministic conflict tool is an agentification of
     existing code (wrapper).
5. **Conclusions** - main design decisions in five bullets.
6. **Bibliography** [bibliography] - course lectures 2 and 3, the assignment, CrewAI docs,
   ICAO separation standards (Doc 4444), Wooldridge *An Introduction to MultiAgent
   Systems*, Russell & Norvig. Cite them in the text.

Writing rules: English, short paragraphs, every table and figure numbered and referenced,
spell-check before merging (the rubric penalises from 5 errors on).

## Slides (8-10, up to 10 min)

1 Title and team - 2 Problem - 3 Environment analysis (table) - 4 Crews and flow diagram -
5-6 Agents (cards: role, task, tools) - 7 Taxonomy table - 8 Key design decisions and why -
9 Next steps (Task 2). Images and diagrams over text: the rubric rewards slides that focus on
the reasoning behind the group's decisions.

## Plan until the deadline (proposal)

| When | What |
|---|---|
| Meeting 1 (by Mon 16/11) | Roles, repo, split the sections, first list of crews/agents |
| Wed 18/11 | Draft of every section in a PR |
| Meeting 2 (Thu 19/11) | Review drafts, freeze agents list, split slides |
| Sat 21/11 | Final review (spelling, format, bibliography), rehearse the talk |
| Sun 22/11 | Submit both PDFs |
