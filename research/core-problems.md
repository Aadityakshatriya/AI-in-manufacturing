# Core problem map: what “AI in manufacturing” actually means

Manufacturing is a chain of decisions made under incomplete, noisy, delayed, and
expensive information. AI is useful when it estimates hidden state from complex
data, learns a response faster than physics or experimentation, or helps choose
among many constrained actions. It is not automatically useful for every factory
task.

## 1. Perception and defect detection

- **Question:** Is the part, weld, surface, assembly step, or tool state normal?
- **Signals:** images, video, X-ray, thermography, sound, vibration, point clouds.
- **Useful AI:** CNNs/vision transformers, anomaly detection, multimodal fusion.
- **Decision:** accept, reject, rework, stop, or send to human review.
- **Crowded version:** train a classifier on clean, random train/test splits.
- **Real gap:** lighting/machine/product shift, rare defects, localization,
  calibrated abstention, and inspection economics.

## 2. Virtual metrology and soft sensing

- **Question:** Can an expensive, destructive, or delayed measurement be predicted
  from process sensors?
- **Useful AI:** Gaussian processes, tree ensembles, temporal models.
- **Decision:** release, adjust, or physically measure the item.
- **Real gap:** drift-aware online updating and deciding *when* prediction is safe
  enough to replace measurement.

## 3. Fault diagnosis and process-state estimation

- **Question:** What abnormal state is developing and what is the likely cause?
- **Useful AI:** interpretable classifiers, Bayesian/causal graphs, multimodal
  temporal models.
- **Decision:** continue, derate, inspect a component, or isolate a process stage.
- **Real gap:** separating symptoms from controllable causes and ranking the next
  useful diagnostic measurement.

## 4. Remaining useful life and maintenance decisions

- **Question:** How long until a tool or asset crosses an unacceptable risk level?
- **Useful AI:** survival models, gradient boosting, 1D CNNs/transformers.
- **Decision:** maintain now, schedule later, order a spare, or keep operating.
- **Crowded version:** C-MAPSS RUL regression.
- **Real gap:** uncertainty, asymmetric failure costs, production-aware scheduling,
  and transfer across assets.

## 5. Process-parameter optimization and control

- **Question:** Which settings will produce the target quality quickly, safely, and
  efficiently?
- **Useful AI:** learned surrogates, Bayesian optimization, model-predictive
  control, or safe RL.
- **Decision:** choose or change current, speed, temperature, pressure, feed, scan
  power, tool path, or recipe.
- **Real gap:** hard constraints, uncertainty, nonstationarity, and proving that an
  offline recommendation is more than correlation.

## 6. Simulation acceleration and sim-to-real transfer

- **Question:** Can a learned surrogate replace a slow FE/CFD/process simulation,
  and how much real data is needed to correct its reality gap?
- **Useful AI:** Gaussian processes, compact neural networks, neural operators,
  residual correction, fine-tuning/domain adaptation.
- **Decision:** explore geometry/settings, optimize a process, or run another
  physical experiment.
- **Real gap:** calibrated transfer and knowing when the simulator has taught the
  wrong relationship.

## 7. Planning, scheduling, routing, and allocation

- **Question:** What should be made/moved/processed next, on which resource, and in
  what order?
- **Useful AI:** learned duration/demand estimates combined with constraint
  programming, mathematical optimization, heuristics, or RL.
- **Decision:** schedule jobs, route pickers/AGVs, batch orders, allocate labor.
- **Crowded version:** PPO on a toy job-shop environment.
- **Real gap:** dynamic disruptions, robust policies, hard feasibility, and beating
  strong operations-research baselines on unseen instances.

## 8. Supply-network prediction and mitigation

- **Question:** How will demand, capacity, or a disruption propagate through a
  multi-tier product/supplier graph?
- **Useful AI:** temporal GNNs, forecasting, simulation, robust optimization/RL.
- **Decision:** dual-source, expedite, move capacity, change stock, or ration
  components.
- **Crowded version:** LLM agents role-playing suppliers.
- **Real gap:** calibrated graph forecasts tied to explicit mitigation cost and
  recovery metrics.

## 9. CAD, engineering drawings, DFM, and process planning

- **Question:** What manufacturing features and requirements are encoded in the
  design, and how should the part be made?
- **Useful AI:** B-Rep GNNs, drawing vision-language models, sequence planning,
  grounded LLM tool use.
- **Decision:** redesign, choose process/machine/tool/setup, sequence operations,
  or quote a job.
- **Real gap:** geometry-grounded constraints and reliable end-to-end plan/cost
  validation, not merely feature recognition or generated prose.

## 10. Traceability, root cause, and engineering-change propagation

- **Question:** Which upstream event caused this defect, or what downstream
  artifacts will a design change affect?
- **Useful AI:** heterogeneous graphs, causal models, retrieval and grounded LLMs.
- **Decision:** contain lots, correct a stage, notify a supplier, update a plan, or
  approve a change.
- **Real gap:** interoperable digital-thread data and high-recall impact analysis
  with evidence for every link.

## 11. Robotics and human work

- **Question:** What is the task state, what action should the robot take, and how
  can work remain safe and ergonomic?
- **Useful AI:** pose/action models, RGB-D fusion, imitation/RL, task-allocation
  policies.
- **Decision:** grasp, move, slow/stop, reassign a task, or redesign a workstation.
- **Real gap:** rare safety events, human variability, uncertainty, and safe
  generalization outside a scripted demo.

## 12. Sustainability, energy, and circular manufacturing

- **Question:** How can production meet quality/delivery constraints with less
  energy, material, scrap, or lost end-of-life value?
- **Useful AI:** forecasts and surrogates combined with optimization, graph/RL
  disassembly planning, material-flow models.
- **Decision:** shift loads, change settings, reuse/remanufacture/recycle, or select
  a disassembly sequence.
- **Real gap:** multi-objective decisions grounded in real process constraints and
  life-cycle boundaries.

## 13. Autonomous experiments and materials/process discovery

- **Question:** Which expensive experiment should be run next?
- **Useful AI:** uncertainty-aware surrogate + Bayesian optimization/active
  learning.
- **Decision:** choose formulation, heat treatment, material, or process trial.
- **Real gap:** closing the loop with constraints and manufacturing performance;
  property prediction alone is materials informatics, not necessarily
  manufacturing AI.

## 14. Industrial knowledge copilots and agents

- **Question:** How can manuals, standards, drawings, sensor results, and software
  tools be used together to support an engineer?
- **Useful AI:** RAG/SFT LLMs with tool calls, structured outputs, citations, and
  deterministic validators.
- **Decision:** diagnose, plan, document, or explain an action.
- **Crowded version:** chat with PDFs.
- **Real gap:** grounded reasoning over live manufacturing state and verified tool
  outputs, with an abstain/escalate path.

## The cross-cutting problem most student projects omit

Trustworthy operation is itself a manufacturing problem:

- Does confidence match reality?
- What happens under a new machine, material, lighting condition, or operator?
- When should the model abstain?
- Which false error is more expensive?
- Does the recommended action obey physics, tooling, safety, and process limits?
- Can the system explain the relevant evidence without fabricating it?

The strongest project is therefore not necessarily the one with the hardest
network. It is the one that closes this loop:

**observe → estimate → quantify uncertainty → choose a constrained action → measure
operational value → learn from the result.**
