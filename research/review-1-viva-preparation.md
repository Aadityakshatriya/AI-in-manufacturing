# Review 1 viva preparation — ToolLife Policy

This document prepares the five speakers for questions after the Review 1 video.
It also corrects claims in the current script that are not supported by the chosen
dataset or by completed experiments.

## 1. Corrections to make before presenting

These are not cosmetic. A reviewer who opens the dataset paper can catch them.

| Current claim | Problem | Defensible replacement |
|---|---|---|
| “Up to 20% of CNC tool costs stem directly from premature or delayed replacements.” | We did not find a primary source supporting this exact CNC-specific percentage. | “Poor replacement timing creates two avoidable costs: discarding usable tool life and risking breakage, scrap and downtime.” |
| “Vibration and temperature metrics” | The selected dataset contains **vibration and electrical-current signals**, not temperature. | “Vibration and spindle/axis-current signals.” |
| “We stream continuous sensor data” | The public data were recorded during individual milling cycles. Our prototype has not yet established a live factory stream. | “We analyse sensor signals recorded during each milling cycle.” |
| “Automated alerts directly into CNC controllers” | Direct controller integration is not part of the validated Review 1 scope. | “The prototype will display a decision-support alert after each cycle; controller integration is future deployment work.” |
| “XGBoost and LightGBM ensemble” | We have not shown that an ensemble is better. | “We will compare XGBoost and LightGBM baselines and may ensemble them only if grouped validation supports it.” |
| “Leave-one-tool-out across 14 cutters” | Fourteen tools exist, but one failed in its first cycle and is treated as an outlier. The paper recommends 13 ordinary tool partitions. | “Thirteen meaningful tool lifecycles will be evaluated by leave-one-tool-out testing; the first-cycle failure will be retained as a stress case.” |
| “Guarantee zero data leakage” | No test protocol should claim an absolute guarantee. | “Prevent cycles from the same cutter appearing in both training and test data, greatly reducing lifecycle leakage.” |
| “Ensure the model can successfully handle unexpected breakages” | Validation can measure this; it cannot ensure success in advance. | “Test how the model behaves on unseen cutters and on the first-cycle-breakage stress case.” |
| “Reduce unplanned downtime by up to 30%” | This is not a result from our project. No model has been trained or factory-tested yet. | “Measure whether the policy can reduce simulated downtime and failure cost compared with fixed replacement.” |
| “Extend tool life” | The software does not physically slow wear in the core project. | “Use a greater fraction of the tool's available safe life.” |
| “Reactive replacement before to predictive replacement after” | The before/after wording is unclear. | “Move from fixed-schedule or reactive replacement to condition-based, predictive replacement.” |

A broad NIST manufacturing survey found that greater use of predictive rather than
preventive maintenance was associated with about 15–18.5% less unplanned downtime,
depending on the comparison reported. That is useful motivation, but it is **not a
cutting-tool result and not our promised improvement**. Cite it only with that
qualification: [NIST survey and paper](https://www.nist.gov/publications/maintenance-costs-and-advanced-maintenance-techniques-manufacturing-machinery-survey).

## 2. Facts every group member must know

### The project in one sentence

ToolLife Policy estimates a calibrated range of cycles remaining for a CNC milling
cutter from vibration and current signals, then combines that uncertainty with the
cost and duration of the next job to recommend **CONTINUE** or **REPLACE**.

### The actual manufacturing decision

This project has two connected problems:

1. **Prediction:** How long is the cutter likely to survive?
2. **Decision:** Given that uncertainty and the next job's consequences, is it
   economically sensible to keep using it?

The second question is the project's differentiator. A good RUL score alone does
not tell an operator what to do.

### Verified primary-dataset facts

Source: [Piecuch and Żabiński, *Scientific Data*, 2025](https://www.nature.com/articles/s41597-025-04923-y)  
Files: [official Figshare dataset](https://doi.org/10.6084/m9.figshare.28589216)

| Item | Verified fact |
|---|---|
| Machine and process | Three-axis Haas VF-1 CNC milling machine |
| Material | Hardened 42CrMo4 steel; measured hardness 35.33–41.67 HRC |
| Cutters | 14 total, from two manufacturers/types |
| Recorded cycles | 968 |
| Failure endpoint | Complete cutter breakage or breakage of a cutting edge |
| Vibration sensing | 8 accelerometer channels sampled at 25 kHz |
| Current sensing | 12 spindle/axis-current channels sampled at 0.5 kHz |
| Cutting parameters | Axial depth 5 or 10 mm; radial depth 4.5 or 8 mm |
| Constant parameters | 3,200 rpm, 640 mm/min feed, 10 mm tool diameter |
| Processed inputs | 120 statistics: min, max, mean, standard deviation, skewness and kurtosis for each of 20 channels |
| Processed matrix | 968 rows × 131 columns after metadata, cycle count and target are added |
| Raw archive | 25.35 GB decimal, approximately 23.60 GiB |
| Target | `CycleToFailure`: cycles remaining before observed failure; a normalized version is also supplied |
| Important outlier | One cutter broke in its first cycle |
| Recommended evaluation | Hold out an entire tool; the authors recommend 13 partitions, training on 12 and testing on one |
| Licence | CC BY 4.0 |

### Proposed modelling stack

1. **Fixed-age and age-only baselines:** establish what is possible without sensor
   intelligence.
2. **XGBoost and LightGBM:** gradient-boosted decision trees trained on the 120
   released signal statistics and process metadata.
3. **1D CNN:** learns local patterns directly from raw vibration and current
   waveforms.
4. **TCN:** uses causal and dilated convolutions to capture longer time-series
   context efficiently.
5. **Quantile prediction plus conformal calibration:** produce lower, median and
   upper RUL estimates whose observed coverage can be checked.
6. **Transparent constrained policy:** calculate the expected cost of continuing
   versus replacing.
7. **Optional RL policy:** DQN or PPO learns decisions inside the simulator and is
   compared with the transparent policy; RL is not required to make the project
   valid.

### Evaluation plan

- Hold out complete cutters, not random rows.
- Compare age-only, sensor-only and sensor-plus-age models.
- Prediction metrics: RUL MAE/RMSE, failure-risk calibration and interval coverage.
- Decision metrics: failure rate, premature replacement, tool-life utilization,
  downtime, scrap exposure and normalized total cost.
- Replay the observed history of a held-out real cutter until replacement or
  failure.
- Use a clearly labelled production simulator for long-term cost and RL results.
- Do not claim real factory savings until a real deployment study exists.

### What has and has not been completed

**Completed:** project selection, primary-data verification, data-column audit,
system design and evaluation plan.

**Planned:** data pipeline, trained models, calibration, simulator, replacement
policy, dashboard and experimental results.

Always use future tense for the planned work: “we will train,” “we will compare,”
and “we expect to test.”

## 3. Speaker 1 — Bhuwan: problem, motivation and scope

### What Bhuwan must understand

- CNC milling uses a rotating multi-edge cutter to remove material along a
  computer-controlled path.
- Tool damage can develop through wear, chipping and eventual edge or cutter
  breakage.
- Fixed-age replacement is preventive maintenance: simple, but conservative
  because nominally identical cutters can fail at different times.
- Run-to-failure is reactive maintenance: it uses the tool fully but risks scrap
  and unplanned downtime.
- Predictive replacement uses measured condition to choose a point between those
  extremes.
- The precise project scope is decision support, not physical tool design and not
  automatic CNC control.

### Likely questions and defensible answers

**Q: What exact problem are you solving?**  
We are deciding whether a milling cutter should be used for the next job or
replaced first. We estimate its remaining life from sensor data and weigh the risk
of breakage against the cost of replacing too early.

**Q: Why not simply replace every cutter after a fixed number of cycles?**  
Because tool lives vary with the individual cutter, workpiece hardness, depth of
cut and actual operating condition. A limit safe for the weakest cutter can waste
substantial life from stronger cutters.

**Q: Why is AI needed?**  
Wear changes several noisy signals at once, and their relationship with failure is
nonlinear. ML can learn those combined patterns. The final cost calculation remains
explicit, so AI is used only where it adds value.

**Q: What is novel here?**  
Tool-life prediction itself is established. Our course contribution is to add
calibrated uncertainty and turn the prediction into a job-aware replacement
decision, evaluated on completely unseen cutters.

**Q: Where did the 20% figure come from?**  
It is not sufficiently supported for this specific claim, so we should remove it.
Our motivation does not require it; the early-versus-late replacement trade-off is
well established.

### Bhuwan's sources

- [Primary milling dataset and manufacturing context](https://www.nature.com/articles/s41597-025-04923-y)
- [Research on balancing premature replacement and failure cost](https://doi.org/10.1016/j.ejor.2010.03.023)
- [NIST maintenance-economics study](https://www.nist.gov/publications/maintenance-costs-and-advanced-maintenance-techniques-manufacturing-machinery-survey)

### Prompt Bhuwan can paste into an AI

```text
Act as my oral-exam tutor for an AI in Manufacturing project. My role is to
explain the manufacturing problem, motivation, significance and project scope.

Our project is ToolLife Policy. It predicts a calibrated range of remaining useful
life for a CNC milling cutter from vibration and machine-current data, then decides
whether to CONTINUE or REPLACE before the next job. Replacing too early wastes
usable tool life; replacing too late risks cutter breakage, scrap and unplanned
downtime. This is currently a proposed decision-support prototype, not a deployed
controller.

Use these sources:
https://www.nature.com/articles/s41597-025-04923-y
https://doi.org/10.1016/j.ejor.2010.03.023
https://www.nist.gov/publications/maintenance-costs-and-advanced-maintenance-techniques-manufacturing-machinery-survey

First teach me CNC milling, tool wear, preventive versus predictive replacement,
and why AI is justified, using simple language. Then test me one question at a
time. Challenge unsupported claims, especially the unsourced 20% tool-cost claim.
After each answer, correct me and give me a stronger 20-second answer. Do not let
me claim that the system has already been deployed or achieved savings.
```

## 4. Speaker 2 — Yadu: sensing, predictive maintenance and system flow

### What Yadu must understand

- The selected sensors are **vibration and electrical current**, not temperature.
- As a cutter wears or chips, contact and cutting forces change. That can alter the
  vibration pattern and the electrical load drawn by the spindle and axes.
- Current is attractive because it may be obtainable from the machine's electrical
  system; vibration can be more sensitive but requires accelerometers.
- Time-series analysis means examining measurements in their recorded time order.
- Anomaly detection asks whether a signal differs from learned normal behaviour;
  it is an optional health indicator, not the sole RUL method.
- The core prototype makes a decision after a milling cycle. Direct CNC-controller
  integration is future work.

### Likely questions and defensible answers

**Q: Why use both vibration and current?**  
They observe different consequences of cutting. Vibration captures mechanical
response, while current approximates the load demanded from the spindle and axes.
Combining them may be more robust, and we will also test each group separately.

**Q: Where is the temperature data?**  
There is none in our primary dataset. The correct channels are eight vibration and
twelve current channels.

**Q: Is the system truly real time?**  
Our target is cycle-level online decision support: process one completed cycle and
decide before the next job. It is not a microsecond safety controller and has not
yet been connected to a CNC control system.

**Q: What is anomaly detection doing?**  
It can flag unusual behaviour relative to healthy cuts, especially unexpected
events. The main supervised task is still RUL prediction because the dataset gives
the true number of cycles remaining.

**Q: What happens if a sensor fails?**  
We will run sensor-dropout and sensor-group ablations. A practical fallback may use
spindle current alone or spindle vibration alone, with wider uncertainty.

### Yadu's sources

- [Dataset sensors, sampling rates and experiment](https://www.nature.com/articles/s41597-025-04923-y)
- [NIST monitoring, diagnostics and prognostics programme](https://www.nist.gov/programs-projects/monitoring-diagnostics-and-prognostics-manufacturing-operations)
- [NIST manufacturing AI examples and cautions](https://www.nist.gov/blogs/manufacturing-innovation-blog/artificial-intelligence-manufacturing-real-world-success-stories)

### Prompt Yadu can paste into an AI

```text
Act as my oral-exam tutor. My section explains the sensing and high-level workflow
of ToolLife Policy, an AI-assisted CNC milling tool-replacement project.

The primary dataset has 8 vibration channels at 25 kHz and 12 spindle/axis-current
channels at 0.5 kHz. It does NOT have temperature. We analyse signals from each
milling cycle, estimate remaining useful life and send the estimate to a decision
layer that recommends CONTINUE or REPLACE. The prototype is cycle-level decision
support; direct CNC-controller integration is only future work. Anomaly detection
is secondary to supervised RUL prediction.

Source:
https://www.nature.com/articles/s41597-025-04923-y
https://www.nist.gov/programs-projects/monitoring-diagnostics-and-prognostics-manufacturing-operations

Teach me why wear affects vibration and current, what time-series analysis means,
the difference between anomaly detection and RUL regression, why sensor fusion can
help, and what “cycle-level online” honestly means. Then conduct a viva one
question at a time, correcting every overclaim. Make me practise 20-second answers.
```

## 5. Speaker 3 — Aditya: ML architecture, uncertainty and policy

### What Aditya must understand

- A **feature** is a numerical summary supplied to a model. The released dataset
  has six statistics for each of 20 channels: 6 × 20 = 120.
- **XGBoost and LightGBM** are gradient-boosting implementations. Trees are added
  sequentially so later trees correct errors made by the existing ensemble.
- We should compare XGBoost and LightGBM first. Calling them an ensemble is valid
  only if we later combine their outputs and validation shows a benefit.
- A **1D CNN** slides learned filters along a waveform to detect short local
  patterns.
- A **TCN** is a convolutional sequence model. Causal convolutions avoid using
  future samples; dilations let it see a longer history without an enormous model.
- **RUL** is the predicted number of useful cycles remaining before failure.
- A point prediction alone hides uncertainty. Quantile models can estimate, for
  example, lower/median/upper RUL; conformal calibration checks and adjusts the
  interval using held-out tools.
- The policy consumes the RUL distribution. It is separate from the health model.
- The transparent policy compares expected costs. Optional RL learns the policy
  through simulator interaction and must beat transparent baselines to justify
  itself.

### Likely questions and defensible answers

**Q: Why use tree models and deep learning?**  
The processed table is small and structured, so boosted trees are strong,
interpretable baselines. CNN/TCN models test whether the raw waveform contains
useful patterns lost by summary statistics. We will deploy whichever generalizes
better, not whichever sounds more advanced.

**Q: What is the difference between XGBoost and LightGBM?**  
Both build boosted decision trees. They differ mainly in tree construction and
computational optimizations. For us they are competing baselines; their performance
must be measured under the same grouped split.

**Q: Why a 1D CNN rather than an image CNN?**  
The raw input is a signal indexed by time, so filters move in one dimension along
time rather than in two dimensions across image height and width.

**Q: How is a TCN different from an ordinary CNN?**  
A TCN is designed for sequences. Causal convolutions use only present and past
data, and dilated convolutions expand the receptive field so the network can learn
longer temporal relationships.

**Q: Why predict lower, median and upper RUL?**  
Two cutters can have the same median prediction but very different uncertainty.
A wide lower-to-upper range should make the replacement policy more cautious,
especially before a costly job.

**Q: What makes the policy “constrained”?**  
Actions must obey defined operational rules, and the policy cannot accept failure
risk above a chosen safety limit merely to save tool cost. Constraints remain
explicit rather than being hidden inside the model.

**Q: Why use RL at all?**  
RL becomes interesting when today's decision changes future tool health, job delay
and later choices. We will first implement a transparent expected-cost or dynamic-
programming policy. RL is justified only if it improves long-horizon decisions in
the same simulator without violating constraints.

**Q: Which metrics evaluate the models?**  
MAE and RMSE evaluate RUL error. Interval coverage checks uncertainty. Brier score
can evaluate predicted failure probability. Policy performance uses failures,
unused tool life, downtime and total normalized cost.

### Aditya's sources

- [Original XGBoost paper](https://arxiv.org/abs/1603.02754)
- [Original LightGBM paper](https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html)
- [TCN paper](https://arxiv.org/abs/1803.01271)
- [Conformal-prediction tutorial](https://www.jmlr.org/papers/v9/shafer08a.html)
- [Original PPO paper](https://arxiv.org/abs/1707.06347)

### Prompt Aditya can paste into an AI

```text
Act as a demanding but clear ML viva examiner. I am presenting the model pipeline
for ToolLife Policy, a CNC milling tool-replacement project.

Data: 968 cycles, 20 sensor channels and 120 released statistical features. The
pipeline compares XGBoost and LightGBM on engineered features; a 1D CNN and TCN on
raw vibration/current time series; quantile RUL predictions with conformal
calibration; then an explicit constrained expected-cost policy. DQN or PPO is an
optional policy comparison inside a production simulator, not the core model.

Teach and test me on: gradient boosting, difference between XGBoost and LightGBM,
1D CNN, causal/dilated TCN, RUL regression, quantile loss, conformal calibration,
MAE versus RMSE, Brier score, expected-cost decisions, dynamic programming and why
RL may or may not be justified. Ask one question at a time. After my answer, point
out errors and give a concise answer I can say aloud.

Primary references:
https://arxiv.org/abs/1603.02754
https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html
https://arxiv.org/abs/1803.01271
https://www.jmlr.org/papers/v9/shafer08a.html
https://arxiv.org/abs/1707.06347
```

## 6. Speaker 4 — Amal: dataset and validation

### What Amal must understand

- The source is not merely “the internet.” It is a peer-reviewed 2025 data
  descriptor in *Scientific Data*, with files deposited on Figshare under CC BY.
- One processed row corresponds to one recorded milling cycle.
- Raw data are high-frequency waveforms. Processed data are summary statistics
  derived from those waveforms and joined with metadata.
- The independent units are tool lifecycles, not the 968 individual rows. This is
  why a random row split would exaggerate generalization.
- Leave-one-tool-out means training on other tools and testing on every cycle from
  one completely unseen cutter.
- The first-cycle-breakage cutter cannot provide a normal degradation history. It
  should be a stress case, leaving 13 normal evaluation groups.
- Prevent leakage by excluding tool ID, filenames and target columns from inputs;
  fit scaling and feature selection only on training tools.

### Likely questions and defensible answers

**Q: Is 968 cycles a large dataset?**  
It is large in raw sample count but small in independent failure histories: only 14
tools, of which 13 have meaningful trajectories. That supports strong classical
baselines and a compact regularized deep model, but not a giant network.

**Q: What are the 120 features?**  
Minimum, maximum, mean, standard deviation, skewness and kurtosis are calculated
for each of the 20 signal channels: six statistics times twenty channels.

**Q: What is the target variable?**  
`CycleToFailure`, the number of milling cycles remaining before the cutter's
observed failure. The release also supplies a normalized version.

**Q: Why is random cross-validation wrong here?**  
Neighbouring cycles from the same cutter are highly related. If some enter training
and others testing, the model partly recognizes that lifecycle rather than
generalizing to a new tool.

**Q: Does leave-one-tool-out guarantee zero leakage?**  
It removes the main lifecycle leakage, but we must also exclude identifier and
target-derived columns and fit preprocessing within each fold. “Zero leakage” is
too absolute; we should describe the controls we implement.

**Q: Why keep the first-cycle failure?**  
It cannot train a degradation trajectory, but it is valuable as an extreme test of
how the system expresses uncertainty or abstains when failure is unpredictable.

**Q: Why not mix PHM 2010 or NASA data into training?**  
Those datasets use different tools, machines, materials, sensors and labels. They
are useful external-shift tests, but naive pooling could make the target
inconsistent.

### Amal's sources

- [Dataset paper](https://www.nature.com/articles/s41597-025-04923-y)
- [Official Figshare record and downloads](https://doi.org/10.6084/m9.figshare.28589216)
- [Official scikit-learn explanation of grouped and leave-one-group-out validation](https://scikit-learn.org/stable/modules/cross_validation.html)
- [PHM Society 2010 challenge archive](https://phmsociety.org/phm_competition/)
- [NASA Milling Wear dataset](https://catalog.data.gov/dataset/milling-wear)

### Prompt Amal can paste into an AI

```text
Act as my dataset and experimental-design viva tutor for ToolLife Policy.

The primary peer-reviewed dataset is:
https://www.nature.com/articles/s41597-025-04923-y
Files: https://doi.org/10.6084/m9.figshare.28589216

It contains 968 CNC milling cycles from 14 tools followed to failure on a Haas
VF-1 cutting 42CrMo4 steel. There are 8 vibration channels at 25 kHz and 12 current
channels at 0.5 kHz. The processed table has 120 signal statistics and metadata.
One cutter failed in its first cycle, so 13 meaningful lifecycles are used for
ordinary leave-one-tool-out evaluation and the outlier is a stress case.

Teach me the dataset line by line: machine, material, sensors, parameters, target,
raw versus processed size, one row's meaning and licence. Then quiz me on data
leakage, why random splitting is wrong, leave-one-tool-out cross-validation, the
outlier, preprocessing leakage and whether 968 cycles is genuinely large. Ask one
question at a time and make me answer in under 25 seconds.
```

## 7. Speaker 5 — Rafiq: expected outcomes, metrics and limitations

### What Rafiq must understand

- At Review 1, benefits are hypotheses, not achieved results.
- “Using more safe tool life” means later but still risk-controlled replacement;
  it does not mean the software physically makes the cutter more durable.
- Prediction accuracy and manufacturing value are different. The final system can
  tolerate a small RUL error poorly if it causes expensive late replacements.
- The real lifecycle replay measures where a policy would stop on an observed
  tool. The long-horizon simulator estimates repeated replacement economics.
- Simulator costs will be normalized and swept across ranges. They are not claimed
  as real rupee savings without factory cost data.
- The fairest goal is lower expected cost **at the same or lower failure rate** than
  the best fixed-age policy.

### Likely questions and defensible answers

**Q: How can you promise 30% less downtime before running the project?**  
We cannot. That number should be removed. We will measure downtime and cost against
fixed-age replacement in real-lifecycle replays and a clearly labelled simulator.

**Q: What exactly is the expected outcome?**  
A calibrated RUL model and an explainable replacement policy that uses more of the
available safe tool life while controlling failure risk and lowering simulated
cost relative to fixed schedules.

**Q: How will you measure success?**  
For prediction: RUL MAE/RMSE and uncertainty coverage. For the decision: failures,
discarded useful life, tool-life utilization, planned and unplanned downtime,
scrap exposure and total normalized cost.

**Q: What are your comparison baselines?**  
A conservative fixed replacement age, a median fixed age, an age-only survival
model, a point-RUL threshold, an uncertainty-aware policy and a perfect-information
oracle. Optional RL is compared under the same simulator.

**Q: How can you evaluate economics without deploying in a factory?**  
We separate evidence. Real cutter histories validate the stopping decision up to
the first replacement. A documented simulator evaluates repeated operation under
different cost assumptions. We report simulated savings, not factory savings.

**Q: Why is uncertainty important?**  
If the RUL range is wide, continuing may be unsafe even when the median looks
acceptable. The policy should become more conservative before a long or valuable
job.

**Q: What if the CNN performs worse than XGBoost?**  
We deploy the better calibrated model and report the comparison. A simpler model
winning on a small dataset is a scientifically useful result, not project failure.

**Q: What is the biggest limitation?**  
Only 13 meaningful degradation histories come from one experimental machine. That
limits claims about other factories; external datasets and sensor-dropout tests
can examine robustness but do not replace real deployment.

### Rafiq's sources

- [NIST evidence on predictive-maintenance benefits and limits](https://www.nist.gov/publications/maintenance-costs-and-advanced-maintenance-techniques-manufacturing-machinery-survey)
- [Optimal replacement trade-off research](https://doi.org/10.1016/j.ejor.2010.03.023)
- [Primary dataset and failure histories](https://www.nature.com/articles/s41597-025-04923-y)

### Prompt Rafiq can paste into an AI

```text
Act as my viva tutor for the expected outcomes, evaluation and limitations of
ToolLife Policy.

This is a proposed CNC milling replacement system. It will predict a calibrated
RUL range, then choose CONTINUE or REPLACE using expected tool, scrap, downtime and
delay costs. Nothing has been deployed yet. We must not promise 30% downtime
reduction or real savings. We will compare against fixed-age, age-only and
point-RUL baselines using held-out cutter replays and a documented production
simulator. Metrics include MAE/RMSE, interval coverage, failures, discarded tool
life, tool-life utilization, downtime and normalized cost.

Teach me the difference between expected benefit and measured result, prediction
metrics versus decision metrics, real replay versus simulation, uncertainty,
baselines, the oracle and the project's limitations. Then run a hostile viva one
question at a time. Reject unsupported percentages and rewrite every answer into a
clear 20-second response.

Sources:
https://www.nist.gov/publications/maintenance-costs-and-advanced-maintenance-techniques-manufacturing-machinery-survey
https://doi.org/10.1016/j.ejor.2010.03.023
https://www.nature.com/articles/s41597-025-04923-y
```

## 8. Shared terminology cheat sheet

| Term | Plain-language meaning |
|---|---|
| CNC milling | Computer-controlled machining in which a rotating cutter removes material |
| Tool wear | Gradual damage caused by repeated cutting, heat, friction and mechanical load |
| RUL | Remaining Useful Life: estimated useful cycles left before failure |
| Time series | Measurements kept in time order rather than treated as unrelated rows |
| Feature | A numerical input given to a model, such as vibration standard deviation |
| Gradient boosting | Building trees sequentially, with each new tree correcting earlier errors |
| XGBoost/LightGBM | Efficient implementations of gradient-boosted decision trees |
| 1D CNN | Neural network that slides learned filters along a time signal |
| TCN | Convolutional sequence model using causal/dilated filters for longer histories |
| Quantile | A point in a predicted distribution, such as lower, median or upper RUL |
| Calibration | Checking whether predicted confidence matches observed outcomes |
| Conformal prediction | A method that adjusts prediction intervals using held-out errors |
| Cross-validation | Repeated training/testing splits used to estimate generalization |
| Leave-one-tool-out | All cycles from one cutter are withheld together for testing |
| Data leakage | Test or future information accidentally entering model training |
| Baseline | Simpler method the proposed model must beat |
| Policy | Rule or learned strategy mapping current state to CONTINUE or REPLACE |
| Constraint | An operational limit the policy is not allowed to violate |
| Reinforcement learning | Learning a sequential policy by receiving rewards/costs in a simulator |
| Digital twin/simulator | Software environment approximating tool degradation and production jobs |

## 9. Ten questions anyone may be asked

1. **What is your input?** Vibration/current signals, process parameters and known
   tool age.
2. **What is your target?** Cycles remaining until the observed cutter failure.
3. **What is your output?** A calibrated RUL range and CONTINUE/REPLACE decision.
4. **Why not use a fixed threshold?** Cutter lives and job consequences vary.
5. **Why both XGBoost and CNN/TCN?** Processed-feature baseline versus raw-signal
   learning.
6. **Why leave one tool out?** To test generalization to a genuinely unseen cutter.
7. **What prevents leakage?** Grouped splits, removal of IDs/targets and fold-local
   preprocessing.
8. **Why model uncertainty?** Replacement is asymmetric; overconfidence can cause
   failure or excessive early changes.
9. **Where does RL operate?** Only in the documented production simulator, after a
   transparent policy is working.
10. **What is the main limitation?** Thirteen meaningful lifecycles from one
    experimental machine; no real factory deployment yet.

## 10. One-hour group preparation plan

### First 10 minutes — correct the shared story

Everyone says the one-sentence project definition aloud. Remove temperature,
controller integration, the 20% claim and the 30% promise from all notes.

### Next 15 minutes — individual study

Each person reads only their packet and opens their three to five links. Nobody
needs to read every paper; each person should be able to locate the evidence for
their own claims.

### Next 20 minutes — AI mock viva

Each person pastes their prompt into an AI and answers at least eight questions
aloud. Answers must stay below 25 seconds.

### Next 10 minutes — cross-questioning

Each speaker asks the next speaker two questions. If only one person can explain a
term, the group is not ready because the reviewer can redirect questions.

### Final 5 minutes — memorize anchors, not paragraphs

Every person memorizes only five anchors:

1. the manufacturing decision;
2. their two or three exact facts;
3. one model or method they own;
4. one evaluation metric;
5. one honest limitation.

Do not memorize long definitions. Start each answer with the direct conclusion,
then give one reason or example.

