# ToolLife Policy: build plan (27–29 October 2026)

This is the working plan for the build. The physics is explained in `docs/physics.html`; the research behind every choice is in `research/next-phase/` (data-survey, physics-brief, model-design, rl-design, costs).

## What changed since Review 1

At Review 1 the plan was one dataset (13 cutters), XGBoost against a small CNN, and a single keep-or-change rule. We have widened all three:

- **Data:** from 1 dataset and 13 cutter lives to 8 public datasets and about 125 cutter lives on about 10 machines, put on one common footing.
- **Model:** a sensor model pretrained on all the raw signals, predicting the chance of failure over the coming cuts, tested on unseen cutters and on a whole unseen machine.
- **Decisions:** an RL agent running a small simulated workshop, benchmarked against the exact optimum where one can be computed.

## 1. Data

| Dataset | Cutter lives | How a life ends | Spindle load | Vibration | Other | Use |
|---|---:|---|---|---|---|---|
| Rzeszów 2025 (ours) | 13 (+1 outlier) | breakage | current, 5 updates/s | 8 ch, 25 kHz | 12 motor currents | main: train, test, RL replay |
| MSTW EndMill 2026 | 25 | wear 300 µm | current, 1 kHz raw | spindle + table, 1 kHz | 3 load cells | cross-machine training and test |
| LUH Hannover 2023 | 9 on 3 machines | wear 150 µm | spindle torque, 500 Hz | none | force 25 kHz | cross-machine test (leave one machine out) |
| NASA Ames | 15 | wear 0.3 mm | spindle current | smoothed | AE | small extra test |
| PHM 2010 | 3 | wear ~165 µm | none | 50 kHz | force 50 kHz | benchmark reviewers expect (needs Kaggle login) |
| NUAA Ideahouse | 13 | wear 0.3 mm | current + power | 400 Hz | | needs IEEE login |
| HES-SO micro-milling | 6 | breakage | currents | 2 kHz | | breakage like ours; no licence stated |
| VMC 650 production | 24 | operator-declared | current (coarse) | IMU (coarse) | | real production lifetimes for the RL workshop |

**Common basis** (details: `research/next-phase/data-survey.md` §4, `physics-brief.md` Part D):

- **Target:** fraction of life used (0 new → 1 end of life) on every dataset, plus each dataset's native remaining life (cycles, runs). End of life is breakage for ours and the dataset's own wear limit for the others; the end type is kept as a label and reported separately.
- **Clock:** cumulative cutting time (all datasets); steel removed (mm³) where it can be computed.
- **Signals:** spindle load (current, torque or power) above idle, divided by the same tool's early-life value; vibration band energies in spindle orders where the sampling rate allows; force where present.
- **Normalisation:** every feature relative to the same tool's first runs, which cancels machine, sensor and setting differences.

## 2. Models

Every model is tested on cutters it never saw, with each cutter weighted equally, and with test cutters locked away until the end.

1. **Yardsticks:** fixed replacement count; age + settings survival model; LightGBM on the 120 released summaries (done: 20.2 cycles mean error, 14.3 in the last 20% of life).
2. **Physics-feature models:** LightGBM and a discrete-time hazard model on the physics features (table current while cutting, net spindle current, energy per mm³, once-per-turn vibration, tooth-pass energy, …).
3. **Main model:** per-sensor encoders on raw signal windows (spectrogram patches for fast signals, patches for slow ones), pretrained by masked reconstruction on all datasets' raw signals; a small GRU over the cutter's history; a hazard head giving the chance of failure in each of the next cuts (→ remaining life, range, next-cut risk). Calibrated with temperature scaling and grouped conformal intervals.
4. **Comparison:** frozen Mantis time-series foundation model embeddings + the same head.

**Tests:** leave-one-cutter-out on ours (13 folds, nested for tuning and calibration); leave-one-machine-out on LUH; leave-one-dataset-out across all; a deliberate random-split run to show how leakage inflates scores.

**Metrics:** remaining-life error overall and in the last 20% of life; dangerous over-estimates near failure; "fails within N" accuracy; calibration; interval coverage; bootstrap confidence intervals over cutters.

## 3. Decisions and RL

- **Single cutter:** keep or change after each cycle. The exact optimum is computed by dynamic programming over the predicted failure curve. Real held-out cutters are replayed, so outcomes are exact; only costs are assumed. RL must match the optimum within 2–3% (correctness check).
- **Workshop (where RL earns its place):** 3 machines (4 as stretch), each replaying a real recorded cutter life that the predictor never trained on; one setter who changes one tool at a time; limited spares; orders with due dates. Actions per machine: run, slow down 20% (Taylor's law, exponent randomised), change, pause. Reward: profit in rupees.
- **Algorithms:** MaskablePPO (main), Double DQN with action masking (comparison), Lagrangian PPO with a breakage budget (factory-realistic).
- **Baselines:** fixed interval, risk threshold with highest-risk-first setter, tuned cost rule, simulation lookahead, perfect-knowledge reference.
- **Success, fixed in advance:** ≥3% more profit than the best tuned rule without more breakages, in ≥70% of cost settings. If not, we report that the rules were as good.

**Costs (India typical, sourced in `costs.md`):** end mill ₹3,000; machine + operator ₹800/h; planned change 10 min → ₹3,133; breakage → ₹6,530 (2.1× a planned change). Sensitivity: breakage = {1.5, 2, 3, 5, 10, 20, 30} × planned change.

## 4. Compute

- GPU: about 25–40 A100-hours for pretraining, training and ablations; under 10 GB of GPU memory per run. Two GPUs let ablations run in parallel.
- CPU: about 150–300 core-hours for RL; 1–3 hours of preprocessing.
- Disk: about 500 GB–1 TB (raw archives ≈ 50 GB compressed, ≈ 200 GB unpacked, plus caches).

## 5. Schedule

| When | Work | Checkpoint for Aaditya |
|---|---|---|
| 27 Oct night | Downloads; convert Rzeszów raw; loaders for MSTW, LUH, NASA, VMC 650 → one common table; physics features; decision layer (DP + replay) on yardstick predictions; RL workshop skeleton | Dataset table with real numbers; first decision results |
| 28 Oct morning | Move data to GPU box; pretrain encoders; physics-feature models | |
| 28 Oct afternoon | Main model, calibration, all tests | Model results table |
| 28 Oct night | RL: single-cutter check vs DP; workshop training starts | RL sanity check |
| 29 Oct morning | Workshop RL + baselines + cost sweep; final tables | All results |
| 29 Oct afternoon | Replay demo page; slides; 5 video scripts (7–8 min) | Slides and scripts |

## 6. Repository layout

- `data/raw/<dataset>/` downloads (gitignored); `data/processed/` common tables and cached windows (gitignored).
- `src/toollife/` library: `rzeszow.py`, `rawzip.py`, `datasets/<name>.py`, `features.py`, `models/`, `policy/` (DP, replay, rules), `rl/` (workshop env, training).
- `scripts/NN_*.py` numbered steps; `results/<step>/` tables and figures (committed).
- `docs/` the public site (explainer, physics, results, demo).

### Interfaces between workstreams

- **Common run table** `data/processed/runs.parquet`, one row per recorded run/cycle: `dataset, tool, run_idx, end_type ('break'|'wear'|'operator'), cum_time_s, cum_volume_mm3 (nullable), life_frac, rul_native, rul_unit, machine, settings…, feature columns…`.
- **Predictions** `results/predictions/<model>.parquet`: `dataset, tool, run_idx, fold, rul_q10, rul_q50, rul_q90, hazard_1 … hazard_K` (probability of failing at each of the next K runs, conditional on surviving so far), produced only by models that never trained on that tool.
