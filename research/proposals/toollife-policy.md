# Concrete project proposal: ToolLife Policy

> **Update (October 2026):** the plain-language explainer
> [`../../PROJECT_EXPLAINED.md`](../../PROJECT_EXPLAINED.md) is the current plan.
> Three things changed after this proposal was written: decisions are made one
> milling cycle at a time (the dataset does not support multi-cycle "jobs" with
> deadlines and part values), all costs are assumed and tested across a range of
> settings, and reinforcement learning is an optional extra rather than part of
> the core.

**Status:** selected project direction  
**Recommended duration:** 10–12 weeks  
**Process:** CNC end milling  
**System output:** **CONTINUE** or **REPLACE BEFORE THE NEXT JOB**, with an
optional derating/RL extension only after the core system works.

## 1. Proposal in one paragraph

We will build an uncertainty-aware decision-support system for cutting-tool
replacement in CNC milling. After every milling cycle, the system will use
vibration, spindle/axis current, cutting conditions, and recent tool history to
estimate a *distribution* of remaining useful life (RUL), not just one number. It
will then combine the probability of failure during the next job with tool cost,
planned changeover time, unplanned downtime, scrap value, and due-date pressure to
decide whether production should continue or the tool should be replaced. The
system will be validated on entire unseen tool lifecycles, compared against fixed
replacement schedules and point-prediction policies, and demonstrated through an
interactive production replay/digital twin.

## 2. Submission-ready problem statement

> **Develop and validate an uncertainty-aware, production-aware cutting-tool
> replacement system for CNC milling that estimates the probability distribution
> of remaining tool life from multi-sensor process data and chooses whether to
> continue machining or replace the tool before the next job so as to minimize
> expected production loss. Compare the proposed policy with fixed-age,
> threshold-based, and point-RUL policies using leave-one-tool-out evaluation,
> real run-to-failure replays, and a documented production simulator.**

This is a manufacturing decision project, not merely a tool-wear prediction
notebook. The actual question is not “How worn is the cutter?” but:

> **Is the remaining value in this tool worth the risk of using it for the next
> production job?**

## 3. Why the problem matters

A factory faces two asymmetric mistakes:

- **Replace too early:** usable tool life is discarded and planned downtime and
  tooling cost increase.
- **Replace too late:** the cutter can break during a job, potentially scrapping
  the part and causing unplanned downtime, recovery work, or schedule delay.

The optimal choice changes with production context. A tool that is acceptable for
one low-value part may be unacceptable immediately before a long, expensive, or
urgent job. A fixed cycle limit or a fixed wear threshold cannot represent that
trade-off. Prior tool-management research explicitly frames replacement as a
balance between quality loss, replacement cost, and failure risk; recent work also
shows the value of making tool maintenance depend on dynamic production risk
([Jeang, 1998](https://doi.org/10.1016/S0377-2217(96)00368-2);
[Errandonea et al., 2026](https://doi.org/10.1016/j.cie.2025.111716)).

AI is justified because multi-sensor signals contain nonlinear, noisy evidence of
damage, while the final decision must account for uncertain consequences. Signal
interpretation is learned; cost accounting and safety constraints remain explicit.

## 4. The exact research contribution

The contribution is **not** a new neural-network theory and is **not** another
attempt to obtain a flattering RUL score from a random train/test split. It is the
integration of five understandable pieces:

1. leakage-safe tool-health prediction on completely unseen cutters;
2. a calibrated interval/distribution rather than an overconfident point estimate;
3. a transparent production-cost model;
4. a replacement policy evaluated on real observed run-to-failure trajectories;
5. an operator-facing replay that explains both the health estimate and the
   economic reason for the action.

The primary research question is:

> **Does calibrated sensor-based failure risk reduce expected production cost
> versus the best fixed replacement schedule without increasing the observed tool
> failure rate on unseen cutters?**

Secondary questions are:

- Do sensors add information beyond simply knowing how many cycles the tool has
  already completed?
- How much accuracy is lost when the system uses only spindle current or only
  spindle vibration instead of all 20 channels?
- Does uncertainty calibration improve replacement decisions under unfamiliar
  tools, cutting conditions, sensor noise, or missing sensors?
- Does a simple dynamic-programming policy perform as well as or better than an RL
  policy for this decision?

## 5. Data found and verified

### 5.1 Primary dataset — sufficient for the complete project

The primary source is the 2025 *Scientific Data* release
[A new open dataset from a milling process—data for classification and estimation
of tool life](https://www.nature.com/articles/s41597-025-04923-y), with the actual
files hosted in the [official Figshare record](https://doi.org/10.6084/m9.figshare.28589216).
It is licensed **CC BY 4.0**.

The experiment used a Haas VF-1 mill and 42CrMo4 workpieces. It contains:

- **14 cutting tools used from new condition until actual breakage**;
- **968 milling cycles**;
- two cutter types;
- axial depth of cut of 5 or 10 mm and radial depth of cut of 4.5 or 8 mm;
- workpiece hardness from 35.33 to 41.67 HRC;
- **8 vibration channels sampled at 25 kHz**;
- **12 spindle/axis-current channels sampled at 0.5 kHz**;
- exact cycles-to-failure labels and complete process metadata.

The paper notes that one cutter broke during its first cycle. We will preserve it
as an extreme stress case but exclude it from ordinary model fitting, leaving 13
meaningful tool groups. The remaining lifetimes vary substantially—roughly 15 to
149 recorded cycles—which makes fixed-age replacement genuinely imperfect.

The release already contains a fast baseline table with **120 signal features**
(minimum, maximum, mean, standard deviation, skewness, and kurtosis for each of 20
channels) plus metadata. We inspected the files and confirmed 968 records, 14 tool
IDs, two tool types, the process variables, and both raw and normalized
cycles-to-failure targets.

| File | Size | Role in this project | Direct access |
|---|---:|---|---|
| `metadata.xlsx` | 72.9 kB | Tool IDs, conditions, cycle count, and RUL labels | [Download](https://ndownloader.figshare.com/files/52968950) |
| `FeatureAndMetadata_Milling.csv` | 1.80 MB | Immediate classical-ML baseline | [Download](https://ndownloader.figshare.com/files/52968974) |
| `raw_data.zip` | 25.35 GB (23.60 GiB) | Raw-signal 1D-CNN/TCN model and sensor ablations | [Download](https://ndownloader.figshare.com/files/52969793) |

The small files allow work to start immediately; the raw archive is needed only
for the deep-signal model. The data authors themselves recommend grouping by tool
and testing on a cutter absent from training, matching our intended evaluation.

### 5.2 Secondary datasets — robustness, not critical-path dependencies

| Dataset | What it adds | How we will use it | Important limitation |
|---|---|---|---|
| [NASA Milling Wear](https://catalog.data.gov/dataset/milling-wear) | Different materials, speeds, feeds, and depths of cut; VB flank-wear measurements; current, vibration, and acoustic-emission signals | External condition-shift test and possible derating-model support | Small and not a clean multi-tool run-to-failure replacement benchmark |
| [PHM Society 2010 milling challenge](https://phmsociety.org/phm_competition/) | 50 kHz force, vibration, and acoustic emission from high-speed milling; microscope wear | Wear-regression and representation-transfer check; a convenient [packaged mirror](https://huggingface.co/datasets/AI4Manufacturing/PHM2010) exists | Only three labelled cutters in the common training set and no documented failure threshold; it must not be treated as our replacement ground truth |
| [QIT-CEMC](https://github.com/wwz456/QIT-CEMC-dataset) | Full-life force, torque, vibration, sound, cutter images, and wear on four cutting edges over 68 cycles | Optional multimodal stretch experiment | Essentially one tool lifecycle and a less convenient external download |

These sources will not be pooled blindly because the machines, tools, materials,
sensors, sampling rates, and targets differ. They are useful precisely because
they expose domain shift.

## 6. Data leakage controls

Tool-life datasets are extremely easy to misuse. Our protocol will make the
following distinctions explicit:

- **Age-only baseline:** cycle count and cutting conditions, but no sensor data.
- **Sensor-only model:** current/vibration evidence, but no cycle number or file
  name.
- **Full deployment model:** sensors, process metadata, and the legitimately known
  number of completed cycles.

`FileName`, `ToolIndex`, the target columns, and any field that directly encodes
future failure will never enter the model. All normalization, feature selection,
and calibration are fitted using training tools only. Consecutive cycles from one
tool are never split randomly across training and test sets. History windows use
past cycles only.

This three-model comparison is important: if an “AI” model merely learns that the
150th cut is late in life, the age-only baseline will expose it.

## 7. Proposed system

The system has two clean layers:

```text
current/vibration + process context
                 ↓
 calibrated distribution of cycles remaining
                 ↓
 failure probability for the next queued job
                 ↓
 explicit production-cost policy
                 ↓
        CONTINUE or REPLACE
```

### Layer A — health and failure-risk model

#### Model A0: non-AI baselines

- replace after a fixed number of cycles selected on training tools;
- empirical survival curve conditioned on tool type/cutting condition;
- linear/Weibull age model.

#### Model A1: explainable classical ML

- XGBoost or LightGBM on the released 120 signal statistics;
- separate age-only, sensor-only, and full feature sets;
- SHAP values and feature-group ablations;
- quantile regression for lower, median, and upper RUL estimates.

This model should be finished first and remains a valid final model if it beats the
deep alternative.

#### Model A2: raw-signal deep model

1. Automatically locate the active cutting portion of each cycle.
2. Normalize each channel using training-tool statistics.
3. Use one compact 1D convolution/TCN encoder for the eight fast vibration
   channels and another for the twelve slower current channels.
4. Pool each encoder into a small vector and concatenate process metadata and,
   optionally, causal embeddings from the previous few cycles.
5. Predict median RUL and a lower/upper quantile, or a discrete probability over
   the next 0–160 cycles.

The model is explainable at the architecture level: convolutional filters detect
local waveform/frequency patterns, pooling summarizes the cut, and the final head
maps this health representation to remaining life. This is ambitious enough to be
substantive without inventing new ML theory.

#### Calibration

Quantile estimates will be corrected with **group-conformal calibration** using
whole calibration tools. The output presented to the policy will be a risk such as
“there is a 12% calibrated probability that this cutter will fail before a
three-cycle job completes,” not a false-precision claim such as “17.4 cycles
remain.” Deep ensembles are a secondary option if quantile calibration is not
stable.

### Layer B — production-aware replacement policy

At the start of each job, the policy sees:

- the calibrated RUL distribution;
- the next job's required number of milling cycles;
- part/scrap value and job criticality;
- planned change time and cost;
- unplanned failure downtime and recovery cost;
- due-date slack for the near-term queue.

For **REPLACE**, the policy pays tool and planned-change cost and starts with a new
tool. For **CONTINUE**, it pays ordinary production cost but accepts the predicted
risk of failure during the job. A short-horizon dynamic program or model-predictive
controller evaluates both branches and selects the lower expected cost. Every
decision can therefore show a calculation such as:

```text
Continue:  0.12 × (scrap + breakdown + delay) = 2.34 cost units
Replace:   new tool + planned change           = 1.60 cost units
Decision:  REPLACE
```

The primary study will use normalized cost units and a wide sensitivity grid
rather than inventing one “real” rupee value. If an industry contact later provides
actual tool, downtime, and scrap costs, they can be dropped into the same config.

### Where RL belongs

RL is **allowed but not required for the core claim**. Once the dynamic-programming
policy and simulator are validated, a constrained DQN or PPO policy can be trained
on the same state/action/reward definition and compared fairly. If RL does not beat
the transparent controller, that is a useful result. RL will not be used merely to
make the project look advanced.

### Where derating belongs

“Reduce cutting aggressiveness” is a stretch action because the primary dataset
does not vary feed and spindle speed within a tool lifecycle in a way that can
identify the causal effect of derating. We will add **CONTINUE AT REDUCED LOAD**
only if a degradation model can be supported by NASA's varying-condition data or
by a clearly stated mechanistic/simulation assumption. The complete core project
requires only CONTINUE and REPLACE.

## 8. Validation design

### 8.1 Prediction experiment

- Exclude the first-cycle-breakage outlier from normal training; retain it for a
  surprise-failure stress test.
- Use nested leave-one-tool-out evaluation on the remaining 13 tools.
- In each fold, reserve whole tools for training, calibration/model selection, and
  final testing; never reserve random cycles.
- Report results per tool as well as pooled, so one long trajectory cannot dominate.
- Add held-condition and held-tool-type stress tests where the data permit.

Prediction metrics:

- RUL MAE and RMSE;
- asymmetric early/late RUL score;
- probability-of-failure Brier score and calibration curve;
- 80%/90% interval coverage and interval width;
- failure-warning lead time;
- sensor-only improvement over the age-only model.

### 8.2 Decision experiment A — real lifecycle replay

For each held-out tool, replay its cycles in chronological order. The policy sees
only information available up to the current cycle and selects a stopping point.
Because the actual failure cycle is known, we can measure directly:

- whether the policy failed before replacement;
- how many usable cycles it discarded;
- percentage of observed tool life utilized;
- planned replacements versus failures;
- normalized cost and regret relative to a clairvoyant oracle.

This evaluation ends at the first replacement, so it does not require invented
post-replacement sensor data.

### 8.3 Decision experiment B — long-horizon production twin

A discrete-event simulator will create many-tool production episodes by
bootstrapping complete lifecycles from training data and generating transparent
job queues. Each synthetic job has a duration in cycles, value/criticality, and
due-date slack. The simulator will expose every assumed cost and random variable in
a configuration file.

Long-horizon metrics:

- total normalized cost per completed job;
- failure and premature-replacement rates;
- tool-life utilization;
- scrap, planned downtime, and unplanned downtime;
- throughput and tardiness;
- worst-case/CVaR cost, not just the average;
- regret versus a perfect-information oracle.

Stress tests will vary failure cost, tool-change time, job mix, sensor dropout,
noise, calibration error, and unfamiliar cutting conditions.

### 8.4 Policy baselines

The proposed system must beat strong, understandable alternatives:

1. replace at a conservative fixed age;
2. replace at the training-set median age;
3. age-only survival threshold;
4. point-RUL threshold without uncertainty;
5. calibrated one-step risk threshold;
6. production-aware dynamic program;
7. perfect-information oracle;
8. optional constrained RL policy.

## 9. Pre-declared success criteria

We should not choose the winner after seeing the plots. Before final testing, use
the following targets:

- the sensor model must improve RUL MAE or next-job failure Brier score by at least
  **10% over the age-only baseline**, or we must state honestly that the sensors did
  not add sufficient transferable information;
- a nominal 90% RUL interval should obtain **85–95% empirical coverage** on unseen
  tools;
- the final policy should reduce expected normalized cost by at least **10% over
  the best fixed-age baseline at an equal or lower failure rate** in the central
  scenario;
- the same policy should beat that baseline across at least **70% of the declared
  cost-sensitivity grid**, rather than at one hand-picked cost ratio;
- every headline number must come from a group-held-out tool, a real lifecycle
  replay, or a clearly labelled simulator result.

If the deep model loses to XGBoost, the project still succeeds with XGBoost as the
deployed model and the deep comparison reported transparently.

## 10. Final demonstration

The web application will replay a real held-out cutter cycle by cycle and show:

- recent vibration/current traces and sensor-health indicators;
- median remaining life plus calibrated uncertainty band;
- probability of surviving the next queued job;
- the next few jobs, their durations, values, and deadlines;
- expected CONTINUE and REPLACE costs;
- the chosen action and a plain-language explanation;
- what fixed-age, point-RUL, dynamic, and optional RL policies would do;
- the eventual observed failure point, without revealing it to the model in
  advance.

Interactive sliders for tool cost, failure cost, changeover time, and job value
will demonstrate why the correct decision changes even when the physical tool
state does not. A sensor-toggle panel will show whether full instrumentation,
spindle vibration only, or spindle current only is sufficient.

## 11. Twelve-week execution plan

| Week | Concrete output |
|---:|---|
| 1 | Download manifest, checksums, metadata audit, lifecycle plots, documented exclusions |
| 2 | Leakage-safe grouped split code; fixed-age, age-only, and empirical-survival baselines |
| 3 | XGBoost/LightGBM feature models; sensor/process/age ablations |
| 4 | Raw 25 GB ingestion, active-cut segmentation, cached training windows |
| 5 | Two-tower 1D-CNN/TCN model and initial leave-tool-out results |
| 6 | Quantile/distribution head, group-conformal calibration, failure-risk evaluation |
| 7 | Real lifecycle replay evaluator and point-policy baselines |
| 8 | Production digital twin, cost model, and dynamic-programming policy |
| 9 | Stress tests, minimal-sensor study, and failure-cost sensitivity map |
| 10 | Optional external-dataset transfer plus either RL or derating stretch—not both unless the core is stable |
| 11 | Polished interactive demo, experiment tables, explanations, and ablations |
| 12 | Reproducibility pass, report, presentation, video, and contingency buffer |

The team's required work is deliberately light: agree on the cost hierarchy and
demo scenario, review weekly outputs, understand the four explainable ideas
(signal features/1D convolutions, RUL, calibrated uncertainty, and expected-cost
policy), and prepare the presentation. Data engineering, model training,
simulation, testing, and application code can be handled in the repository.

## 12. Deliverables

1. Reproducible data download and preprocessing pipeline with checksums.
2. Dataset audit and leakage report.
3. Classical and raw-signal model training code.
4. Calibrated RUL/failure-risk models with model cards.
5. Real lifecycle replay evaluator.
6. Documented discrete-event production simulator.
7. Fixed-age, risk-threshold, dynamic-programming, oracle, and optional RL policies.
8. Interactive operator dashboard.
9. Final technical report, presentation figures, and five-minute demo scenario.
10. Automated tests and one-command experiment/demo instructions.

## 13. Main risks and honest fallbacks

| Risk | Why it matters | Planned response |
|---|---|---|
| Only 13 meaningful failure trajectories | A large deep network can memorize tools | Grouped evaluation, compact network, heavy ablation, classical model as a first-class result |
| Cycle count dominates RUL | The system could look intelligent without reading sensors | Mandatory age-only, sensor-only, and full-model comparison |
| Twenty sensors are unrealistic for deployment | A laboratory result may be too expensive to reproduce | Spindle-current-only and spindle-vibration-only models; quantify the accuracy/cost trade-off |
| Production economics are not present in the sensor data | Simulator results could be mistaken for factory savings | Separate real lifecycle replay from simulated multi-tool economics; use normalized costs and sensitivity ranges |
| Cross-dataset targets do not match | Naive pooling would create misleading labels | Use secondary datasets only for domain-shift or representation tests |
| Raw model does not beat feature boosting | Deep learning is not automatically superior on 968 cycles | Deploy the better calibrated model and explain why; retain the comparison |
| Derating effect is not identifiable | A three-action policy could be based on fiction | Keep derating out of the core unless external/mechanistic evidence supports it |

## 14. Final recommendation

Proceed with this project. It is mechanically grounded, has a newly released and
verified run-to-failure dataset, supports both classical and deep learning, and
ends in a real manufacturing decision rather than a prediction screenshot. Its
ambitious part is the complete chain—raw multi-sensor learning, uncertainty,
economic policy, honest validation, and an operator demo—not needless ML
complexity.

The correct core scope is:

> **calibrated RUL distribution + production-aware CONTINUE/REPLACE policy +
> leave-one-tool-out lifecycle replay.**

Raw-signal deep learning is a planned model, RL is a controlled comparison, and
derating/multimodal transfer are stretches. That combination is difficult enough
to be impressive but bounded enough to finish properly in two to three months.
