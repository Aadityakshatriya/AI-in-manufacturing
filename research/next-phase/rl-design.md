# The decision-maker: reinforcement learning design for cutter replacement

**Date:** 27 October 2026
**Status:** design for the two-day build. Nothing here has been built or run yet.
**Scope:** only the part that decides *what to do* after each cut. The predictor (the model that turns vibration and current into failure probabilities) is designed elsewhere. It appears here only through the output it must hand over (section 1.3).

---

## 0. The short version

**For one cutter with two choices, RL is not needed.** "Keep or change" for a single cutter is a stopping problem: you stop once, and the cutter is gone. Given the predictor's failure probabilities and our assumed costs, the best rule can be calculated exactly with a small table calculation (dynamic programming, "DP"). We will do that calculation and use it as the yardstick. If an RL agent cannot match it in this easy case, the agent or the environment has a bug.

**RL is worth using once we add a workshop.** Several machines share one tool setter and a small stock of spare cutters. Orders arrive with due dates and different part values. Each machine can also run 20% slower to make its cutter last longer. Now the right move for one machine depends on every other machine: a cutter may be worth changing early because the setter is free now and will be busy later. The exact calculation grows too large to do, so learning a policy by trial and error becomes the reasonable tool. The literature says the same thing (section 2.6).

**Recommended environment ("the workshop").** Three machines (four as a stretch goal). Each machine replays real recorded cutter lifecycles: the cutter breaks exactly where the real one broke, and what the agent sees is our predictor's output on that cutter's real signals. Each machine has four actions: run, run slow, change cutter, pause. There is one setter and a spare-cutter stock that is restocked on a schedule. Orders arrive at random and are handed to machines by a fixed rule. The reward is profit in rupees. Slowing down makes each part use up less of the cutter's life, following Taylor's tool-life equation. The dataset cannot tell us how big this effect is, because every cutter ran at the same speed, so we randomise the effect and sweep it.

**Algorithms.** The main agent is MaskablePPO from sb3-contrib, with one choice covering all machines at once and impossible combinations ruled out. The comparison agent is a Double DQN with the same ruling-out (a short custom CleanRL-style script, because the standard library's DQN cannot rule out actions). The "factory-realistic" version is PPO with a Lagrange multiplier, a penalty weight that rises automatically until the agent stays within a breakage budget. All RL runs on CPU. The GPU is for training the predictor.

**Evaluation.** Every number we report comes from cutters the predictor and the agent never trained on. We compare against a fixed-count rule, a remaining-life threshold, a hazard threshold, the one-step cost rule, plan-ahead MPC, the exact DP (single machine), sensible per-machine rules with setter priority, a simulation-based lookahead (multi-machine), and a "perfect knowledge" reference. We use at least five training seeds, paired comparisons on identical random scenarios, and confidence intervals that resample *cutters*, because 13 cutters is the real sample size.

**Compute.** Roughly 150–300 CPU core-hours plus up to about 10 GPU-hours for the predictor's cross-validation. That is under a day on a single 32–64-core machine.

**How we will phrase results.** We use three levels of claim, from "measured on real held-out cutters, with costs assumed" down to "simulated". We never say RL "reduces factory costs" (section 7.3).

---

## 1. What the data allows

### 1.1 Facts checked in `data/raw/metadata.xlsx`

`CycleToFailure` counts down from L to 0 for each cutter. The row with 0 is the cycle in which the cutter broke, so a cutter with L = 49 finished 49 good cycles and broke during the 50th.

| Cutter | Type | ADOC (mm) | RDOC (mm) | Hardness (HRC) | L (good cycles before breaking) | Rows | Missing cycles |
|---|---|---|---|---|---|---|---|
| 10 | 1 | 10 | 4.5 | 37.33 | 14 | 15 | none |
| 6 | 1 | 5 | 8.0 | 40.00 | 29 | 28 | 1, 28 |
| 4 | 1 | 5 | 8.0 | 35.33 | 40 | 41 | none |
| 2 | 1 | 5 | 8.0 | 36.67 | 49 | 48 | 17, 18, 30 (and one duplicate row) |
| 3 | 1 | 10 | 8.0 | 40.00 | 49 | 44 | 2, 3, 11, 38, 41, 45 |
| 5 | 1 | 10 | 8.0 | 38.17 | 53 | 51 | 30, 38, 43 |
| 103 | 2 | 10 | 4.5 | 39.83 | 59 | 60 | none |
| 101 | 2 | 10 | 4.5 | 39.33 | 83 | 84 | none |
| 102 | 2 | 5 | 4.5 | 38.33 | 84 | 82 | 34, 35, 80 |
| 8 | 1 | 5 | 4.5 | 41.67 | 115 | 116 | none |
| 105 | 2 | 5 | 4.5 | 38.33 | 124 | 125 | none |
| 7 | 1 | 10 | 4.5 | 40.33 | 126 | 124 | 1, 106, 107 |
| 9 | 1 | 5 | 4.5 | 37.33 | 149 | 149 | 3 |
| 11 | 1 | 10 | 4.5 | 37.17 | 0 (broke in first cycle) | 1 | — |

Consequences for the design:

1. **Only 13 usable lifecycles.** Lives range from 14 to 149 good cycles (median 59, mean 75). Every RL result rests on these 13. Cutter 11 is kept out of the pools and used only as a stress case ("a new cutter can fail at once").
2. **All cutters ran at 3200 rpm and 640 mm/min with a 10 mm cutter.** The data says nothing about what happens at another speed. The slow-down action is therefore entirely an assumption (section 4.4) and must be labelled as one.
3. **Rows are not in time order** (cutter 5 starts at cycle 9), some cycles are missing, and cutter 2 has a duplicate row. The replay must sort by `CycleToFailure` (descending), drop the duplicate, and carry the last prediction forward over gaps.
4. **Radial depth of cut explains much of the life.** All five cutters at RDOC 8.0 lived 29–53 cycles, while the RDOC 4.5 cutters lived 14–149. Cutting conditions are known before cutting starts, so the agent may see them. With so few cutters, though, it can also *memorise* them (section 7.2).

### 1.2 The other datasets

The secondary datasets (PHM 2010: three labelled cutters run to a wear limit; NASA milling: 16 cases with sparse wear readings) end at a **wear limit**, not a breakage. In a workshop that is a *quality* failure: parts made beyond the limit are scrap, but the machine is not damaged. They add few lifecycles and come from different machines and materials. Recommendation: do **not** mix them into the main pool during the two-day build. Use them afterwards as a robustness test: does a policy built on the main dataset still behave sensibly on a "family B" machine whose failure means scrap instead of breakage?

### 1.3 What the predictor must hand to the decision-maker

The environment never runs a neural network. It reads pre-computed tables, which keeps it fast and makes leakage easy to audit.

For every outer fold f, every cutter c in that fold's pools, and every number of completed cycles k = 0 … L_c:

```
pred[f][c][k] = ( p(1), p(2), ..., p(N), p(>N) )      # sums to 1
   p(j)   = P(cutter breaks during the j-th next cut | everything known after k cuts)
   p(>N)  = P(cutter survives all N next cuts)
   N      = 10 (recommended)
   k = 0  = prediction for a brand-new cutter (conditions only, no signals yet)
optional: K samples per entry (ensemble members or MC-dropout draws), for realistic forecast noise
provenance: which cutters the predictor that produced this row was trained on (used by an assertion)
```

Helper quantities used everywhere below: the survival curve `S(j) = 1 - p(1) - ... - p(j)` and the per-cut hazard `h(j) = p(j) / S(j-1)`, the chance of breaking on cut j given that the cutter survived until then. If the predictor outputs remaining-life quantiles instead of `p(j)`, convert the quantiles to this format once, offline.

---

## 2. What the literature does

Search covered 2015–2026 with emphasis on 2022–2026. Details marked *(abstract-level)* were confirmed only from the abstract or publisher metadata, not the full text.

### 2.1 RL aimed directly at milling cutters

- **Siraskar et al. (2025), *Discover Applied Sciences*.** This is the only direct comparison of RL algorithms for milling tool replacement that we found. A simple hand-written REINFORCE agent was compared with untuned Stable-Baselines3 DQN, A2C and PPO across 15 environment variants: simulated wear, PHM Society wear data, noisy single-signal states with random breakdowns, and multi-signal states. Averaged F1 for "replace at the right time" was REINFORCE 0.609, A2C 0.442, DQN 0.374 and PPO 0.345. The authors stress that these algorithms are very sensitive to hyperparameters. There is no economic objective and no DP or threshold baseline. *Lesson:* untuned off-the-shelf deep RL performs poorly here; budget time for tuning, and measure money, not classification scores.
- **Ferrisi et al. (2025), Green-Aware AI workshop at ECAI 2025.** Deep RL chooses milling parameters to extend tool life in a custom simulator that trades production efficiency against tool efficiency *(abstract-level)*. This is the closest precedent for our slow-down action.
- **Aglogallos et al. (2026), *Frontiers in AI*.** This paper uses PPO, A2C, DDPG and SAC (Stable-Baselines3) to *estimate wear* on PHM 2010, with the wear estimate as the action, and compares against XGBoost. Its text and tables disagree in places. *Lesson:* this is RL used as a regression model, which we should not copy. Our RL makes decisions; the predictor does the estimating.
- **Nasir et al. (2025), *Operational Research*.** A Markov-decision-process model (solved exactly, not learned) for task assignment plus predictive maintenance, using open milling degradation data. It computes the policy offline *(abstract-level)*. This supports a DP-first approach.
- **Darányi, Ruppert & Abonyi (2026), *Computers & Industrial Engineering*.** "Risk-based assignment of tool maintenance tasks to opportunity windows under dynamic manufacturing conditions" *(metadata only)*. The idea is the same as our workshop's: do tool maintenance when the production schedule leaves a gap. **Note:** `research/proposals/toollife-policy.md` cites this DOI as "Errandonea et al., 2026", but Crossref lists Darányi, Ruppert and Abonyi as the authors.

**Gap.** We found no peer-reviewed work that (i) feeds a per-cut failure-probability predictor, built from real run-to-failure end-mill signals, into an RL agent, (ii) evaluates on held-out real cutters, (iii) compares against an exact DP optimum and tuned thresholds, and (iv) includes speed derating and a shared setter. That is a real niche, but a small-sample one.

### 2.2 Probabilistic remaining-life prediction feeding RL ("predict, then decide")

- **Lee & Mitici (2023), *Reliability Engineering & System Safety*.** A CNN with Monte-Carlo dropout gives a remaining-life distribution for turbofan engines, updated as new measurements arrive, and a deep RL agent decides replacements from that distribution. They report 29.3% lower cost than replacing at the mean predicted life, 95.6% of unscheduled maintenance avoided, and 12.81 cycles of wasted life on average. This is the closest template to our pipeline. Its baseline (replace at the *mean* prediction) is weak, because a tuned lower-quantile rule is the fair comparison.
- **Mitici, de Pater, Barros & Zeng (2023), *RESS*.** The same kind of probabilistic prediction, fed into a renewal-cost calculation (no RL). The cost-optimal replacement time sat near the lower bound of the 99% prediction interval, with a 53% saving against time-based maintenance and few failures relative to a perfect-prognosis benchmark. *Lesson:* a well-tuned "use the cautious end of the interval" rule is strong. It is the baseline RL must beat.
- **Xu & Zhang (2025), *Complex & Intelligent Systems*.** A predictor with MC-dropout outputs mean life, variance and failure probability. A quantile-regression DQN (QR-DQN) then chooses do-nothing, repair or replace, with a risk-aware rule for scoring actions (from the plain mean to CVaR, the average of the worst outcomes). It is compared only against other DQN variants, with no threshold or DP baseline, and the reported catastrophe rates are qualitative.
- **Chen & Liu (2025, arXiv).** Multi-agent PPO with a GRU quantile life predictor for replacement and inspection timing on engines *(abstract-level)*.
- **Offline RL.** Khorasgani et al. (2021, arXiv) learn maintenance actions offline from C-MAPSS. Bukhsh et al. (2023, *Neural Computing and Applications*) train DQN in a simulator, then conservative Q-learning (CQL) on the logged data. CQL won, but data logged from an untrained policy worked poorly because it covered too few actions. *Lesson for us:* our run-to-failure logs contain **no** "change now" actions, so offline RL has nothing to learn the change action from. Section 5.5 explains why offline RL is not the right tool here.

### 2.3 Several machines, shared crew, spare parts

- **Lee, Venkatraman & Farahat (2026, arXiv, "Planning or Learning").** This is the closest published design to our workshop. Six real bearing run-to-failure trajectories (PRONOSTIA) are replayed, with one shared maintenance crew servicing at most one asset per step, in 8,000-step episodes. DQN and PPO (64-64 networks, three seeds) are compared with a receding-horizon search planner that treats failure as forbidden and with a threshold rule. They also test action masking and reward shaping. The planner had zero failures, and its cost did not depend on the failure penalty. RL was cheaper when failures were cheap but kept making failures when they were expensive. Masking cut failures but raised cost. The threshold rule was far worse than both. They suggest DQN collapsed to "never maintain" because its discount horizon was shorter than asset lifetimes. **They trained and evaluated on the same six trajectories.** *Lessons:* hold out assets, make the discount horizon longer than a cutter's life, and report the cost-versus-failure trade-off instead of one number.
- **Ruiz Rodríguez et al. (2022), *Robotics and Computer-Integrated Manufacturing*.** Multi-agent deep RL for predictive maintenance on parallel machines, where agents coordinate which technician serves which machine. It outperformed corrective and preventive policies in simulation and in a real use case.
- **Andriotis & Papakonstantinou (2019, 2021), *RESS*.** The 2019 paper uses a factorised action space (one sub-action per component) with a shared value function and compares with DQN and with exact solutions on small systems. The 2021 paper handles risk and budget **constraints** with Lagrangian relaxation and state augmentation in a partially observed setting. These are the precedents for our factored actions and for constrained PPO.
- **Hao et al. (2023), *Information Sciences*.** Joint condition-based maintenance and spare ordering with a factorised actor-critic. It reported 17.39% and 27.95% lower cost than PPO and DQN respectively.
- **Zheng et al. (2024) and Zhu et al. (2025), *RESS*.** Maintenance plus spare ordering, solved **exactly** by value iteration where possible and by deep RL otherwise. Deep RL landed within **3.86%** (Zheng) and **4.82%** (Zhu) of the exact optimum on average, while cutting solve time by more than 90% on larger systems. Zhu's DQN beat a heuristic by 11.27%.
- **de Pater & Mitici (2021), *RESS*.** Predictive maintenance with a limited stock of spares, solved with a rolling-horizon integer program, not RL. It is an optimisation baseline for spare coupling.
- **Huang, Chang & Arinez (2020), *Expert Systems with Applications*** (deep RL preventive maintenance for serial production lines) and **Lamprecht & Huber (2021, INDIN)** (Double DQN for flow-line maintenance). Both are earlier production-line examples *(abstract-level)*.

### 2.4 Optimal stopping and the classical answer

- **Control-limit policies.** In classical replacement theory (Makis & Jardine 1992; Banjevic et al. 2001, both pre-2015 background), when the failure risk rises steadily with age and condition, the optimal policy is a threshold on the risk ("replace when hazard ≥ h*"). The threshold comes from the costs through the long-run cost rate. Our hazard-threshold baseline is exactly this rule.
- **Becker, Cheridito & Jentzen (2019), *JMLR*, "Deep optimal stopping".** This paper learns stopping rules from simulated paths with neural networks. It is useful when the state is high-dimensional. For our single cutter the state is small, so exact DP is preferable.
- **Sinclair et al. (2023), ICML, "Hindsight learning".** When all randomness comes from *outside inputs* the agent cannot influence (for us: cutter lives, orders), recorded inputs can be replayed to check "what would have happened under another action", which makes learning much more data-efficient. Our cutter lives are such inputs, except that slowing down changes how fast a life is used up. Mao et al. (2019, ICLR) make a related point: input-driven environments add variance that the value function should account for.

### 2.5 Summary table

| Paper | Setting | Method | Compared against | Headline result | What we take from it |
|---|---|---|---|---|---|
| Siraskar 2025 | Milling tool replacement, 15 env variants | REINFORCE vs SB3 DQN/A2C/PPO (untuned) | Each other | REINFORCE F1 0.61; others 0.35–0.44 | Tune; use money metrics |
| Lee & Mitici 2023 | Turbofan, probabilistic remaining life | Deep RL on remaining-life distribution | Replace at mean life | −29.3% cost | Weak baseline; use quantile rules |
| Mitici et al. 2023 | Turbofan, probabilistic remaining life | Renewal-cost optimisation (no RL) | Time-based, perfect prognosis | −53% vs time-based | Strong non-RL baseline |
| Lee, Venkatraman, Farahat 2026 | 6 replayed bearings, 1 crew | DQN, PPO, masking, shaping | Search planner, threshold | Planner 0 failures; RL cheaper only when failures are cheap | Hold out assets; long horizon; trade-off curves |
| Zheng 2024 / Zhu 2025 | Maintenance plus spares | Deep RL vs value iteration | Exact optimum, heuristic | Within 3.9% / 4.8% of optimum | RL buys scale, not optimality |
| Andriotis 2021 | Multi-component, constraints | Constrained multi-agent deep RL (Lagrangian) | Engineered policies | Beats baselines under constraints | Lagrangian breakage budget |
| Ruiz Rodríguez 2022 | Parallel machines, technicians | Multi-agent deep RL | Corrective, preventive | Large downtime reductions | Shared-technician coupling is where RL helps |
| Xu & Zhang 2025 | Turbofan | QR-DQN with CVaR-style scoring | DQN variants only | Lower reward variance | Risk-sensitive option, if time |

### 2.6 What the literature tells us

1. **Where an exact optimum can be computed, well-built deep RL comes within about 4–5% of it, not above it** (Zheng 2024; Zhu 2025). RL's value is handling problems too large for exact calculation.
2. **Big reported gains are usually against weak baselines**: replace at the mean prediction, fixed schedules, run to failure. Tuned cautious-quantile rules are much harder to beat (Mitici 2023). We must tune our baselines as carefully as the RL.
3. **Deep RL in this domain is fragile with respect to hyperparameters** (Siraskar 2025) and the discount horizon (Lee et al. 2026).
4. **Unconstrained RL accepts failures whenever the failure penalty is finite.** If the factory wants a breakage budget, it has to be a constraint (Andriotis 2021; Lee et al. 2026).
5. **Most papers evaluate in simulators, and even replay papers often test on the trajectories they trained on.** Testing on held-out real cutters is what will make our results credible.
6. **RL starts to pay off with shared resources** (crew, spares) **and multiple assets** (Ruiz Rodríguez 2022; Hao 2023; Darányi 2026). A single asset is a stopping problem.

---

## 3. Honest assessment: when is RL justified?

### 3.1 One cutter, keep or change: exact answers exist

After k cuts, the predictor gives `p(1..N), p(>N)`, so the survival curve `S(j)` is known. Write v for the profit of one good part, C_c for the cost of a planned change, C_b for the cost of a breakage, d_c and d_b for the downtime of each (in cut-times), and g for the long-run profit per cut-time of the whole policy. g matters because changing a cutter starts a fresh one, which is worth g per unit of time from then on.

**Plan-ahead rule (open-loop MPC, "Rule 3").** Score each plan "make j more parts, then change" for j = 0 … N:

```
R(j) =  sum_{i=1..j} [ v * S(i)  -  g * S(i-1) ]          # parts made, time spent cutting
      - (1 - S(j)) * (C_b + g * d_b)                        # broke before finishing the plan
      - S(j)       * (C_c + g * d_c)                        # finished the plan, planned change
```

Pick the best j. If it is 0, change now; otherwise make one part and re-plan. The one-step cost rule ("Rule 2") is the case that compares only j = 0 with j = 1. If the hazard keeps rising (`h(1) ≤ h(2) ≤ …`), the one-step comparison is already optimal: this is the "monotone case" of optimal stopping and the reason control-limit policies are optimal. g is found by bisection (Dinkelbach's method): guess g, run the policy over the training cutters, set g to the profit per cut-time achieved, and repeat until it stops changing.

**Exact closed-loop DP.** The plan-ahead rule ignores the fact that the next prediction will bring new information. The exact answer models that. The state is (age bin a, prediction bin z), where z is the predictor's one-cut breakage probability `h(1)` in about 20 bins. Breakage probability per state comes from the predictor (we trust its calibration). The probabilities of moving from z to z′ are counted from the training cutters' out-of-fold predictions. Then we solve with relative value iteration:

```
V(a, z) = max {  change: -C_c - g*d_c + V(0, z0),
                 keep:   -g + (1 - h(a,z)) * ( v + E[ V(a+1, z') | a, z ] )
                            +      h(a,z)  * ( -C_b - g*d_b + V(0, z0) ) }
```

This is roughly 150 ages × 20 bins = 3,000 states and 2 actions, which takes seconds to solve. It is the optimal policy **for the model** (predictor plus estimated transitions). It is not the optimum in reality, because the predictor is imperfect.

**Perfect-knowledge reference.** Change the cutter right after its L-th good part. Nobody can actually do this; it measures how much room is left.

**A property worth stating loudly:** for one cutter, replaying a held-out real cutter gives an **exact** answer to "what would have happened". "Keep" shows the next real prediction or the real breakage, and "change" ends the cutter's life. No simulator is involved, only the assumed costs. These results are therefore our strongest evidence (claim level 1, section 7.3).

### 3.2 What RL could add for one cutter, and why it probably will not

An RL agent trained on replays of real training cutters could in principle learn to correct a mis-calibrated predictor ("when it says 5%, it is really 10%"). With about 10 training lives, that correction is mostly noise. The honest expectation is that RL **matches** the DP within a few percent and does not beat it. That is still useful, because it validates the RL pipeline before we trust it in the workshop.

### 3.3 When RL becomes justified

RL is justified when all of the following hold. The workshop is built to make them hold, and each one is something a real tool-room faces.

1. **Coupling through shared resources.** One setter and a few spare cutters link the machines. The value of changing cutter 1 now depends on whether the setter will be needed at machine 2 in three ticks, and whether a spare will be left. Exact DP needs the product of all machines' states. Three machines at about 3,000 states each is already about 3 × 10¹⁰ states before orders and spares are added.
2. **Actions with delayed, cross-machine effects.** Slowing down costs throughput now and saves cutter life, spares and setter time later. Whether that pays depends on due dates and on the other machines.
3. **Outside random inputs that create opportunities.** A rush order or a high-value batch arriving makes a "change before the big job" decision worthwhile (the opportunity-window idea in Darányi 2026).
4. **Dynamics available only as a simulator.** The workshop is a replay plus assumptions, not a closed-form model. Note that a lookahead planner can also use the simulator, so RL's real competitor is **simulation-based lookahead (rollout)**, not just simple rules. We include one (H4 in section 6).
5. **A shop-wide risk budget.** "No more than 2 breakages per 1,000 parts" is a constraint over the whole episode, which constrained RL handles directly.

### 3.4 What RL cannot do here, stated plainly

- It cannot learn anything about cutters that is not in the 13 lifecycles and the predictor.
- It cannot learn the real effect of slowing down. It learns *our assumed* effect.
- It cannot learn real costs. It learns *our assumed* costs, which is why we sweep them.

---

## 4. The workshop environment

### 4.1 Critique of the proposed design, and the refinements

| Proposed | Problem | Refinement |
|---|---|---|
| Several machines replaying real lifecycles | Only 13 lives; heavy repetition; predictor outputs on training cutters are over-confident if produced by a model that saw them | Nested out-of-fold predictions (4.10); pools of disjoint cutters; training-only augmentation (4.11) |
| Job queue with due dates and part values | No data for it; if the agent also dispatches jobs, the action space explodes and the project turns into a scheduling project | Orders generated at random to hit a target machine utilisation; **a fixed rule** dispatches them (earliest due date to the first free machine); the agent controls only cutters and speed |
| Limited spare cutters | Good | Stock is refilled by scheduled deliveries; with no spare in stock, the machine waits |
| One setter, one change at a time | Good: this is the main coupling | Planned change takes 1 tick; recovery after a breakage takes 3 ticks of machine time and 2 of setter time; enforced by masks |
| Actions keep / change / slow / pause | "Pause" is pointless unless something is scarce; a separate choice per machine cannot express "at most one change per tick" | One joint choice covering all machines, with a mask, for up to 4 machines; separate per-machine choices plus a documented tie-break rule as the scaling variant (4.6) |
| Slow down about 20% via Taylor | The data has one speed; tool life measured in minutes is not the same as life measured in parts; the Taylor exponent n is unknown | A "damage clock" replay (4.3–4.4); life-in-parts multiplier `0.8^(1 - 1/n)`; n randomised during training; a stress test where slowing gives no benefit |
| Reward = profit in rupees | Correct, but large and spiky; end-of-episode tricks; costs unknown | Fixed scaling; episodes are *cut off* (not *ended*) at the time limit; cost-conditioned policy; cost sweep |
| Episode length (not specified) | Must cover many cutter lives and the discount horizon | T = 2,000 ticks, discount γ = 0.995 |

### 4.2 Time and entities

- **Tick** = the time to make one part at normal speed. One recorded cycle of the dataset is treated as one part. All machines decide together at every tick.
- **Machines** M = 3 by default (M = 1, 2 in the curriculum; 4 as a stretch goal). Each machine has: a mounted cutter (trajectory, damage used so far, failure point), a status (running, running slow, paused, being changed, broken and waiting, idle with no order), the current order, and how far the current part has got.
- **Setter:** one person. They are either free or busy for a known number of ticks.
- **Spares:** stock on hand (start with 3), a delivery of q cutters every R ticks (default q = 2, R = 50; a "loose" setting uses q = 3), and a storage cap.
- **Orders:** arrive at random times. Each has a batch size b (5–20 parts), a value class (contribution ₹600 / ₹1,500 / ₹4,000 per part with probabilities 0.3 / 0.5 / 0.2) and a due tick (arrival + b × U[1.3, 3.0] + an allowance for the queue). The arrival rate is set so that machine utilisation at normal speed is about 0.9 (training draws from [0.75, 1.0]). A finished machine takes the order in the queue with the earliest due date.

### 4.3 Replaying a real cutter: the damage clock

When a cutter is mounted, the environment picks a trajectory τ from the current **pool** (training pool during training, test pool during evaluation). It also picks one of the K predictor samples if they are provided, and a break point inside the breaking cycle, u ~ U(0, 1).

```
fail_at = L_τ + u           # in "recorded cycles" of damage
damage  = 0
each tick the machine cuts:   damage += δ(speed)          # δ(normal) = 1
if damage > fail_at:          breakage during this part (the part is scrapped)
when a part is completed:     agent sees pred[f][τ][floor(damage)]   (carry forward over missing cycles)
```

At normal speed this reproduces the recording exactly: L good parts, then a break during part L + 1. The environment must pass a **replay-fidelity test** that checks this for every cutter (section 4.14). The cutter breaks exactly where the real one broke, and the agent only ever sees what the predictor said about the real signals up to that point.

### 4.4 How slowing down changes a replayed cutter (Taylor)

Taylor's equation `v · T^n = C` says that tool life in minutes T grows as cutting speed v falls: `T ∝ v^(-1/n)`. If we cut at a fraction s of normal speed and keep the feed per tooth, each part takes 1/s times longer. So:

```
damage per tick at speed s      = s^(1/n)          (life in minutes is used up more slowly)
parts per tick at speed s       = s
damage per part at speed s      = s^(1/n - 1)
life in parts, multiplier       = s^(1 - 1/n)
```

With s = 0.8:

| Taylor exponent n | Life in minutes ×  | Life in parts × | Throughput |
|---|---|---|---|
| 0.25 (textbook value for carbide) | 2.44 | 1.95 | −20% |
| 0.40 | 1.75 | 1.40 | −20% |
| 0.60 (some fitted values for coated carbide) | 1.45 | 1.16 | −20% |
| 1.0 (stress test: slowing saves no cutter life per part) | 1.25 | 1.00 | −20% |

The common mistake is to apply the minutes multiplier to parts. With n = 0.25, that would claim 2.44× more parts when the true figure under this model is 1.95×.

**Assumptions to state wherever slow-down results appear:**

1. The size of the effect is assumed, not measured. Every cutter in the dataset ran at the same speed. Textbook values of n are about 0.125 for high-speed steel and 0.25 for carbide (Groover's table), while published fits for coated carbide range up to 0.6–0.8. We randomise n ~ U[0.2, 0.5] per training episode and evaluate at n = 0.25, 0.4, 0.6 and 1.0. At n = 1.0, slowing down only loses throughput, so a sound agent should stop using it.
2. Taylor's law describes gradual flank wear. Our cutters *broke*. We assume breakage follows the same "damage used up" clock (linear damage accumulation). This is plausible, because worn cutters break, but unproven.
3. At slow speed the agent still sees the predictor's output on the **normal-speed** signals recorded at the same damage. Real signals at slow speed would look different, and we cannot replay them.
4. The predictor's forecast is in units of normal-speed cuts. At slow speed, each part uses up `ρ = 0.8^(1/n - 1)` cycles of damage, so the chance of surviving j slow parts is `S(ρ · j)` (interpolated). The environment exposes ρ to the agent and to the baselines.

Other options we considered and rejected. Multiplying the hazard by a speed factor is inconsistent with a fixed real failure point. Resampling a new life from a fitted distribution throws away the real replay.

### 4.5 What the agent sees (observation)

Every item below is something a real shop would know at decision time. Values are scaled to roughly [-1, 1] by **fixed** constants (no running statistics, so nothing from the test set leaks in through normalisation).

| Group | Items | Size per machine |
|---|---|---|
| Predictor | `p(1..10)`, `p(>10)` for the current damage; P(break within 1 / 5 parts at the current speed) | 13 |
| Cutter | parts made with this cutter; damage used (in normal-speed cycles, log scale) | 2 |
| Conditions | ADOC, RDOC, cutter type of the mounted trajectory | 3 |
| Status | one-hot of 6 states; ticks until busy ends | 7 |
| Order | parts left; slack = due − now − parts left (in ticks); value class | 3 |
| **Global** | setter busy ticks; spares on hand; ticks to next delivery; orders waiting; smallest slack in queue; ρ (damage per slow part) | 6 |
| **Costs** (cost-conditioned policy only) | breakage multiplier κ, cutter price, lateness rate, utilisation | 4 |

For M = 3 this is about 100 numbers. **Left out on purpose:** cutter ID, file name, true remaining life, time left in the episode. The last one matters: with a visible countdown the agent learns to run cutters to destruction just before the episode ends, because the bill would arrive after the end (section 7.1).

### 4.6 Actions and masking

Each machine has `{RUN, SLOW, CHANGE, PAUSE}`.

**Recommended form: one joint choice with a mask.** The joint action is a single number in `Discrete(4^M)`: 64 options for 3 machines, 256 for 4. Each step the environment computes which of these are allowed and hands that list to the agent ("action masking"), so the agent can never pick a forbidden combination. Masking is a valid policy-gradient method and works much better than punishing invalid choices (Huang & Ontañón 2022).

Per-machine rules:
- RUN and SLOW are allowed only if a healthy cutter is mounted, the machine is not busy, and it has an order.
- CHANGE is allowed only if the setter is free, a spare is in stock, and the machine is not already being changed. After a breakage, CHANGE starts the 3-tick recovery.
- PAUSE is always allowed. For a busy or broken machine it means "wait".

Joint rule: **at most one CHANGE per tick**, because there is one setter. The joint mask is the product of the per-machine masks with that rule applied. Enumerate it each step; with 64 options this is cheap.

**Scaling variant (M ≥ 5):** use one choice per machine (`MultiDiscrete([4]*M)`). MaskablePPO supports per-machine masks for this. The environment then resolves conflicts by a documented rule: if several machines ask for the setter, the one with the highest one-cut breakage probability gets it and the others wait. The drawback is that part of the decision is made by a fixed rule, not learned. Action-branching networks (Tavakoli et al. 2018) or factorised actor-critics (Andriotis 2019; Hao 2023) are the literature's route if we ever go beyond 4 machines.

### 4.7 Reward: profit in rupees

All numbers are assumptions for a 10 mm solid-carbide end mill in a small Indian job shop. **They must be replaced by real numbers if anyone can get them from a machine shop.**

| Item | Symbol | Default | Swept over |
|---|---|---|---|
| Contribution per good part | v | by order class: ₹600 / ₹1,500 / ₹4,000 | × 0.5 – 2 |
| Material lost in a scrapped part | m | 0.5 × v | — |
| New cutter | c_tool | ₹3,000 | ₹1,500 – ₹6,000 |
| Setter labour per change | c_lab | ₹200 | — |
| Extra damage and inspection after a breakage | c_dmg | set so the breakage multiplier κ = 5 | κ ∈ {3, 5, 10, 20} |
| Downtime: planned change / breakage | d_c / d_b | 1 / 3 ticks | 1–2 / 2–6 |
| Lateness | c_late | ₹100 per late order per tick × value-class weight | 0 – ₹500 |
| Slow speed | s | 0.8 | — |

Each tick the reward is the sum of: + v for each good part finished; − (c_tool + c_lab) for every cutter change (planned, or the recovery change after a breakage); − (m + c_dmg) for each breakage; − c_late for each late order. The scrapped part's lost contribution and the downtime are **not** charged separately, because they already show up as parts not made. Charging them again would count them twice.

Here **κ = cost of a breakage event ÷ cost of a planned change**, both including lost production at a typical v:

```
planned change  = c_tool + c_lab + d_c·v                         = 3,000 + 200 + 1,500          = ₹4,700
breakage event  = c_tool + c_lab + m + c_dmg + (d_b + 1)·v       = 3,000 + 200 + 750 + c_dmg + 6,000
κ = 5  ⇒  c_dmg = 5 × 4,700 − 9,950 = ₹13,550        (κ = 3 ⇒ ₹4,150;  κ = 10 ⇒ ₹37,050;  κ = 20 ⇒ ₹84,050)
```

(The "+ 1" is the scrapped part itself.) κ is the single number the explainer's "a breakage costs 5, 10 or 20 times a planned change" refers to. Below κ ≈ 2.1 (c_dmg = 0) a breakage costs little more than a planned change, and running to failure becomes reasonable. Divide the reward by ₹10,000 for training. Report everything in rupees.

### 4.8 Episodes, discounting, end effects

- **Length:** T = 2,000 ticks. With lives of 14–149 parts, each machine goes through about 25 cutters per episode.
- **The time limit cuts the episode off; it does not end it.** In Gymnasium terms, `truncated=True`, `terminated=False`, so the agent's value estimate carries on past the cut-off. There is no time-left feature.
- **Discount γ = 0.995** (looks about 200 ticks ahead, about 3 median cutter lives). Lee et al. (2026) traced a DQN collapse to a discount horizon shorter than asset lives. Try γ = 0.999 in tuning. GAE λ = 0.95.
- **Starting state:** cutters mounted at random ages (pick a random trajectory, start at a random damage below its failure point) so the agent does not only see fresh starts.

### 4.9 Sources of randomness, and what is held fixed during evaluation

| Source | Training | Evaluation |
|---|---|---|
| Which trajectory a new cutter gets | random from the training pool, with augmentation | random from the test pool, from a fixed seed |
| Predictor sample (if K samples exist) | random per mounted cutter | fixed per seed |
| Break point inside the breaking cycle (u) | random | fixed per seed |
| Order arrivals, sizes, values, due dates | random | fixed per seed |
| Taylor n, utilisation, costs | random per episode (cost-conditioned policy) | each fixed grid cell |
| Starting ages | random | fixed per seed |

During evaluation every policy faces **exactly the same** sequence of random events for a given seed ("common random numbers"). Differences between policies then come from the decisions, not from luck, and paired comparisons become far more precise.

### 4.10 Leakage-safe data flow (nested cross-fitting)

**The trap.** If the predictor's outputs for the training cutters come from a predictor *trained on those same cutters*, they are over-confident. The agent learns to trust the predictor too much and then fails on held-out cutters.

**The rule.** Every prediction the agent ever sees must come from a predictor that did not train on that cutter.

```
13 cutters → 4 outer folds (each test fold has 3–4 cutters, at least one short-lived (≤53) and one long-lived (≥115))
   Example:  F1 = {10, 4, 103, 9}   F2 = {6, 2, 101, 7}   F3 = {3, 102, 105}   F4 = {5, 8}

for each outer fold f:
    train_tools = all usable cutters not in f
    # predictions the agent TRAINS on:
    for each c in train_tools:
        fit predictor on train_tools − {c}  →  pred[f][c][·]          (inner leave-one-out)
    # predictions the agent is TESTED on:
    fit predictor on train_tools        →  pred[f][c][·] for c in f
    RL training, baseline tuning, DP transition counts, augmentation fits:  train_tools only
    evaluation:                                                          f only
```

That is 4 × (~10 inner + 1 outer) ≈ 44 predictor fits. The single-cutter real-replay evaluation (section 6.1) uses ordinary leave-one-cutter-out (13 folds) with the same nested rule inside.

*Cheaper fallback, if time runs out:* use the predictor's plain leave-one-cutter-out outputs for every cutter in both pools. The predictor that produced a training cutter's outputs then saw the test cutters, which is a mild second-order leak. If used, say so in the results.

Other leakage rules:
- No checkpoint selection or early stopping on test cutters. Use a fixed training budget, chosen on fold F1's inner validation only.
- Fixed observation scaling (or, if `VecNormalize` is used, fit on training and freeze for evaluation with `training=False`).
- Baseline thresholds, g, and DP transition counts are tuned on training cutters only.
- An assertion checks that no test-pool cutter ID appears in the training pool, and that each `pred` row's provenance excludes that cutter.

### 4.11 Fighting over-fitting to about ten cutters

With about 10 training lives and about 75 cutter mounts per episode, each real life repeats about 7 times per episode. An agent can learn to recognise "the one with these conditions that dies at 49".

1. **Time-warp augmentation (training only).** Stretch a real training trajectory by w ~ LogUniform(0.8, 1.25): the new life is L′ = round(w · L), the prediction at step k′ is read from step k′/w, and the forecast survival curve is stretched the same way, `S′(j) = S(j / w)`. This creates new lives while keeping the predictor's real error pattern. Evaluation uses unwarped real held-out cutters only.
2. **Predictor-sample noise.** If the predictor provides K ensemble or MC-dropout samples, each mount uses a random one.
3. **Training mixture:** 50% real replays, 50% warped. Ablate this (section 6.7).
4. **Measure the gap.** Report the profit on training cutters next to the profit on held-out cutters for every policy. A large gap for RL and a small one for the DP means memorisation.

### 4.12 Curriculum: build and check in this order

"Curriculum" here means building and validating in stages. Weights are not carried between stages, because the observation size changes. Optionally, pad the observation to 4 machines to allow transfer.

| Stage | Setting | Exact optimum available? | What must be true before moving on |
|---|---|---|---|
| A | 1 machine, RUN/CHANGE, always an order, unlimited spares, setter always free | Yes (closed-loop DP, 3.1) | PPO and DQN within 2% of DP profit on training cutters; real-replay evaluation runs on held-out cutters |
| B (if time) | 1 machine, plus SLOW and PAUSE, orders with due dates, limited spares | Yes (DP over about 50,000 discretised states) | RL within about 3% of DP; RL's use of slow-down matches DP's in direction |
| C | 2 machines, 1 setter, spares | No | RL ≥ the best tuned heuristic on training cutters |
| D (main) | 3 machines, full workshop, cost-conditioned | No | Final evaluation (section 6) |

Stage A is the bug detector. If RL cannot match a 3,000-state DP, nothing it does in Stage D can be trusted.

### 4.13 Environment step (sketch)

```python
class Workshop(gymnasium.Env):
    # observation: Box(~100,)   action: Discrete(4**M)   + action_masks() -> bool[4**M]
    def step(self, a):
        acts = decode(a, self.M)                     # base-4 digits, one per machine
        assert self.joint_mask[a]
        ledger = Ledger()
        for i in machines_choosing(acts, CHANGE):    # at most one
            self.start_change(i, ledger)             # spares -= 1; setter busy; c_tool + c_lab charged
        for i, m in enumerate(self.machines):
            if m.busy_ticks: self.tick_busy(m); continue      # finishing a change/recovery mounts a new trajectory
            if acts[i] in (PAUSE,) or m.order is None: continue
            s = 1.0 if acts[i] == RUN else 0.8
            m.progress += s
            m.damage   += s ** (1.0 / self.n)        # Taylor damage clock
            if m.damage > m.fail_at:                 # real failure point reached
                self.breakage(m, ledger)             # part scrapped: charge m + c_dmg; status BROKEN (needs a CHANGE)
                continue
            if m.progress >= 1.0:
                m.progress -= 1.0
                ledger.revenue(m.order.value)        # good part
                m.order.parts_left -= 1
                m.obs_pred = self.pred[m.traj][floor(m.damage)]     # carry forward over gaps
                if m.order.parts_left == 0: self.dispatch_next(m)
        self.deliveries(); self.arrivals(); ledger.lateness(self.late_orders())
        self.t += 1
        return self.obs(), ledger.total / 1e4, False, self.t >= self.T, {"ledger": ledger}
```

### 4.14 Tests the environment must pass before any training

1. **Replay fidelity:** at normal speed with no changes, every cutter makes exactly L good parts and breaks on part L + 1.
2. **Damage conservation:** total damage equals the sum of per-tick increments. Alternating RUN and SLOW cannot skip the failure point.
3. **No-benefit check:** with n = 1.0, a cutter makes exactly the same number of parts at either speed. With n > 1, slowing yields fewer.
4. **Mask correctness:** never two CHANGEs in one tick, never a CHANGE with zero spares, never RUN on a broken machine. Random-policy fuzzing for 10⁶ steps finds no violations.
5. **Accounting identity:** the sum of rewards equals revenue minus all costs, from an independent ledger.
6. **Determinism:** the same seed and the same actions give an identical episode.
7. **Leakage assertions** from 4.10.

---

## 5. Algorithms

### 5.1 Recommendation

| Role | Algorithm | Library | Why |
|---|---|---|---|
| **Main** | MaskablePPO, joint `Discrete(4^M)` with mask | sb3-contrib (on Stable-Baselines3 and Gymnasium) | Stable, supports masking out of the box (including `MultiDiscrete`), well documented, easy for the team to read |
| **Comparison** | Double DQN (dueling, 3-step returns) **with masking** | ~250-line CleanRL-style script | Value-based contrast to PPO. SB3's DQN has no action masking, so the mask is applied by hand in both acting and the target max |
| **Factory-realistic** | PPO-Lagrangian with a breakage budget, PID-controlled multiplier | CleanRL-style PPO plus a cost critic (update formulas follow OmniSafe's PPOLag / CPPOPID) | A breakage budget is a constraint, not a price (2.6 point 4) |
| **Optional** | QR-DQN with CVaR action selection | sb3-contrib QR-DQN (no masking) or custom | Risk-averse variant (Xu & Zhang 2025; Dabney et al. 2018) |
| **Explainability** | Distil the PPO policy into a depth-≤5 decision tree (VIPER-style) | scikit-learn | A rule the operator can read; report how often it agrees with PPO and the profit it earns |

### 5.2 MaskablePPO settings (starting point; tune on fold F1's inner validation only)

```
policy = MlpPolicy, net_arch = dict(pi=[256,256], vf=[256,256]), activation Tanh
n_envs = 16 (DummyVecEnv if the env step is < 50 µs; SubprocVecEnv otherwise — then
              action_masks() must be a method of the env itself, the ActionMasker wrapper cannot be used)
n_steps = 1024  (16,384 transitions per update), batch_size = 4096, n_epochs = 10
learning_rate = 3e-4 → 0 linear,  gamma = 0.995,  gae_lambda = 0.95,  clip_range = 0.2
ent_coef = 0.01 → 0.001,  vf_coef = 0.5,  max_grad_norm = 0.5,  target_kl = 0.02
device = "cpu",  torch.set_num_threads(1) per process
evaluation: MaskableEvalCallback and sb3_contrib's evaluate_policy (the plain SB3 versions ignore masks)
tuning grid (16 configs, 1 seed, 5M steps): lr {3e-4, 1e-4} × ent {0.01, 0.003} × gamma {0.995, 0.999} × width {128, 256}
```

### 5.3 Masked Double DQN settings

```
buffer 1e6, batch 256, lr 1e-4, gamma 0.995, n-step 3, dueling head [256,256], Huber loss
learning_starts 2e4, train_freq 4, soft target update tau 0.005
epsilon 1.0 → 0.05 over the first 20% of steps; explore only among valid actions
store next-state mask in the buffer; target = r + γ^n · Q_target(s', argmax_{valid a'} Q_online(s', a'))
```

### 5.4 PPO-Lagrangian ("factory-realistic")

- **Cost signal:** c = 1 at each breakage. **Constraint:** expected breakages per 1,000 parts ≤ β, with β ∈ {0.5, 1, 2, 4}, calibrated so the range brackets the breakage rates of the tuned baselines.
- **Learning:** a separate value network for cost. Policy loss uses the advantage `(A_r − λ·A_c) / (1 + λ)`. After each rollout, λ is updated by a PID controller on the measured breakage rate minus β (Stooke, Achiam & Abbeel 2020), which oscillates less than plain gradient ascent on λ.
- **Why not OmniSafe directly:** its PPOLag and CPPOPID are the reference implementations. But its actor modules are Gaussian (continuous-action) types, and it has no action masking. Adding both is more work than about 80 extra lines on a CleanRL PPO.
- **Output:** a *trade-off curve* (profit against breakage rate) for β = 0.5…4, drawn next to each baseline's own curve as its threshold is swept. The honest question is: **is RL's curve above the rules' curve?**

### 5.5 Considered and not recommended

| Option | Why not (here) |
|---|---|
| A2C | Same family as PPO but less stable; nothing gained |
| SAC-discrete | Known to be unstable in discrete settings (Christodoulou 2019; Zhou et al. 2022); no advantage over PPO for 64–256 actions |
| Offline RL (CQL, IQL) | The run-to-failure logs contain no "change" actions, so offline RL has nothing to learn that action from. For keep/change, the replay already gives the exact counterfactual. Logging simulator data and then running offline RL only adds steps |
| Multi-agent RL (PettingZoo, MAPPO) | With M ≤ 4, one central agent sees everything and its joint action is exact. Multi-agent adds instability and is harder to explain; it is justified only for many machines with partial views (Ruiz Rodríguez 2022) |
| Recurrent PPO | MaskablePPO does not support recurrent networks, and the predictor's output already summarises the history. If needed, stack the last 3 predictor vectors instead |
| OmniSafe as-is | No discrete actor or masking (see 5.4) |

### 5.6 Additions that are likely worth more than another algorithm

1. **A cost-conditioned policy.** Draw κ, cutter price, lateness rate, n and utilisation at random each episode and put them in the observation. One trained policy then covers the whole cost sweep, which saves about 5× compute and makes the "cost slider" demo possible. Check it against specialist policies trained at 3 fixed cost settings; it should be within about 2% of them.
2. **Rollout lookahead (H4 in section 6.2)** as the strongest non-learned competitor. If PPO cannot beat it, the honest conclusion is "planning with the predictor suffices".
3. **Policy distillation** into a small tree, for explanation (section 5.1). Koulinas et al. (2024) used the same idea, decision trees trained on RL policies, in a production–maintenance setting.
4. **Hindsight learning** (Sinclair et al. 2023) as a stretch goal. Cutter lives and orders are outside inputs, so replayed inputs can score alternative actions directly.

### 5.7 Libraries

Gymnasium ≥ 1.0 (environment API), Stable-Baselines3 2.x with sb3-contrib 2.x (MaskablePPO), CleanRL single-file scripts (DQN, PPO-Lagrangian), NumPy (environment), PyTorch (networks), scikit-learn (distillation tree), rliable (interval estimates), pandas and matplotlib (reporting). Not needed: PettingZoo, OmniSafe (read for reference only), Ray/RLlib.

### 5.8 Compute estimate

The environment step is NumPy table lookups. Target at least 50,000 raw environment steps per second per core, and measure it in the first hour. With SB3 overhead, expect roughly 2,000–6,000 training steps per second per single-core process. Stable-Baselines3 itself warns that PPO with non-image policies is meant to run on the CPU. The GPU is for the predictor.

| Job | Steps / runs | Estimate |
|---|---|---|
| Predictor nested out-of-fold outputs (≈44 fits + 13 leave-one-out) | GPU if 1D-CNN/TCN on raw signals; CPU if gradient boosting | GBM: minutes. Deep model at 5–10 min per fit: 4–8 GPU-hours |
| Stage A (PPO, DQN) | 1M steps; 13 folds × 5 seeds × 2 algorithms | 10–20 core-hours |
| Hyperparameter grid (fold F1 inner) | 16 configs × 5M | 10–20 core-hours |
| Stage D PPO, M = 3, cost-conditioned | 20M steps; 4 folds × 5 seeds | 20–50 core-hours |
| Stage D DQN | 10M steps; 4 folds × 3 seeds | 25–50 core-hours |
| Stage D PPO-Lagrangian | 20M steps; 4 budgets × 4 folds × 3 seeds | 50–120 core-hours |
| Baseline tuning and evaluation (rollout H4 dominates) | 200 episodes × grid | 20–40 core-hours |
| **Total** | | **≈ 150–300 CPU core-hours + 0–10 GPU-hours.** On a 32–64-core machine: 5–10 hours of wall-clock time |

The step counts are planning estimates. Stage A should converge well inside 1M steps, and M = 3 within 10–20M. Learning curves decide the final budget, which is then fixed for all folds.

---

## 6. Baselines and evaluation protocol

### 6.1 Single-machine baselines (Stage A, plus the real-replay evaluation)

Each is tuned on training cutters only. Thresholds are tuned to maximise profit on training cutters, with the same tuning effort for every rule.

| ID | Rule | Notes |
|---|---|---|
| B0 | Never change (run to failure) | Lower bound |
| B1 | Fixed count: change after k parts | k tuned; optionally one k per RDOC group |
| B2 | Remaining-life quantile: change when the 10th-percentile remaining life ≤ m | The explainer's Rule 1 |
| B3 | Hazard threshold: change when `h(1) ≥ h*` | The classical control-limit policy |
| B4 | One-step expected cost, with the long-run rate g | The explainer's Rule 2 |
| B5 | Plan-ahead over N cuts, then re-plan (open-loop MPC) | The explainer's Rule 3 |
| B6 | Exact closed-loop DP on the fitted model | Section 3.1 |
| RL | PPO, DQN (Stage A agents) | |
| B7 | Perfect knowledge: change right after the L-th good part | Upper reference for measuring regret |

**Real-replay evaluation (claim level 1).** For each of the 13 cutters (leave-one-out, with nested predictions), run every policy along the real recording and record the exact outcome: broke or not, parts made, share of life used, and profit per cut-time under each cost setting. Output: a 13-row table per policy, plus totals computed as total profit ÷ total time across cutters (the renewal-reward ratio).

### 6.2 Multi-machine baselines (Stages C and D)

| ID | Rule | Notes |
|---|---|---|
| H1 | Fixed count per machine; setter serves the earliest request | |
| H2 | Hazard threshold per machine; setter goes to the highest hazard; pause a machine whose hazard is above the threshold while the setter is busy or no spare is in stock | No slow-down |
| H3 | Per-machine expected-cost rule (B4), with setter priority by expected saving; slow down when order slack > σ* **and** hazard > h_s; pause when changing is impossible and breakage risk exceeds the margin of the next part | Strongest simple rule; σ*, h_s and thresholds grid-searched on training cutters (≤ 200 configurations, similar to the RL tuning budget) |
| H4 | **Rollout lookahead:** at each tick, score about 4M + 1 candidate joint actions (H3's choice, and each single-machine change to it) by simulating 16 futures over 15 ticks with H3 as the follow-on policy. Futures draw breakages from the *predictor's* probabilities, never the true lives | Strongest non-learned competitor; NumPy-vectorised, about 5 ms per decision |
| H5 | **Perfect-prognosis H3:** H3 given each mounted cutter's true remaining life | Upper reference. Not a proven optimum, so call it a "perfect-prognosis reference" |
| RL | PPO, DQN, PPO-Lagrangian | |

### 6.3 Splits, seeds, and paired scenarios

- **Outer split:** 4 folds of held-out cutters (4.10). Each policy is trained and tuned on training cutters and evaluated on test cutters.
- **Training seeds:** 5 per fold for PPO (10 if time allows), 3 for DQN and PPO-Lagrangian.
- **Evaluation episodes:** 100 per fold per scenario, T = 2,000, M = 3, with seeds 1…100 **shared by every policy** (common random numbers, 4.9).
- **Scenarios:** the cost grid in 6.6.
- **Also report** each policy's profit on the training cutters, to expose memorisation (4.11).

### 6.4 Metrics

| Metric | Definition |
|---|---|
| **Profit** (primary) | ₹ per 1,000 ticks |
| Breakage rate | breakages per 1,000 parts; share of cutters that broke |
| Life used | for cutters changed before breaking: parts made ÷ (L + 1); wasted parts |
| Changes | planned changes per 1,000 parts; spare stockout ticks |
| Lateness | share of orders late; ₹ lateness; average lateness |
| Throughput and behaviour | parts per tick; share of time slow; share of time paused; setter utilisation |
| Regret | (perfect-prognosis reference − policy) profit, in ₹ and % |
| Tail risk | 5th-percentile episode profit; average of the worst 10% of episodes (CVaR at 10%) |
| Decision time | ms per decision (H4 against the RL forward pass) |

### 6.5 Statistics: what the sample size really is

- **The real sample size is 13 cutters, not 100 × 5 × 4 episodes.** Episodes in one fold reuse the same 2–4 test cutters, so they are not independent evidence about new cutters.
- **Confidence intervals:** a hierarchical bootstrap that resamples test cutters (or folds) first, then training seeds, then episodes; 10,000 resamples; 95% percentile intervals.
- **Policy comparisons:** paired differences on identical scenarios (common random numbers), bootstrapped as above. Report the mean difference with its interval and the probability of improvement P(RL > best baseline) across runs (rliable; Agarwal et al. 2021).
- **Learning curves:** interquartile mean (IQM) across fold × seed runs, with stratified-bootstrap intervals (rliable).
- **No per-episode t-tests,** and no "best seed" reporting (Henderson et al. 2018).

### 6.6 Sensitivity (cost and assumption sweep)

| Factor | Values |
|---|---|
| Breakage multiplier κ | 3, 5, 10, 20 |
| Cutter price | ₹1,500, ₹3,000, ₹6,000 |
| Lateness rate | low, medium, high |
| Taylor exponent n | 0.25, 0.4, 0.6, 1.0 (no benefit) |
| Utilisation | 0.8, 0.9, 1.0 |
| Spares | tight (2 per 50 ticks), loose (3 per 50 ticks) |

That gives 4 × 3 × 3 × 4 × 3 × 2 = 864 cells. Evaluate RL (cost-conditioned) and H1–H3 on all of them, and H4 and the specialist RL policies on 12 anchor cells. Report the **win rate**: the share of cells where RL beats the best heuristic with the paired interval excluding zero. This matches the explainer's "holds in at least 70% of cost settings" rule.

### 6.7 Ablations (each one answers a plain question)

| Ablation | Question |
|---|---|
| No SLOW action | How much of RL's gain comes from slowing down, which rests entirely on the Taylor assumption? |
| No PAUSE action | Is pausing ever useful? |
| Observation without the predictor (age and conditions only) | **Do the sensors matter for the decision**, not just for prediction accuracy? |
| Forecast of 1 cut instead of 10 | Does a longer forecast help? |
| Mask replaced by a penalty for invalid actions | Reproduces the masking result in our setting |
| Without time-warp augmentation | Does augmentation reduce the training-versus-test gap? |
| Calibrated vs uncalibrated predictor | How much do decisions depend on honest probabilities? |
| Cost-conditioned vs specialist | Is one policy for all costs good enough? |

### 6.8 Success criteria (fixed before seeing test results)

- **S1, the sanity check:** in Stage A, RL is within 2% of the DP's profit on training cutters and within 3% on held-out cutters.
- **S2, the main question:** in Stage D on held-out cutters, RL's profit is at least 3% above the best tuned heuristic (H3 or H4), without a higher breakage rate (or with RL's trade-off curve above the heuristic's), with the paired 95% interval excluding zero, in at least 70% of the cost grid.
- **S3, factory-realistic:** PPO-Lagrangian keeps the breakage budget on held-out cutters (within the interval) and earns at least as much as the best heuristic tuned to the same budget.
- **If S2 fails,** we report that "rules with the predictor were as good as RL in our workshop". That is a legitimate and useful finding, consistent with 2.6.

---

## 7. Pitfalls and honest claims

### 7.1 Reward hacking and exploiting the simulator

"Reward hacking" means the agent finds a way to score well that we did not intend, usually by exploiting a gap in the simulator or the reward (Skalse et al. 2022).

| Exploit | How it shows up | Prevention or check |
|---|---|---|
| Always slow | Slow share near 100% | Real throughput cost via utilisation ≈ 0.9; the n = 1.0 test must drive the slow share to about 0 |
| Pause forever | Paused share high while orders wait | Lost contribution and lateness are charged; check pause share against queue length |
| Burn cutters before the episode ends | Breakages bunched at the end | No time-left feature; truncation (not termination); compare breakage timing across the episode |
| Re-rolling short-lived cutters | Changes a brand-new cutter early when its conditions match a short life in training | Legitimate only if the predictor says so; check on held-out cutters; ablate condition features |
| Rounding tricks in the damage clock | Alternating RUN and SLOW to dodge the failure point | Damage-conservation test (4.14) |
| Mask holes | Changes during recovery, two changes in a tick | Mask fuzzing (4.14) |
| Accounting holes | Breakage on an order's last part costs nothing | Ledger identity test; spot-check 20 breakage events by hand |
| Learning the simulator's order generator | Behaviour tied to exact arrival patterns | Randomise generator settings in training; evaluate at other utilisations |

### 7.2 Over-fitting to replayed trajectories

- Ten training lives are very few. Watch the training-versus-test gap per policy (4.11).
- Conditions plus age can almost identify a cutter in this dataset. Ablate the conditions.
- Augmentation helps, but it also teaches the agent our augmentation. Never report results on augmented data.
- The predictor's errors on test cutters may differ from its out-of-fold errors on training cutters. That is the real deployment risk, and it is why the test pool exists.

### 7.3 Claim levels and wording

| Level | What it rests on | Allowed wording |
|---|---|---|
| **1. Real held-out cutters** (single machine, keep/change) | Real lifecycles, real predictor outputs, exact "what would have happened"; only costs assumed | "On 13 real cutters, each judged by a model that never saw it, policy X changed the cutter before it broke in a of 13 cases and used c% of its life on average. Under assumed costs (κ = 5), it earned ₹… per part, d% more than the best fixed-count rule." |
| **2. Replay-based simulation** (workshop) | Real lives and predictions; everything else assumed | "In a simulated workshop where cutter lifetimes and sensor-based predictions come from real held-out cutters, but orders, the setter, spares, costs and the speed–life relationship are assumed, the RL policy earned x% more simulated profit than the best rule, with y breakages per 1,000 parts. This held in z% of cost settings." |
| **3. Synthetic** | Augmented or synthetic trajectories | Training only. Never a headline result. |

**Never write:** "RL reduces factory costs by X%"; "the agent learned that slowing down extends tool life" (it learned *our assumed* Taylor effect); "RL found the optimal policy"; "validated on real machines".
**Always say,** next to any slow-down result: "the speed–life effect is assumed from Taylor's equation; all cutters in the dataset ran at the same speed."

---

## 8. Two-day build plan

**Day 1, morning.** Trajectory store (sorting, gaps, duplicate, cutter 11 excluded) and the predictor output contract. If the real predictor is not ready, use a stand-in: a Weibull model on age and conditions, with nested fitting, so everything downstream can be built and tested. Build the single-machine environment, the real-replay evaluator, B0–B5, and the DP (B6). Write the environment tests.

**Day 1, afternoon.** Stage A PPO and DQN against the DP, then fix whatever disagrees. Build the workshop environment (masks, orders, spares, setter, Taylor clock) and H1–H3. Calibrate the order generator so H3 at utilisation 0.9 has about 10–20% late orders.

**Day 1, night.** Hyperparameter grid on fold F1's inner validation. Launch Stage D PPO (4 folds × 5 seeds) and DQN runs.

**Day 2, morning.** PPO-Lagrangian with the 4 budgets. Rollout baseline H4. Evaluation harness with common random numbers and the hierarchical bootstrap.

**Day 2, afternoon.** Sensitivity grid, ablations, distillation tree, plots, results write-up using the claim levels in 7.3.

**If time runs short, drop in this order:** Stage B DP → DQN in the workshop (keep it in Stage A) → 4-machine runs → QR-DQN/CVaR → hindsight learning.

---

## 9. Decisions for the team

1. **Costs.** Can anyone get rough real numbers (cutter price, setter time, value of a scrapped part) from a machine shop? They drop straight into section 4.7.
2. **Breakage budget** for PPO-Lagrangian. Proposed: report the whole curve for β ∈ {0.5, 1, 2, 4} breakages per 1,000 parts, rather than picking one value.
3. **Machines:** 3 (recommended) or 4.
4. **The wear-limit datasets:** robustness test after the main build (recommended), or a "family B" machine inside the main workshop.
5. **Predictor readiness:** the RL build only needs the output tables in 1.3. A stand-in predictor unblocks day 1.

---

## 10. References

**RL and decision-making for tools and maintenance**

- Siraskar, R., Kumar, S., Patil, S., Bongale, A., Kotecha, K., Kulkarni, A. (2025). An empirical study of the naïve REINFORCE algorithm for predictive maintenance. *Discover Applied Sciences* 7:210. https://doi.org/10.1007/s42452-025-06613-1
- Siraskar, R., Kumar, S., Patil, S., Bongale, A., Kotecha, K. (2023). Reinforcement learning for predictive maintenance: a systematic technical review. *Artificial Intelligence Review* 56:12885–12947. https://doi.org/10.1007/s10462-023-10468-6
- Ogunfowora, O., Najjaran, H. (2023). Reinforcement and deep reinforcement learning-based solutions for machine maintenance planning, scheduling policies, and optimization. *Journal of Manufacturing Systems* 70:244–263. https://doi.org/10.1016/j.jmsy.2023.07.014
- Lee, J., Mitici, M. (2023). Deep reinforcement learning for predictive aircraft maintenance using probabilistic Remaining-Useful-Life prognostics. *Reliability Engineering & System Safety* 230:108908. https://doi.org/10.1016/j.ress.2022.108908
- Mitici, M., de Pater, I., Barros, A., Zeng, Z. (2023). Dynamic predictive maintenance for multiple components using data-driven probabilistic RUL prognostics: the case of turbofan engines. *RESS* 234:109199. https://doi.org/10.1016/j.ress.2023.109199
- de Pater, I., Mitici, M. (2021). Predictive maintenance for multi-component systems of repairables with Remaining-Useful-Life prognostics and a limited stock of spare components. *RESS* 214:107761. https://doi.org/10.1016/j.ress.2021.107761
- Xu, Z., Zhang, Q. (2025). Predictive maintenance optimization for industrial equipment via reliable prognosis and risk-aware reinforcement learning. *Complex & Intelligent Systems* 12:11. https://doi.org/10.1007/s40747-025-02127-w
- Lee, X. Y., Venkatraman, C., Farahat, A. (2026). Planning or Learning: Reliability and Cost in Multi-Asset Maintenance. arXiv:2609.13566. https://arxiv.org/abs/2609.13566
- Ruiz Rodríguez, M. L., Kubler, S., de Giorgio, A., Cordy, M., Robert, J., Le Traon, Y. (2022). Multi-agent deep reinforcement learning based predictive maintenance on parallel machines. *Robotics and Computer-Integrated Manufacturing* 78:102406. https://doi.org/10.1016/j.rcim.2022.102406
- Andriotis, C. P., Papakonstantinou, K. G. (2019). Managing engineering systems with large state and action spaces through deep reinforcement learning. *RESS* 191:106483. https://doi.org/10.1016/j.ress.2019.04.036
- Andriotis, C. P., Papakonstantinou, K. G. (2021). Deep reinforcement learning driven inspection and maintenance planning under incomplete information and constraints. *RESS* 212:107551. https://doi.org/10.1016/j.ress.2021.107551
- Hao, S., et al. (2023). Deep reinforce learning for joint optimization of condition-based maintenance and spare ordering. *Information Sciences* 634:85–100. https://doi.org/10.1016/j.ins.2023.03.064
- Zheng, M., Su, Z., Wang, D., Pan, E. (2024). Joint maintenance and spare part ordering from multiple suppliers for multicomponent systems using a deep reinforcement learning algorithm. *RESS* 241:109628. https://doi.org/10.1016/j.ress.2023.109628
- Zhu, Y., Zheng, M., Su, Z., Xia, T., Lin, J., Pan, E. (2025). Deep reinforcement learning for joint optimization of maintenance and spare parts ordering considering spare parts supply uncertainty. *RESS* 264:111385. https://doi.org/10.1016/j.ress.2025.111385
- Huang, J., Chang, Q., Arinez, J. (2020). Deep reinforcement learning based preventive maintenance policy for serial production lines. *Expert Systems with Applications* 160:113701. https://doi.org/10.1016/j.eswa.2020.113701
- Lamprecht, R., Huber, M. (2021). Reinforcement learning based condition-oriented maintenance scheduling for flow line systems. IEEE INDIN 2021. arXiv:2108.12298. https://arxiv.org/abs/2108.12298
- Bukhsh, Z. A., Molegraaf, H., Jansen, N. (2023). A maintenance planning framework using online and offline deep reinforcement learning. *Neural Computing and Applications*. https://doi.org/10.1007/s00521-023-08560-7
- Khorasgani, H., et al. (2021). An offline deep reinforcement learning for maintenance decision-making. arXiv:2109.15050. https://arxiv.org/abs/2109.15050
- Chen, Y., Liu, C. (2025). Sequential multi-objective multi-agent reinforcement learning approach for predictive maintenance. arXiv:2502.02071. https://arxiv.org/abs/2502.02071
- Nasir, A., Mekid, S., Sawlan, Z., Alsawafy, O. (2025). Optimized task assignment and predictive maintenance for industrial machines using Markov decision process. *Operational Research* 25:96. https://doi.org/10.1007/s12351-025-00976-4
- Darányi, A., Ruppert, T., Abonyi, J. (2026). Risk-based assignment of tool maintenance tasks to opportunity windows under dynamic manufacturing conditions. *Computers & Industrial Engineering* 212:111716. https://doi.org/10.1016/j.cie.2025.111716
- Ferrisi, S., Afrasiabi, M., Guido, R., Umbrello, D., Ambrogio, G., Bambach, M. (2025). Deep reinforcement learning-based parameter optimization in milling: a novel approach for enhancing tool life. Green-Aware AI @ ECAI 2025, CEUR-WS Vol-4165, 128–139. https://ceur-ws.org/Vol-4165/paper3.pdf
- Aglogallos, A., Bousdekis, A., Kontos, S., Mentzas, G. (2026). Health state prediction with reinforcement learning for predictive maintenance. *Frontiers in Artificial Intelligence* 8:1720140. https://doi.org/10.3389/frai.2025.1720140
- Koulinas, G., Paraschos, P., Koulouriotis, D. (2024). A machine learning framework for explainable knowledge mining and production, maintenance, and quality control optimization in flexible circular manufacturing systems. *Flexible Services and Manufacturing Journal* 36(3). https://doi.org/10.1007/s10696-024-09537-x

**Stopping, planning, and outside-input problems**

- Becker, S., Cheridito, P., Jentzen, A. (2019). Deep optimal stopping. *JMLR* 20(74):1–25. https://jmlr.org/papers/v20/18-232.html
- Makis, V., Jardine, A. K. S. (1992). Optimal replacement in the proportional hazards model. *INFOR* 30(2):172–183. (Background.)
- Banjevic, D., Jardine, A. K. S., Makis, V., Ennis, M. (2001). A control-limit policy and software for condition-based maintenance optimization. *INFOR* 39(1):32–50. (Background.)
- Sinclair, S. R., et al. (2023). Hindsight learning for MDPs with exogenous inputs. ICML, PMLR 202:31877–31914. https://proceedings.mlr.press/v202/sinclair23a.html
- Mao, H., Venkatakrishnan, S. B., Schwarzkopf, M., Alizadeh, M. (2019). Variance reduction for reinforcement learning in input-driven environments. ICLR. https://arxiv.org/abs/1807.02264
- Bertsekas, D. P. (2020). *Rollout, Policy Iteration, and Distributed Reinforcement Learning*. Athena Scientific.
- Groover, M. P. *Fundamentals of Modern Manufacturing* (Taylor tool-life parameter table: n ≈ 0.125 for HSS, 0.25 for carbide, 0.6 for ceramic).

**RL methods**

- Schulman, J., et al. (2017). Proximal policy optimization algorithms. https://arxiv.org/abs/1707.06347
- Huang, S., Ontañón, S. (2022). A closer look at invalid action masking in policy gradient algorithms. FLAIRS-35. https://arxiv.org/abs/2006.14171
- Huang, S., et al. (2022). The 37 implementation details of proximal policy optimization. ICLR Blog Track. https://iclr-blog-track.github.io/2022/03/25/ppo-implementation-details/
- Andrychowicz, M., et al. (2021). What matters in on-policy reinforcement learning? ICLR. https://arxiv.org/abs/2006.05990
- Hessel, M., et al. (2018). Rainbow: combining improvements in deep reinforcement learning. AAAI. https://arxiv.org/abs/1710.02298
- Dabney, W., Rowland, M., Bellemare, M. G., Munos, R. (2018). Distributional reinforcement learning with quantile regression. AAAI. https://arxiv.org/abs/1710.10044
- Christodoulou, P. (2019). Soft actor-critic for discrete action settings. https://arxiv.org/abs/1910.07207
- Zhou, H., et al. (2022). Revisiting discrete soft actor-critic. https://arxiv.org/abs/2209.10081
- Tavakoli, A., Pardo, F., Kormushev, P. (2018). Action branching architectures for deep reinforcement learning. AAAI. https://arxiv.org/abs/1711.08946
- Ray, A., Achiam, J., Amodei, D. (2019). Benchmarking safe exploration in deep reinforcement learning (Safety Gym). OpenAI. https://cdn.openai.com/safexp-short.pdf
- Stooke, A., Achiam, J., Abbeel, P. (2020). Responsive safety in reinforcement learning by PID Lagrangian methods. ICML. https://arxiv.org/abs/2007.03964
- Ji, J., et al. (2024). OmniSafe: an infrastructure for accelerating safe reinforcement learning research. *JMLR* 25(285):1–6. https://jmlr.org/papers/v25/23-0681.html
- Chow, Y., Ghavamzadeh, M., Janson, L., Pavone, M. (2018). Risk-constrained reinforcement learning with percentile risk criteria. *JMLR* 18(167). https://jmlr.org/papers/v18/15-636.html
- Greenberg, I., Chow, Y., Ghavamzadeh, M., Mannor, S. (2022). Efficient risk-averse reinforcement learning. NeurIPS. https://arxiv.org/abs/2205.05138
- Levine, S., Kumar, A., Tucker, G., Fu, J. (2020). Offline reinforcement learning: tutorial, review, and perspectives on open problems. https://arxiv.org/abs/2005.01643
- Kumar, A., Zhou, A., Tucker, G., Levine, S. (2020). Conservative Q-learning for offline reinforcement learning. NeurIPS. https://arxiv.org/abs/2006.04779
- Kostrikov, I., Nair, A., Levine, S. (2022). Offline reinforcement learning with implicit Q-learning. ICLR. https://arxiv.org/abs/2110.06169
- Bastani, O., Pu, Y., Solar-Lezama, A. (2018). Verifiable reinforcement learning via policy extraction (VIPER). NeurIPS. https://arxiv.org/abs/1805.08328
- Tobin, J., et al. (2017). Domain randomization for transferring deep neural networks from simulation to the real world. IROS. https://arxiv.org/abs/1703.06907
- Skalse, J., Howe, N., Krasheninnikov, D., Krueger, D. (2022). Defining and characterizing reward hacking. NeurIPS. https://arxiv.org/abs/2209.13085

**Evaluation and libraries**

- Agarwal, R., Schwarzer, M., Castro, P. S., Courville, A., Bellemare, M. G. (2021). Deep reinforcement learning at the edge of the statistical precipice. NeurIPS. https://arxiv.org/abs/2108.13264
- Henderson, P., et al. (2018). Deep reinforcement learning that matters. AAAI. https://arxiv.org/abs/1709.06560
- Raffin, A., et al. (2021). Stable-Baselines3: reliable reinforcement learning implementations. *JMLR* 22(268). https://jmlr.org/papers/v22/20-1364.html
- sb3-contrib MaskablePPO documentation. https://sb3-contrib.readthedocs.io/en/master/modules/ppo_mask.html
- Huang, S., et al. (2022). CleanRL: high-quality single-file implementations of deep reinforcement learning algorithms. *JMLR* 23(274). https://jmlr.org/papers/v23/21-1342.html
- Towers, M., et al. (2024). Gymnasium: a standard interface for reinforcement learning environments. https://arxiv.org/abs/2407.17032
- Terry, J. K., et al. (2021). PettingZoo: Gym for multi-agent reinforcement learning. NeurIPS Datasets and Benchmarks. https://arxiv.org/abs/2009.14471

**Data**

- Piecuch, G., Żabiński, T. (2025). A new open dataset from a milling process — data for classification and estimation of tool life. *Scientific Data*. https://www.nature.com/articles/s41597-025-04923-y ; files: https://doi.org/10.6084/m9.figshare.28589216

*Verification note: bibliographic details were checked against Crossref, publisher pages or arXiv. Papers marked "(abstract-level)" or "(metadata only)" in section 2 were not read in full. The web-search budget ran out near the end of the research pass, so Darányi et al. (2026) is cited from Crossref metadata only.*
