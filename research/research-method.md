# Research method and actual constraints

## What is constrained

1. **Calendar:** a polished system must be achievable in 8–12 weeks.
2. **Human effort:** the student team should mainly understand the problem, make
   design choices, validate results, and present. Codex can implement the data,
   modeling, experiments, application, and documentation.
3. **Explanatory burden:** the model can use deep learning, a GNN, RL, SFT, LoRA,
   multimodal fusion, or an optimizer, but the team must be able to explain the
   architecture, inputs, outputs, loss/reward, evaluation, and failure modes.
4. **Research ambition:** novelty must not depend on inventing a new ML theory or
   proving a novel learning algorithm.
5. **Completion quality:** one complete, evaluated system is worth more than a
   collection of disconnected model demos.
6. **Manufacturing relevance:** the problem must be anchored in product design,
   process engineering, production, quality, supply networks, factory operations,
   maintenance, human factors, or circular manufacturing.

## What is not constrained

- Public dataset size.
- Normal cloud/GPU use or paid compute.
- Using multiple modalities or combining several datasets.
- Fine-tuning and SFT of an existing model.
- RL when a credible simulator, state, action, reward, and baseline exist.
- GNNs when the object is naturally a graph, such as a CAD B-Rep, BOM, routing
  network, assembly, or operation precedence graph.
- A complex product experience, digital twin, simulator, interactive dashboard,
  explainability layer, or evaluation harness implemented by Codex.

Training a foundation model from scratch is outside scope because it adds cost and
risk without strengthening the manufacturing contribution.

## Breadth procedure

The opportunity universe is a morphological analysis, not a superficial list of
random titles. It crosses:

- **50 manufacturing contexts**, from CAD, process planning, quotation, supply
  networks, machining, welding, forming, additive manufacturing, inspection, and
  metrology through maintenance, ergonomics, digital thread, and remanufacturing;
- **20 intervention patterns**, including forecasting, anomaly detection,
  diagnosis, RUL, virtual metrology, surrogates, parameter recommendation,
  control, sequencing, routing, active sampling, causal analysis, uncertainty,
  counterfactuals, optimization, RL, GNN reasoning, grounded LLMs, multimodal
  fusion, and inverse design.

This produces exactly 1,000 combinations. Two high-value combinations per
context produce a 100-project longlist. The shortlist is then evidence-driven,
not automatically chosen from the matrix.

## Hard gates for a finalist

A concept is rejected as a flagship if any gate fails:

1. There is no concrete manufacturing decision after the model output.
2. A non-AI rule or ordinary optimization solves the whole problem just as well.
3. There is no credible public dataset, simulator, or defensible synthetic-data
   route within two weeks.
4. Success cannot be measured against a baseline.
5. The contribution is only a chatbot, a generic dashboard, or another standard
   defect classifier.
6. The concept substantially duplicates a project already in the class sheet.
7. The critical path requires physical experiments or expert labeling that the
   team cannot obtain in time.

## Weighted ranking rubric (100 points)

| Criterion | Weight | What earns the points |
|---|---:|---|
| Industrial value | 15 | Avoids scrap/downtime, improves yield/flow, or reduces engineering work |
| AI necessity | 10 | AI handles perception, uncertainty, complex interactions, or sequential decisions that rules alone cannot |
| Differentiation | 15 | Goes beyond a crowded prediction demo and the known class proposals |
| Data/simulator credibility | 15 | Public, documented, relevant, and usable without new physical collection |
| Evaluation rigor | 10 | Strong baselines, leakage-safe splits, operational and ML metrics |
| Demo impact | 10 | A visible input → reasoning → manufacturing-action story |
| Explainability | 10 | Architecture, decision logic, and failure behavior can be taught clearly |
| 8–12 week execution fit | 10 | End-to-end implementation has a bounded critical path |
| Fallback strength | 5 | A smaller publishable system remains if one data/model component fails |

Compute cost and dataset size are deliberately not negative criteria.
