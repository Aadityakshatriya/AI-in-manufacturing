# ToolLife Policy — AI in Manufacturing course project

We are building a system that listens to a CNC milling machine while it cuts (vibration and motor current), estimates how many more cuts its cutting tool can survive, and recommends whether to **keep going** or **change the tool** before the next cut.

## Start here

**New to the project? Read [`PROJECT_EXPLAINED.md`](PROJECT_EXPLAINED.md) top to bottom.** It starts from zero (what milling is, what a sensor is, what training a model means) and walks through the data, the models, the decision rules, how we test everything, and the plan for the next 10 days. Every technical word is explained, and there is a word list at the end.

The same content as a web page, easier to read on a phone: https://aadityakshatriya.github.io/AI-in-manufacturing/ (source: [`docs/index.html`](docs/index.html))

## Where the project stands

- **August–September 2026:** chose the project, found and checked the dataset, wrote the plan, presented at Review 1.
- **Now:** building. No code has been written yet. For the next review we show what we built, not the problem statement again.
- **Current plan:** decisions are made one cut at a time, costs are assumed (the dataset has no money in it), and reinforcement learning is an optional extra, not the core.

## Space and computing power

**Space and computing power are not a problem for this project.** The raw sensor data is about 25 GB and the neural networks train best on a GPU; Aditya is arranging storage and compute. Do not shrink or skip any part of the plan because of data size or hardware.

## The data

A public 2025 dataset from Rzeszów University of Technology: 14 cutters run until they broke, 968 recorded cuts, 8 vibration and 12 current sensor channels.

- Paper: https://www.nature.com/articles/s41597-025-04923-y
- Files: https://doi.org/10.6084/m9.figshare.28589216

## What is in this repository

**Current project documents**

- [`PROJECT_EXPLAINED.md`](PROJECT_EXPLAINED.md) — the plain-language explanation of the whole project. Read this first.
- [`research/proposals/toollife-policy.md`](research/proposals/toollife-policy.md) — the full technical proposal. Where it differs from `PROJECT_EXPLAINED.md`, the explainer is the current plan.
- [`research/review-1-video-script.md`](research/review-1-video-script.md) — the Review 1 video script.
- [`research/review-1-viva-preparation.md`](research/review-1-viva-preparation.md) — Review 1 question practice for each speaker.
- [`research/aditya-complete-project-guide.md`](research/aditya-complete-project-guide.md) — a longer, more technical walkthrough of the same project.

**How we picked the project (history; you do not need to read these)**

Before choosing ToolLife Policy, we scanned a wide range of manufacturing problems, narrowed them to 100 ideas and then 15 detailed ones, and the team voted for idea number 8. These files record that search:

- [`research/research-method.md`](research/research-method.md), [`research/class-landscape.md`](research/class-landscape.md), [`research/core-problems.md`](research/core-problems.md), [`research/evidence-base.md`](research/evidence-base.md)
- [`research/shortlist.md`](research/shortlist.md), [`research/additional-projects-detailed.md`](research/additional-projects-detailed.md)
- [`research/recommendation.md`](research/recommendation.md) — recommends a welding project (WeldSense) that we did **not** pick
- `research/opportunity-universe-1000.*` and `research/project-longlist-100.*` — the idea spreadsheets, regenerated with `python3 scripts/generate_opportunity_universe.py`
