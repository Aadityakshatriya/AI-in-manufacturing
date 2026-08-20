# Fifteen additional detailed project charters

These are additional to WeldSense, FormTwin, MeasureLess, CADPlan, and
BornQualified-AM. Each is framed as a complete manufacturing decision system,
not as an isolated prediction notebook.

## Comparative ranking

“Readiness” describes the data and validation path, not model simplicity.

| Rank | Project | Score /100 | Readiness | Core manufacturing decision |
|---:|---|---:|---|---|
| 1 | **MoldRx — injection-molding defect twin and constrained recipe tuner** | 91 | A | Accept/reject a part and choose the next safe process recipe |
| 2 | **PackRecover — EV battery-pack disassembly and value-recovery planner** | 89 | A− | Choose the safest, highest-value next disassembly operation |
| 3 | **AssemblyGuard — multimodal assembly error detection and recovery** | 88 | A− | Detect a skipped/wrong step and recommend the correct recovery step |
| 4 | **ShiftProof — calibrated quality inspection under domain shift** | 87 | A | Accept, reject, or reinspect under changing visual conditions |
| 5 | **AFP-Guard — automated-fiber-placement geometric quality controller** | 86 | A− | Repair/rework a tow or alter placement parameters |
| 6 | **DrawInspect — drawing/PMI-to-inspection-plan copilot** | 85 | B+ | Select characteristics, instruments, order, and sampling frequency |
| 7 | **ChangeGraph — engineering-change impact and evidence graph** | 84 | B | Approve a change and identify every downstream affected artifact |
| 8 | **ToolLife Policy — production-aware tool replacement** | 84 | A | Continue, derate, or replace a cutting tool |
| 9 | **SafeCell — predictive human–robot safety twin** | 83 | A− | Continue, slow, reroute, or stop the robot before a near miss |
| 10 | **PickTwin — dynamic warehouse picking and workload twin** | 82 | A | Batch orders and route workers/AGVs as the system changes |
| 11 | **ReworkPolicy — causal lot-rework decision engine** | 82 | B | Rework or release a lot based on expected treatment effect |
| 12 | **CellBirth — early battery-cell qualification and test allocation** | 81 | B+ | Grade early, continue formation, or allocate further testing |
| 13 | **EnergyFlow — energy/carbon-aware factory scheduler** | 80 | B+ | Reschedule flexible loads without breaking due dates |
| 14 | **SpareLink — maintenance-driven spare-parts inventory policy** | 80 | B+ | Stock, pool, repair, or expedite a critical part |
| 15 | **FactoryRecovery — fault diagnosis and safe recovery-policy twin** | 79 | A− | Diagnose a process upset and select a validated recovery action |

## 1. MoldRx — injection-molding defect twin and constrained recipe tuner

### Manufacturing problem and decision

Injection-molding defects such as flash, short shots, voids, flow marks, weld
lines, and air traps depend on interacting settings. MoldRx sees the produced part
and recipe, quantifies each defect, decides whether the part is acceptable, and
proposes the next process recipe under machine and quality constraints.

### Why AI is justified

The image-to-defect mapping is a perception problem, while the nonlinear relation
between six process variables and multiple competing defects is difficult to
encode with fixed rules. Ordinary optimization still handles the final constrained
search; AI supplies the defect measurements and response surface.

### Teachable architecture

1. U-Net/YOLO segmentation for ten defect classes.
2. Gradient boosting or a small MLP mapping temperature, injection/holding
   pressure, times, and back pressure to defect areas, viability, energy, and
   cycle time.
3. SHAP/partial-dependence analysis for process understanding.
4. Conformal intervals or ensembles for uncertainty.
5. Pareto/constrained Bayesian optimization for the next recipe.

The 2026 [open injection-molding dataset](https://doi.org/10.5281/zenodo.20322729)
contains 1,000 controlled parameter configurations, high-resolution images,
pixel-level masks and COCO annotations for ten defect types, quantified defect
areas, process variables, and the mold STEP model. A [companion dataset](https://doi.org/10.5281/zenodo.20309380)
adds part weights, energy, and cycle time.

### Evaluation

- Segmentation mAP/IoU per defect and per held-out recipe region.
- Defect-area MAE, viability AUPRC, and uncertainty coverage.
- Leave-parameter-region-out testing rather than a random image split.
- Predicted Pareto improvement in quality, energy, and cycle time.
- Comparison with default recipe, one-factor-at-a-time tuning, random search, and
  optimizer without image feedback.

### Demo, risk, and bounded build

The app displays the part image/CAD, overlays defects, exposes recipe sliders, and
updates predicted defects, energy, time, uncertainty, and the Pareto frontier.
The dataset's associated work already studies closed-loop tuning, so the honest
course contribution is a reproducible multimodal extension with uncertainty,
held-out-region testing, and an operator-grade interface—not claiming the idea is
scientifically unprecedented. If segmentation is difficult, quantified defect
areas and process variables still support a complete recipe-tuning fallback.

## 2. PackRecover — EV battery-pack disassembly and value-recovery planner

### Manufacturing problem and decision

An end-of-life battery pack is not simply assembled in reverse. Components may be
damaged, missing, stuck, hazardous, or worth different amounts. PackRecover chooses
the next feasible disassembly action to maximize recovered value while minimizing
time, tool changes, collision, and safety risk.

### Why AI is justified

The pack is naturally a graph of components, fasteners, precedence, accessibility,
and visibility. Conditions are uncertain and each removal changes the next state.
That supports an explainable GNN plus sequential planner/RL rather than forcing AI
onto a flat table.

### Teachable architecture

1. Heterogeneous product graph with component, connection, tool, hazard, condition,
   and value attributes.
2. Message-passing GNN predicts removability, operation time, failure/stuck risk,
   and recovered value.
3. Beam search, Monte Carlo tree search, or PPO selects a sequence under hard
   precedence/safety constraints.
4. A POMDP-style extension updates beliefs after a missing or stuck component.
5. Rule validator prevents impossible actions; the LLM only narrates the plan.

A new [KIT battery-pack disassembly knowledge-graph dataset](https://publikationen.bibliothek.kit.edu/1000196148)
contains product structures, real disassembly sequences, and component visibility
for ten EV battery packs including BMW, Hyundai, Volvo, and Fiat designs. A
[gear-pump robotic disassembly dataset](https://doi.org/10.25500/edata.bham.00000810)
provides a second multiobjective planning case.

### Evaluation

- Leave-one-pack-design-out generalization.
- Sequence feasibility, safety-rule violations, total time/tool changes, recovered
  value, and Pareto hypervolume.
- Robustness to stuck, damaged, and missing components.
- Comparison with reverse-assembly, greedy value, shortest-time, rule search, and
  graph/RL policies.

### Demo, risk, and bounded build

An interactive graph/3D-lite view removes components step by step, explains why an
action is available, and lets the user introduce corrosion or missing parts. Ten
pack designs are not enough for an enormous model, which is an advantage for
explainability. Training cases can be expanded with valid subgraphs and simulated
conditions. The fallback is a graph optimizer with learned time/risk estimates;
the project does not depend on controlling a physical robot.

## 3. AssemblyGuard — multimodal assembly error detection and recovery

### Manufacturing problem and decision

Assembly systems usually recognize the current action but do not understand a
flexible procedure well enough to detect a skipped step, wrong tool, wrong order,
or corrective action. AssemblyGuard estimates the procedural state and recommends
the smallest valid recovery path.

### Why AI is justified

Actions are ambiguous in a single camera view and real workers take alternative
paths. Video, pose, hands, tools, IMUs, depth, and narration provide complementary
evidence. A purely fixed sequence breaks as soon as a worker pauses, backtracks,
or performs two actions concurrently.

### Teachable architecture

1. Pretrained video/pose encoder plus compact IMU encoder.
2. Late fusion into step probabilities and tool/object state.
3. Procedure graph or hidden-state model constrains legal transitions.
4. Sequence model predicts the next valid step and flags unlikely transitions.
5. Shortest-path search produces a recovery plan; grounded RAG displays the
   relevant work-instruction fragment.

[OpenMarcie](https://openaccess.thecvf.com/content/CVPR2026/papers/Bello_OpenMarcie_Dataset_for_Multimodal_Action_Recognition_in_Industrial_Environments_CVPR_2026_paper.pdf)
contains eight modalities, synchronized wearable/egocentric/exocentric sensing,
overlapping action labels, and 36 volunteers performing bicycle and 3D-printer
assembly/disassembly. [IMPACT](https://arxiv.org/abs/2604.10409) emphasizes
incomplete observations, flexible paths, and corrective behavior; [IndEgo](https://indego-dataset.github.io/)
adds industrial assembly, inspection, repair, and logistics footage.

### Evaluation

- Subject-held-out step/action F1 and transition accuracy.
- Error-detection delay for synthetically masked, swapped, or skipped steps.
- Recovery-plan validity and edit distance to a legal procedure.
- Calibration and abstention on ambiguous states.
- Ablations for camera, wearable, pose, tool detection, and procedure graph.

### Demo, risk, and bounded build

The demo plays an assembly, highlights recognized hands/tools/step, shows procedure
progress, and injects a skipped or wrong operation. The principal risk is that
real error labels may be sparse. The defensible fallback constructs errors by
editing legal sequences while evaluating perception only on real footage. No robot
policy or VLA fine-tuning is required for the core project.

## 4. ShiftProof — calibrated quality inspection under domain shift

### Manufacturing problem and decision

A model trained under one lighting setup often fails after a camera, illumination,
surface finish, or product variant changes. ShiftProof makes the operational
decision—accept, reject, or reinspect—while explicitly measuring uncertainty and
shift.

### Why AI is justified

Rare or novel defects cannot be exhaustively enumerated, and high-resolution
texture deviations are hard to express as hand-built rules. The worthwhile
research problem is safe deployment, not another benchmark classifier.

### Teachable architecture

1. PatchCore or pretrained-feature anomaly detector.
2. Optional segmentation refinement for anomaly location.
3. Shift detector on embeddings/illumination statistics.
4. Temperature scaling, conformal prediction, or deep ensembles.
5. Cost-sensitive gate chooses accept/reject/reinspect using false-escape and
   review costs.

[MVTec AD 2](https://www.mvtec.com/research-teaching/datasets/mvtec-ad-2) has
8,000+ high-resolution images across eight difficult industrial scenarios and
deliberately tests lighting conditions outside training; part of the ground truth
is evaluated only through the official server. [MVTec LOCO AD](https://www.mvtec.com/research-teaching/datasets/mvtec-loco-ad)
adds logical as well as structural anomalies.

### Evaluation

- AUROC/AUPRO and pixel localization.
- Calibration error and conformal coverage.
- Selective risk versus percentage automatically handled.
- False escapes, false rejects, human-review load, and total expected cost.
- Clean, known-lighting-shift, unknown-shift, and cross-category splits.

### Demo, risk, and bounded build

The dashboard lets users alter lighting/contrast or switch domains and watch the
model detect shift, expand uncertainty, and route marginal parts to reinspection.
It is the most reliable project technically, but also the most crowded. It is a
flagship only if the decision/calibration layer is central; plain PatchCore or
YOLO results are insufficient.

## 5. AFP-Guard — automated-fiber-placement geometric quality controller

### Manufacturing problem and decision

Automated fiber placement can create gaps, overlaps, wrinkles, twists, and tow
misalignment. AFP-Guard processes the streaming laser profile and robot path,
locates geometric defects, and recommends continue, pause, repair, or parameter
adjustment.

### Why AI is justified

Laser profiles contain structured but noisy 3D geometry that changes with path,
layer, and local curvature. Static thresholds become fragile, while defects are
rare and expensive to label.

### Teachable architecture

1. Align timestamped robot poses with laser-line profiles.
2. Convert profiles into height/deviation maps.
3. 1D/2D CNN or autoencoder detects anomalous geometry.
4. Geometry layer measures gap width, overlap, tow angle, and confidence.
5. Rule/constrained optimizer maps defect severity to repair/rework actions.

The [open AFP dataset and code](https://doi.org/10.5281/zenodo.17048470) provide
timestamped robot-controller data and laser profiles for a cross-ply laminate,
with an 8.6 MB archive and public processing implementation. Earlier [laser-profile
AFP research](https://arxiv.org/abs/1910.04997) supports synthetic-defect
augmentation.

### Evaluation

- Defect detection/localization and geometric measurement error.
- Leave-pass/layer-out generalization.
- Robustness to profile noise, missing lines, alignment error, and novel defect size.
- Detection delay and amount of avoidable defective tow length.
- Rule thresholds versus learned anomaly model versus hybrid.

### Demo, risk, and bounded build

Visualize the laminate growing pass by pass, the laser cross-section, defect heat
map, measured gap/overlap, and recommended repair. The primary dataset is small;
synthetic geometry and physics/rule-based defect injection must be an explicit
part of the design. The fallback is a transparent geometric QA pipeline plus a
learned robustness layer.

## 6. DrawInspect — engineering drawing/PMI to inspection plan

### Manufacturing problem and decision

Inspection planning requires finding every critical dimension/tolerance, mapping
it to measurable features and datum references, choosing CMM/probe/gauge methods,
sequencing measurements, and deciding sampling frequency. DrawInspect converts a
2D drawing or STEP-with-PMI into a validated draft inspection plan.

### Why AI is justified

Drawings mix geometry, symbols, text, tables, and implicit relationships. AI is
useful for extraction and association; deterministic geometry/GD&T rules and an
optimizer must own plan validity.

### Teachable architecture

1. OCR/object detector or VLM extracts dimensions, feature-control frames, datum
   symbols, surface finish, and notes from 2D drawings.
2. STEP parser extracts semantic PMI when available.
3. Bipartite graph links requirements to geometric features/datums.
4. Rules assign candidate instruments and accessibility constraints.
5. Optimizer sequences measurements to reduce setups/probe changes.
6. Uncertainty sends ambiguous annotations to human review.

[NIST D2MI](https://www.nist.gov/ctl/smart-connected-systems-division/smart-connected-manufacturing-systems-group/enabling-digital-0)
demonstrated CAD-with-PMI flow into CAM and CMM, while [NIST STEP/PMI models](https://catalog.data.gov/dataset/nist-cad-models-and-step-files-with-pmi)
provide public test parts.

### Evaluation

- Annotation/entity F1 and dimension-to-feature association accuracy.
- Requirement coverage, datum-chain validity, and impossible-measurement rate.
- Setup/probe changes and travel compared with rule/manual sequences.
- Drawing-to-STEP consistency checks.
- Human-review rate under calibrated confidence.

### Demo, risk, and bounded build

Upload a drawing/STEP file, click any GD&T callout, view the referenced 3D feature,
and inspect the generated measurement sequence. The biggest risk is limited public
gold-standard CMM plans. The fallback evaluates extraction/association on public
models and validates plans against a deterministic synthetic CMM environment.

## 7. ChangeGraph — engineering-change impact and evidence graph

### Manufacturing problem and decision

A design change can silently affect BOMs, suppliers, process plans, tooling,
inspection programs, inventory, work instructions, and certifications. ChangeGraph
predicts the impact set, ranks required reviews, and supplies an evidence path for
every claimed dependency.

### Why AI is justified

The data form a heterogeneous graph, dependencies may be indirect, and relevant
evidence is spread across structured records and documents. A GNN can rank likely
impacts; retrieval/LLM can explain them. Neither should replace deterministic
known-dependency traversal.

### Teachable architecture

1. Synthetic-but-realistic digital thread linking requirements, CAD features,
   parts, BOM, operations, machines, tools, controls, suppliers, and documents.
2. Graph rules produce guaranteed direct impacts.
3. Relational GNN ranks indirect or historical change propagation.
4. RAG retrieves supporting document fragments.
5. Evidence validator requires a graph path and citation for every recommendation.

The [NIST digital-thread roadmap](https://www.nist.gov/publications/roadmap-strengthen-us-manufacturing-supply-chain-digital-thread-technology)
identifies interoperability, traceability, causal analytics, and lifecycle links
as manufacturing priorities; [NIST's digital-thread testbed](https://www.nist.gov/ctl/smart-connected-systems-division/smart-connected-manufacturing-systems-group/enabling-digital)
connects engineering, manufacturing, quality, and supply-chain information.

### Evaluation

- Direct/indirect impact precision and, more importantly, recall.
- Evidence-path validity and hallucination rate.
- Leave-change-type and leave-subassembly-out generalization.
- Review effort saved at fixed missed-impact risk.
- Graph rules versus GNN versus hybrid versus LLM-only.

### Demo, risk, and bounded build

Change a tolerance, material, supplier, or CAD feature and watch affected nodes and
documents light up with reasons. Public end-to-end change histories are scarce, so
the ground truth must be generated from a transparent digital-thread simulator.
This is acceptable if the simulator and evaluation are first-class artifacts and
the project does not pretend synthetic labels are factory evidence.

## 8. ToolLife Policy — production-aware cutting-tool replacement

### Manufacturing problem and decision

Predicting flank wear is not the actual factory decision. ToolLife Policy chooses
continue, reduce aggressiveness, or replace the tool based on uncertain wear,
remaining jobs, due dates, changeover time, part value, and scrap risk.

### Why AI is justified

Force, vibration, acoustic emission, and sound encode wear nonlinearly. A policy
must translate uncertain health into asymmetric economic consequences; a fixed
wear threshold ignores the production context.

### Teachable architecture

1. Handcrafted signal statistics + gradient boosting as the transparent baseline.
2. 1D CNN on force/vibration/AE windows as the deep model.
3. Survival/RUL head with calibrated interval.
4. Discrete-event production simulator with tool wear and job values.
5. Dynamic programming or constrained RL selects the replacement policy.

The PHM 2010 milling data, indexed through the [PHM Society repository](https://data.phmsociety.org/),
include tri-axial force/vibration, acoustic emission, cutting conditions, and
microscope wear. A newer [multi-feature whole-life tool-wear dataset](https://www.nature.com/articles/s41597-024-04345-2)
adds image, force, torque, sound, and vibration modalities.

### Evaluation

- Wear MAE and interval coverage on leave-tool-out splits.
- Early/late replacement rate, avoided scrap, downtime, throughput, and total cost.
- Robustness to new tools/materials and sensor dropout.
- Threshold, periodic replacement, oracle, model-predictive, and RL policies.

### Demo, risk, and bounded build

Show live sensor traces, health distribution, queued jobs, and the economic reason
for continuing or replacing. Logged data cannot validate the production policy
directly, so all economic claims must come from a documented simulator. The
fallback is uncertainty-aware wear/RUL plus a deterministic cost policy.

## 9. SafeCell — predictive human–robot safety twin

### Manufacturing problem and decision

Most safety vision systems detect that a person is already inside a danger zone.
SafeCell predicts short-horizon human motion and collision risk, then chooses
continue, slow, reroute, or stop while limiting nuisance interventions.

### Why AI is justified

Human intent and motion are uncertain, occluded, and temporally structured. Robot
geometry and safety constraints remain deterministic; AI estimates future human
occupancy and its uncertainty.

### Teachable architecture

1. Person/pose tracking from video or depth.
2. Small temporal transformer/LSTM predicts a distribution over future joints or
   occupied regions.
3. Robot trajectory and human distribution produce time-to-collision risk.
4. Rule-based safety shield enforces minimum separation and speed limits.
5. Cost-aware controller selects continue/slow/reroute/stop.

The [UR10 human–robot dataset](https://orda.shef.ac.uk/articles/dataset/A_Vision_Data_Repository_for_Human-UR10_Robot_Interactions_in_Manufacturing/16669315)
contains 12.95 GB of real and digital-twin interaction video. A separate [factory
safe/unsafe behavior dataset](https://doi.org/10.1016/j.dib.2024.110791) contains
691 high-resolution clips across eight behavior classes.

### Evaluation

- Trajectory/occupancy error and collision-risk calibration.
- Near-miss recall at fixed false-stop rate.
- Warning horizon, robot idle time, and throughput.
- Real-to-synthetic and subject/viewpoint generalization.
- Reactive zone, constant-velocity, learned prediction, and oracle comparisons.

### Demo, risk, and bounded build

Reconstruct a 2D/3D workcell and display predicted human occupancy, robot path, and
safety action. This is decision support/simulation, not a certified safety system.
The fallback uses recorded robot paths and evaluates the safety policy offline;
physical cobot control is explicitly out of scope.

## 10. PickTwin — dynamic warehouse picking and workload twin

### Manufacturing problem and decision

Static shortest paths ignore order arrivals, batching, congestion, picker skill,
fatigue/workload, storage policy, and urgent production demand. PickTwin jointly
batches orders, assigns workers/AGVs, and routes them as conditions change.

### Why AI is justified

Optimization ensures feasibility, but learned travel/service-time estimates and a
policy can adapt to stochastic arrivals and worker differences. A plain demand
forecast is not enough; the output is a dispatch decision.

### Teachable architecture

1. Warehouse graph from CAD/layout and storage coordinates.
2. Gradient boosting forecasts pick/service time from location, product, operator,
   load, and time context.
3. Mixed-integer/heuristic optimizer handles batching and initial routes.
4. RL or rolling-horizon policy adapts routes after new orders/congestion.
5. Fairness constraint limits workload imbalance.

A 2025 [real footwear-manufacturing warehouse dataset](https://doi.org/10.1016/j.dib.2025.111837)
contains WMS orders, product classes and locations, operator/temporal performance,
CAD layouts, routing paths, and Python scripts.

### Evaluation

- Travel distance, lateness, throughput, congestion, and workload variance.
- Replay of chronological days; no random order-row split.
- Unseen demand surges and blocked-aisle shocks.
- Nearest-neighbor, S-shape, static optimization, and adaptive policy baselines.

### Demo, risk, and bounded build

Animate workers/AGVs on the actual layout while users inject an urgent order or
aisle blockage. RL is optional: a rolling-horizon learned-time optimizer is already
a complete project. This avoids spending the schedule tuning a policy that cannot
beat operations-research baselines.

## 11. ReworkPolicy — causal lot-rework decision engine

### Manufacturing problem and decision

A low intermediate quality score does not imply that rework will help. Rework can
improve some lots, damage others, consume capacity, and delay final inspection.
ReworkPolicy estimates the individual treatment effect and chooses rework only
when expected yield gain exceeds cost and uncertainty.

### Why AI is justified

This is a causal intervention question, not ordinary classification. Predicting
final yield under observed historical decisions can reproduce operator bias;
double/debiased ML estimates how outcomes would differ under rework versus no
rework, given explicit assumptions.

### Teachable architecture

1. Outcome model and treatment-propensity model using gradient boosting.
2. Doubly robust or double-ML conditional treatment effect.
3. Overlap diagnostics and sensitivity analysis for hidden confounding.
4. Policy chooses rework/release with uncertainty and capacity constraints.
5. Optional contextual bandit simulation studies online learning.

[Published causal manufacturing work](https://arxiv.org/abs/2406.11308) reports a
2–3% yield improvement for a real LED color-conversion rework decision, providing
a strong problem formulation and baseline.

### Evaluation

- Semi-synthetic benchmark with known treatment effects.
- Policy value, regret, yield, rework volume, capacity usage, and cost.
- Propensity overlap, covariate balance, placebo tests, and sensitivity curves.
- Naive yield predictor, always/never rework, historical policy, uplift trees, and
  doubly robust policy.

### Demo, risk, and bounded build

The interface shows two potential-outcome estimates, uncertainty, important
covariates, and how cost/capacity changes the policy. The original factory data
are proprietary, so a transparent semi-synthetic generator based on a multistage
process is mandatory. The project must present its causal assumptions explicitly;
otherwise it becomes an unjustified counterfactual demo.

## 12. CellBirth — early battery-cell qualification and test allocation

### Manufacturing problem and decision

Formation and cycling are slow. CellBirth predicts later capacity, resistance,
stability, or failure risk from early formation data and manufacturing metadata,
then chooses grade, continue testing, or allocate an additional diagnostic cycle.

### Why AI is justified

Early voltage/current trajectories contain subtle signatures spread across time,
and quality depends on synthesis, coating, assembly, and formation conditions.
Uncertainty matters because an incorrect early release is costly.

### Teachable architecture

1. Curve features + gradient boosting baseline.
2. 1D CNN or compact transformer for early cycling curves.
3. Multitask heads for capacity/resistance and failure risk.
4. Conformal intervals and out-of-distribution checks by chemistry/batch.
5. Active-testing policy chooses whether another cycle/measurement is worth its
   time and energy.

The [high-throughput sodium-ion dataset](https://doi.org/10.5281/zenodo.7981010)
links synthesis, screen-printed electrode coating, robotic assembly, formation,
and cycling. The [DOE Battery Data Hub](https://batterydata.nrel.gov/) supplies
additional public cell-test data for transfer experiments.

### Evaluation

- Later-life quality error using only the first N cycles.
- Batch/chemistry-held-out performance and calibration.
- Test-time/energy saved versus false-release/false-scrap cost.
- Feature, 1D CNN, transformer, and full-history oracle comparisons.

### Demo, risk, and bounded build

Plot early curves, predicted end quality, confidence, batch context, and the value
of one more test cycle. The manufacturing metadata may not align across external
battery datasets, so one dataset is primary and others are only transfer tests.
The fallback is early prediction plus a deterministic confidence-based testing
policy.

## 13. EnergyFlow — energy/carbon-aware factory scheduler

### Manufacturing problem and decision

Factories have flexible and inflexible loads, production due dates, startup costs,
thermal constraints, electricity prices, and carbon intensity. EnergyFlow moves
eligible operations to reduce peak demand, energy cost, or carbon without missing
production targets.

### Why AI is justified

The schedule itself is an optimization problem. AI is useful for forecasting load,
duration, and production/thermal response under uncertain context—not for replacing
hard scheduling constraints.

### Teachable architecture

1. Time-series/gradient-boosting load forecast by operation and factory state.
2. Learned energy-duration surrogate for each operation/machine.
3. Mixed-integer or CP-SAT scheduler with precedence, capacity, and due dates.
4. Scenario/robust optimization over forecast uncertainty.
5. Optional RL handles rolling arrivals after the optimizer baseline is strong.

The U.S. Department of Energy's [2026 hourly manufacturing thermal-load dataset](https://catalog.data.gov/dataset/hourly-thermal-load-profiles-for-u-s-manufacturing-subsectors)
covers hourly demand and operating profiles for 63 manufacturing subsectors. The
[EIA Manufacturing Energy Consumption Survey](https://www.eia.gov/consumption/manufacturing/)
supplies authoritative sector context.

### Evaluation

- Energy cost, peak demand, carbon, tardiness, throughput, and schedule stability.
- Chronological and tariff/carbon shock tests.
- Earliest-due-date, cost-blind schedule, perfect-forecast oracle, deterministic,
  and robust policies.

### Demo, risk, and bounded build

Show a Gantt chart and energy/carbon curve while users change tariffs, carbon
intensity, or deadlines. Public sector data do not contain a detailed machine job
schedule, so a documented factory simulator must join process jobs to the public
load profiles. The fallback is forecast + CP-SAT; RL is a stretch, not the core.

## 14. SpareLink — maintenance-driven spare-parts inventory policy

### Manufacturing problem and decision

Critical parts have intermittent demand: months of zero use followed by a costly
failure. SpareLink combines installed-base reliability, planned maintenance,
repair turnaround, part compatibility, pooling across sites, and supplier lead
times to decide stock, repair, transfer, pool, or expedite.

### Why AI is justified

Standard forecasts perform poorly on zero-heavy demand. Reliability and maintenance
state provide causal demand signals, while heterogeneous part descriptions make
cross-site pooling hard. Optimization converts the predictive distributions into
inventory actions.

### Teachable architecture

1. Croston/SBA/TSB classical intermittent-demand baselines.
2. Survival/reliability model converts installed-base age and maintenance plan into
   demand distribution.
3. Optional language model structures part descriptions and retrieves compatible
   pooled parts, always exposing matched specifications.
4. Stochastic base-stock/network optimizer selects inventory and transfers.

An [open benchmark repository](https://github.com/danieldehaan96/spdf) includes
industrial and simulated spare-demand datasets, including seven years for 5,000
items. Research on [maintenance-informed demand](https://doi.org/10.1016/j.ijpe.2019.03.015)
establishes the installed-base/failure approach.

### Evaluation

- Inventory-service curves rather than forecast accuracy alone.
- Fill rate, downtime, stockouts, working capital, expiry/obsolescence, and transfers.
- Rolling-origin backtests and rare-demand stress tests.
- Croston-family, historical base-stock, reliability-informed, and oracle policies.

### Demo, risk, and bounded build

The app shows several factories, machines, pooled parts, uncertainty, and the cost
of a stockout versus holding. Dataset licenses/metadata must be audited before
publication. The fallback uses the transparent industrial benchmark without the
LLM pooling component.

## 15. FactoryRecovery — fault diagnosis and safe recovery-policy twin

### Manufacturing problem and decision

When a continuous process begins drifting, identifying the fault is only the first
step. Operators need to know which measurement to check and which safe control
action can return the process to its operating envelope without causing another
constraint violation.

### Why AI is justified

Many faults create overlapping multivariate symptoms across time. AI can estimate
fault state and forecast the response to candidate actions; a safety shield keeps
the recovery policy within deterministic process limits.

### Teachable architecture

1. PCA/PLS and gradient boosting as interpretable fault baselines.
2. 1D temporal CNN or transformer for fault diagnosis and early detection.
3. Learned dynamics surrogate predicts short-horizon process response.
4. Model-predictive control or constrained RL chooses recovery actions.
5. Retrieval layer explains variables/actions using process documentation.

The [Tennessee Eastman reference dataset](https://data.dtu.dk/articles/dataset/Tennessee_Eastman_Reference_Data_for_Fault-Detection_and_Decision_Support_Systems/13385936)
contains 132.96 GB, 28 faults, six operating modes, 500 simulations per condition,
100-hour trajectories, and a decision-support framing.

### Evaluation

- Fault F1, detection delay, and unseen-severity/mode generalization.
- Recovery time, integrated deviation, product-loss proxy, and constraint violations.
- Diagnosis-only, PID/rule recovery, MPC, RL, and oracle comparisons.
- Action/model ablations and safety-shield intervention rate.

### Demo, risk, and bounded build

Display the live process variables and flowsheet, inject a fault, show competing
diagnoses, select the next sensor/action, and animate recovery. Tennessee Eastman
is process rather than discrete mechanical manufacturing and is widely studied;
the project differentiates through safe recovery and explanation. The fallback is
diagnosis + model-predictive recovery; RL is optional.

## What these new ideas change in the overall recommendation

Three projects now deserve a serious comparison with the original five:

1. **MoldRx** has the cleanest end-to-end public dataset and lowest execution risk.
2. **PackRecover** has the strongest originality/mechanical/circular-manufacturing
   combination and a very recent real-product graph dataset.
3. **AssemblyGuard** has the richest human-centered multimodal data and the best
   path to an impressive procedural-reasoning demo.

If the priority is **scientific reliability**, choose MoldRx or MeasureLess. If the
priority is **distinctiveness and mechanical identity**, choose PackRecover or
FormTwin. If the priority is **multimodal spectacle backed by a real process**,
choose WeldSense or AssemblyGuard.
