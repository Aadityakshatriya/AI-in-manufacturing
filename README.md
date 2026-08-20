# AI in Manufacturing — Project Selection Research

This repository is the working base for selecting and then building an ambitious,
explainable AI-in-manufacturing course project over 8–12 weeks.

## Current research artifacts

- [`research/research-method.md`](research/research-method.md) — constraints, scope, and filtering method.
- [`research/class-landscape.md`](research/class-landscape.md) — audit of the provided class Google Sheet.
- [`research/core-problems.md`](research/core-problems.md) — the 14 recurring manufacturing problem families, where AI helps, and where standard student projects fall short.
- [`research/opportunity-universe-1000.csv`](research/opportunity-universe-1000.csv) and its [formatted XLSX version](research/opportunity-universe-1000.xlsx) — systematic breadth map: 50 manufacturing contexts × 20 AI intervention patterns.
- [`research/project-longlist-100.csv`](research/project-longlist-100.csv) and its [formatted XLSX version](research/project-longlist-100.xlsx) — 100 concrete, decision-linked project directions.
- [`research/evidence-base.md`](research/evidence-base.md) — primary papers, official roadmaps, public datasets, and what each source establishes.
- [`research/shortlist.md`](research/shortlist.md) — ranked shortlist and detailed flagship concepts.
- [`research/additional-projects-detailed.md`](research/additional-projects-detailed.md) — fifteen more complete project charters with models, data, evaluation, demos, risks, and fallbacks.
- [`research/recommendation.md`](research/recommendation.md) — final recommendation, fallback plan, deliverables, and 12-week execution path.

The generated CSVs can be reproduced with:

```bash
python3 scripts/generate_opportunity_universe.py
```

## Selection principle

The project should not stop at “predict a label.” Its output must change a real
manufacturing decision: adjust a process, decide what to inspect, plan an
operation, mitigate a disruption, or choose a recovery action. The model may be
advanced, but its architecture and role must remain explainable to first-year
students without introducing new ML theory.
