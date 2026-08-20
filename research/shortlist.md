# Ranked shortlist

The score is a project-selection score, not a claim about research-paper novelty.
Weights and hard gates are defined in `research-method.md`. Projects are ranked
for this team, this class landscape, and an 8–12 week build.

## Top 20

| Rank | Project | Score /100 | Decision produced | Verdict |
|---:|---|---:|---|---|
| 1 | **WeldSense: multimodal early defect warning + process rescue** | **91** | Warn, continue, stop, or recommend a feasible setting change during a weld | Best combination of mechanical depth, real multimodal data, demo quality, and explainable architecture |
| 2 | **FormTwin: simulation-to-real sheet-forming quality twin** | **89** | Choose forming settings and quantify real-part quality risk | Best niche mechanical-science project; unusually good 2026 sim-to-real data path |
| 3 | **MeasureLess: uncertainty-aware virtual metrology + adaptive inspection** | **89** | Measure or skip each part/wafer under a budget and drift | Most rigorous decision/evaluation story; less visually dramatic |
| 4 | **CADPlan: STEP-to-process-plan and DFM copilot** | **87** | Select operations, machines/tools, sequence, and redesign flags | Highest “wow” product; full-plan ground truth is the principal risk |
| 5 | **BornQualified-AM: melt-pool quality twin + experiment planner** | **86** | Select scan settings, measure next, or stop a risky build | Excellent NIST data and research depth; data integration is heavy |
| 6 | **SupplyGraph Resilience: ripple forecast + mitigation optimizer** | **86** | Dual-source, expedite, reallocate capacity, or change inventory | Strong data and graph/RL story, but overlaps the class LLM shock proposal |
| 7 | **ChangeGraph: engineering-change impact copilot** | **84** | Identify affected parts, suppliers, process plans, inspections, and documents | Distinctive digital-thread problem; end-to-end labels must be simulated |
| 8 | **ShiftProof Quality Gate: anomaly detection + conformal reinspection** | **83** | Accept, reject, or send to human review under lighting/domain shift | Extremely buildable and measurable, but visual anomaly detection is crowded |
| 9 | **MoldRx: injection-molding quality + counterfactual settings** | **82** | Reject/accept and recommend a low-risk setting adjustment | Clear process story and easy data; public datasets are smaller |
| 10 | **ForgeRx: radial-forging virtual quality and CMM predictor** | **82** | Change thermal/stroke settings and select parts for CMM | Strong mechanical identity; only 81 real forged parts in the main dataset |
| 11 | **TraceGraph: cross-stage lot genealogy and causal containment** | **81** | Contain affected lots and rank the causal process stage | High industrial value; realistic public linked-stage datasets are scarce |
| 12 | **PickTwin: adaptive warehouse batching, routing, and workload balance** | **81** | Batch orders and route pickers/AGVs as orders change | New real manufacturing warehouse dataset and polished simulator potential |
| 13 | **RecoverAI: value-aware product disassembly sequence planner** | **80** | Choose a collision-free sequence maximizing recovered value | Memorable circular-manufacturing demo; needs synthetic graph/condition labels |
| 14 | **ToolLife Policy: calibrated wear + production-aware replacement** | **80** | Continue, derate, or replace the tool | Better than ordinary RUL, but maintenance remains a crowded category |
| 15 | **AFP Guard: composite-placement geometric quality decision system** | **79** | Repair, rework, or change fiber-placement parameters | Niche, mechanical, and visual; dataset/ecosystem smaller than welding or AM |
| 16 | **EnergyFlow: tariff/carbon-aware production and utility scheduling** | **79** | Shift production loads while preserving due dates | Clear operational savings; the AI contribution can be overshadowed by optimization |
| 17 | **CellBirth: early battery-cell quality and formation policy** | **78** | Grade cells early and adapt formation/testing | Important manufacturing problem; public data alignment and electrochemistry burden are high |
| 18 | **ErgoTwin: personalized assembly ergonomics + task redesign** | **78** | Coach posture, redesign station/task, or reallocate work | Good human-centered demo; privacy and generalization must be handled carefully |
| 19 | **ChatterGuard: milling chatter prediction + adaptive feed control** | **77** | Adjust feed/spindle parameters online | Mechanically clean, but closed-loop validation without a machine needs a credible simulator |
| 20 | **HeatTreat-BO: recipe surrogate + constrained Bayesian optimization** | **76** | Select a furnace recipe under hardness, distortion, time, and energy limits | Teachable and useful; suitable open process-property datasets are less standardized |

## Detailed weighted scorecard for the six finalists

| Project | Value /15 | AI /10 | Diff. /15 | Data /15 | Eval /10 | Demo /10 | Explain /10 | Execution /10 | Fallback /5 | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WeldSense | 15 | 10 | 13 | 13 | 9 | 10 | 9 | 8 | 4 | **91** |
| FormTwin | 14 | 9 | 14 | 12 | 9 | 9 | 9 | 9 | 4 | **89** |
| MeasureLess | 15 | 9 | 13 | 12 | 10 | 8 | 10 | 8 | 4 | **89** |
| CADPlan | 14 | 10 | 13 | 11 | 8 | 10 | 9 | 8 | 4 | **87** |
| BornQualified-AM | 15 | 10 | 13 | 12 | 8 | 10 | 8 | 6 | 4 | **86** |
| SupplyGraph Resilience | 15 | 10 | 12 | 14 | 9 | 9 | 8 | 6 | 3 | **86** |

## 1. WeldSense — recommended flagship

### Problem

Most student welding projects inspect a completed bead image. By then, the part is
already defective. WeldSense asks a better question: **how early can a weld be
identified as high-risk, how certain is that warning, and what feasible process
change would reduce predicted risk?**

### End-to-end system

1. Synchronize short windows of video, audio, current/voltage, and process settings.
2. Encode each modality with an understandable specialist:
   - small 2D/3D CNN or pretrained video encoder;
   - log-mel spectrogram CNN;
   - 1D temporal CNN for electrical signals;
   - MLP for settings and material/thickness metadata.
3. Fuse the four embeddings with late fusion or gated attention.
4. Predict defect class/risk at 25%, 50%, 75%, and 100% of the weld.
5. Calibrate confidence with conformal prediction or temperature scaling; defer
   when risk is uncertain.
6. Train a separate response surrogate relating settings and observed state to
   defect risk. A constrained search proposes candidate current, voltage, gas, or
   travel-speed adjustments. It is presented as an **offline recommendation**, not
   a proven causal intervention.
7. A grounded LLM may explain the model output and retrieve welding-process
   guidance, but it never invents sensor values or bypasses the constraint engine.

### Why AI is actually needed

Defects manifest differently and at different times across sound, arc appearance,
electrical stability, and final geometry. Fixed thresholds cannot model those
cross-modal interactions or generalize cleanly across weld types and settings.

### Evaluation

- Grouped splits by welding session and, where possible, unseen parameter ranges.
- Macro-F1/AUPRC at 25/50/75/100% completion.
- Detection lead time and fraction of defects caught before completion.
- Expected calibration error, conformal coverage, and risk-versus-coverage curves.
- Modal ablations: electrical only, audio only, video only, all modalities.
- Domain tests by thickness, steel type, weld type, and session.
- Offline recommendation feasibility and predicted improvement, clearly separated
  from claims requiring a physical welding trial.

### Demo

A weld timeline plays while modality traces update. The system shows live defect
risk, uncertainty, influential time windows/modalities, and a constrained “what
if current/voltage/speed changed?” panel.

### Risks and fallbacks

- Intel access is gated and the research license requires a real identity.
- Labels may be noisy and modalities slightly misaligned.
- If Intel access is delayed, the project starts on the public high-frequency
  current/voltage and thermographic datasets. A strong electrical/thermal early
  warning system remains a complete fallback.
- The parameter recommender is evaluated offline unless a validated process
  simulator or physical experiment becomes available.

## 2. FormTwin — strongest niche mechanical alternative

### Problem and system

Finite-element forming simulations are expensive and do not perfectly reproduce
the factory. FormTwin learns a fast surrogate from simulated forming signals,
adapts it using limited real press data, predicts dimensional/defect outcomes,
quantifies the simulation-to-reality gap, and recommends settings with constrained
Bayesian optimization.

The teachable architecture is simulation features/time-series → small temporal
encoder or gradient-boosted model → quality outputs, plus a Gaussian-process or
ensemble residual corrector trained on real parts.

### Evaluation

- Simulator-only accuracy.
- Zero-shot sim-to-real error.
- Error versus 1, 5, 10, … real calibration parts.
- Uncertainty coverage and detection of out-of-distribution material/process cases.
- Surrogate speedup over simulation.
- Parameter-search improvement subject to thinning/split/springback constraints.

### Why it is unusually good

It is visibly mechanical, the ML remains simple, the novelty is the reality-gap
experiment and decision loop, and the 2026 public dataset was built for exactly
this question. The main contingency is dataset documentation/tooling maturity.

## 3. MeasureLess — strongest scientific evaluation

### Problem and system

Physical metrology is slow and expensive, so not every item is measured. A virtual
metrology model predicts the missing measurement and its uncertainty. A policy
then decides whether each item should be physically measured, balancing quality
risk against inspection cost while detecting drift.

An online Gaussian process is the clean baseline. Gradient boosting or a small
sequence model can be the predictive comparator. Inspection policies include
periodic, random, uncertainty threshold, cost-aware threshold, and a contextual
bandit/RL extension.

### Evaluation

Replay the process stream with controlled drift and report measurement reduction,
RMSE, tolerance escapes, detection delay, regret/cost, and calibration coverage.
This evaluates the manufacturing decision—not merely prediction error.

### Differentiation and limitation

The project is a rigorous extension/reproduction of a current NIST direction,
not a claim that adaptive virtual metrology itself is new. A meaningful extension
would use multiple quality characteristics, changing inspection budgets, and
cost-sensitive safe abstention.

## 4. CADPlan — highest product/demo ambition

### Problem and system

Given a STEP part, CADPlan should identify manufacturing features, choose a
candidate operation sequence, flag infeasible/expensive geometry, estimate a cost
range, and explain the plan visually.

- OpenCascade or equivalent parses STEP/B-Rep geometry.
- A face-adjacency GNN segments pockets, holes, slots, steps, and other features.
- A transparent constraint/rule engine filters machine, tool, setup, and approach
  directions.
- A graph/sequence policy or optimizer orders operations.
- A grounded LLM converts the validated plan into an explanation and uses tools
  for lookups; it cannot override geometry constraints.

### Evaluation

Feature IoU/F1 on MFCAD++; plan constraint-violation rate; operation coverage;
cycle-time/cost error on synthetic or available job records; comparison with a
rule-only baseline; and expert-style failure cases for inaccessible features,
tight tolerances, or machine-envelope violations.

### Principal risk

Feature labels are abundant, but public end-to-end process plans and real CNC
quotations are not. The system can still be excellent, but “cost accuracy” must
not be faked. The fallback is feature recognition + rule-valid DFM + transparent
parametric cost ranges.

## 5. BornQualified-AM — ambitious data-rich alternative

### Problem and system

Fuse thermal/process monitoring with post-build quality, predict whether a scan or
layer will meet quality targets, calibrate uncertainty, and use Bayesian
optimization to choose the next scan-parameter experiment. A dashboard visualizes
the build, thermal history, predicted defect map, uncertainty, and parameter
tradeoffs.

### Risk

NIST data are high quality but spread across experiments and measurement systems.
Data engineering and physical interpretation—not ML complexity—are the critical
path. It is a strong selection only if the chosen NIST challenge has a clean
input/output join after a one-week spike.

## 6. SupplyGraph Resilience — technically strong but strategically secondary

Represent the multi-tier product/supplier network as a temporal graph, forecast
production/transaction changes, inject shocks in SupplySim, and compare mitigation
policies such as dual sourcing, expediting, capacity shifts, and safety stock.
Evaluate fulfilled demand, recovery time, cost, and robustness on unseen graphs.

This is valid applied GNN/RL work. It ranks below the five flagships because the
class sheet already contains an LLM supply-shock project. It should be selected
only if we explicitly want to beat that idea with a quantitative, non-theatrical
system.

## Projects intentionally not recommended as flagships

- Generic RUL on C-MAPSS.
- MFCC/spectrogram machine-sound anomaly detection.
- Standard MVTec defect classification or segmentation.
- Job-shop PPO without a strong operations-research baseline.
- RAG over maintenance manuals without a predictive/diagnostic engine.
- A dashboard called a digital twin that has no live state estimator, uncertainty,
  counterfactual, or control decision.
- LLM agents role-playing suppliers without a calibrated network model and
  measurable mitigation policy.
