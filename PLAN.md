# ToolLife Policy: build plan (27–29 October 2026)

This is the working plan for the build. The physics is explained in `docs/physics.html`; the research behind every choice is in `research/next-phase/` (data-survey, physics-brief, model-design, rl-design, costs).

## What changed since Review 1

At Review 1 the plan was one dataset (13 cutters), XGBoost against a small CNN, and a single keep-or-change rule. After a wide research pass we kept the models simple enough for every team member to explain, and widened the parts that make the project real:

- **Model:** a 1D CNN autoencoder that learns what healthy cutting sounds like, feeding a TCN that reads the cutter's history and predicts remaining life (low/middle/high) and the chance of breaking soon. Both are convolutional networks, as promised at Review 1.
- **Decisions:** keep/change for one cutter checked against the exact optimum, plus RL (DQN and PPO) in a small 3-machine workshop.
- **Data:** our 13 cutters, plus one experiment across 4–5 other public datasets on shared features.

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

## 2. Models (agreed 27 Oct: simple, convolutional, trains on the Mac)

Every model is tested on cutters it never saw (hide one cutter, train on the other 12, repeat 13 times), each cutter weighted equally.

1. **Yardsticks:** fixed replacement count; settings + age survival model; LightGBM on the 120 released summaries (done: 20.2 cycles mean error, 14.3 in the last 20% of life).
2. **CNN autoencoder (about 3M parameters).** Input: 0.16 s of vibration from the five table sensors (5 × 4,096 samples). Encoder: 6 convolution layers squeeze it into a 64-number fingerprint. Decoder: the mirror image rebuilds the vibration. Trained without labels on the healthy early part of each training cutter's life; an autoencoder never hears the cutter it is later judged on (5 fold groups). Gives two things per cycle: the fingerprint, and a **health score** = how badly it rebuilds the sound.
3. **TCN predictor (about 100k parameters).** Per cycle about 30 inputs: fingerprint, health score, motor-current features (spindle and table current, energy per mm³), settings, age. Four dilated causal convolution layers look back over about 30 cycles. Output: a risk curve (chance of breaking on each of the next cycles), from which we read remaining life low/middle/high and the chance of breaking within 1, 3 and 5 cycles. Calibrated with one temperature and a grouped conformal safety margin.
4. **Ablation:** the same TCN without the autoencoder inputs, to show whether the autoencoder adds anything.
5. **Shared-feature experiment:** the same TCN on features every dataset has (spindle load and vibration relative to the cutter's early life, fraction of life used), trained on the other datasets and tested on ours.

**Metrics:** remaining-life error overall and in the last 20% of life; dangerous over-estimates near failure; chance-of-breaking accuracy; interval coverage.

## 3. Decisions and RL

- **Single cutter:** keep or change after each cycle. The exact optimum is computed from the risk curve. Real held-out cutters are replayed, so outcomes are exact; only costs are assumed. RL must match the optimum within 2–3%.
- **Small workshop:** 3 machines, each replaying a real held-out cutter life; one setter who changes one tool at a time; actions per machine: run, slow down 20% (Taylor's law, exponent varied), change. Reward: profit in rupees.
- **Algorithms:** DQN and PPO (with impossible actions blocked), from standard libraries.
- **Baselines:** fixed interval, risk threshold, one-step cost rule, exact optimum (single cutter), perfect-knowledge reference.
- **Success, fixed in advance:** more profit than the best tuned rule without more breakages, in most cost settings. If not, we report that the rules were as good.

**Costs (India typical, sourced in `research/next-phase/costs.md`):** end mill ₹3,000; machine + operator ₹800/h; planned change ₹3,133; breakage ₹6,530 (2.1× a planned change). Sensitivity: breakage = {1.5, 2, 3, 5, 10, 20, 30} × planned change.

## 4. Compute

The Mac (Apple M5, 10 cores, 16 GB) is enough: autoencoders about 20–40 minutes each on its GPU, the TCN seconds to minutes per fold, RL on the CPU cores. A GPU box would only make it faster.

## 5. Schedule

| When | Work | Checkpoint for Aaditya |
|---|---|---|
| 27 Oct night | Convert raw data; physics features; loaders for other datasets; single-cutter decisions on yardstick predictions; RL environment | First decision results |
| 28 Oct | CNN autoencoders (5 fold groups); TCN predictor with and without them; calibration; shared-feature experiment | Model results table |
| 28 Oct night | RL: single cutter vs exact optimum; workshop training | RL sanity check |
| 29 Oct morning | Workshop results and cost sweep; final tables | All results |
| 29 Oct afternoon | Replay demo page; slides; 5 video scripts (7–8 min) | Slides and scripts |

## 6. Repository layout

- `data/raw/<dataset>/` downloads (gitignored); `data/processed/` common tables and cached windows (gitignored).
- `src/toollife/` library: `rzeszow.py`, `rawzip.py`, `datasets/<name>.py`, `features.py`, `models/`, `policy/` (DP, replay, rules), `rl/` (workshop env, training).
- `scripts/NN_*.py` numbered steps; `results/<step>/` tables and figures (committed).
- `docs/` the public site (explainer, physics, results, demo).

### Interfaces between workstreams

- **Common run table** `data/processed/runs.parquet`, one row per recorded run/cycle: `dataset, tool, run_idx, end_type ('break'|'wear'|'operator'), cum_time_s, cum_volume_mm3 (nullable), life_frac, rul_native, rul_unit, machine, settings…, feature columns…`.
- **Predictions** `results/predictions/<model>.parquet`: `dataset, tool, run_idx, fold, rul_q10, rul_q50, rul_q90, hazard_1 … hazard_K` (probability of failing at each of the next K runs, conditional on surviving so far), produced only by models that never trained on that tool.
