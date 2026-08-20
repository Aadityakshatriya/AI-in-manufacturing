# Evidence base: where AI is useful in manufacturing

Research cutoff: 21 August 2026. Preference was given to official datasets,
standards bodies, benchmark owners, and primary papers. This file records what a
source establishes for project selection; it is not a general literature review.

## Cross-manufacturing findings

### 1. The opportunity is not “AI everywhere”; it is connected decisions

NIST's **2026 Roadmap on Artificial Intelligence and Machine Learning for Smart
Manufacturing** covers industrial data, multimodal sensing, autonomous systems,
additive manufacturing, laser processes, digital twins, supply networks,
robotics, sustainability, physics-informed ML, generative and semantic AI,
predictive control, reliability, and data-centric metrology. Its recurring gaps
are data quality, domain shift, uncertainty, explainability, cross-machine
generalization, simulation-to-real transfer, online adaptation, and the failure
to connect isolated point solutions into manufacturing operations.

- [NIST publication page](https://www.nist.gov/publications/2026-roadmap-artificial-intelligence-and-machine-learning-smart-manufacturing)
- [NIST roadmap PDF](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=960263)

Two independent reviews reinforce the same selection lesson. Manufacturing AI is
already rich in predictive-maintenance and classification studies; production
decisions, reliable deployment, and interpretability receive less coverage.

- [CIRP review of AI in manufacturing](https://www.sciencedirect.com/science/article/pii/S000785062400115X)
- [Journal of Manufacturing Systems review of IoT/ML applications](https://www.sciencedirect.com/science/article/pii/S0278612524000773)

**Project implication:** favor a system that explicitly connects perception or
prediction to inspection, control, planning, or recovery, and test the complete
decision loop.

### 2. Digital twins are useful only when they support prediction and action

NIST describes digital twins as fit-for-purpose digital representations tied to
real manufacturing use cases and highlights measurement science, verification,
validation, and uncertainty. NIST's AIMS and AI2AM programs similarly focus on
human-machine decision support, reliable process knowledge, and additive
manufacturing informatics—not merely a 3D animation.

- [NIST Digital Twins for Advanced Manufacturing](https://www.nist.gov/programs-projects/digital-twins-advanced-manufacturing)
- [NIST Augmented Intelligence for Manufacturing Systems](https://www.nist.gov/programs-projects/augmented-intelligence-manufacturing-systems-aims)
- [NIST AI2AM](https://www.nist.gov/programs-projects/advanced-informatics-and-artificial-intelligence-additive-manufacturing)

**Project implication:** every proposed “twin” in the shortlist includes a
surrogate/predictive state, uncertainty, a decision, and a counterfactual or
closed-loop experiment.

## Product engineering, CAD, and process planning

- [Autodesk Fusion 360 Gallery](https://www.research.autodesk.com/publications/fusion-360-gallery/) provides 8,625 human CAD design sequences and a Gym-style design environment. It is useful for learning/edit-sequence research, but not by itself a machining process-plan benchmark.
- [MFCAD++](https://pure.qub.ac.uk/en/datasets/mfcad-dataset-dataset-for-paper-hierarchical-cadnet-learning-from/) contains 59,655 B-Rep CAD models with 3–10 interacting machining features, providing a credible supervised path for feature segmentation.
- [Hierarchical CADNet](https://doi.org/10.1016/j.cad.2022.103226) and [BRepGAT](https://academic.oup.com/jcde/article/10/6/2384/7453688) establish that face-adjacency GNNs are an understandable, high-performing model family for machining-feature recognition.
- [TriView2CAD](https://www.modelscope.cn/datasets/zhuofanChen/TriView2CAD) provides roughly 200,000 synthetic samples connecting engineering drawings, JSON, DXF/PNG, STEP, and B-Rep representations.
- [NIST CAD models and STEP files with PMI](https://catalog.data.gov/dataset/nist-cad-models-and-step-files-with-pmi) provide public parts with semantic product-manufacturing information and GD&T.
- [LLM-based CAPP research](https://doi.org/10.1016/j.rcim.2026.103233) and [LLMs for composite process planning](https://doi.org/10.1016/j.mfglet.2024.03.010) show that language models can help process planning, but a credible course project must ground them in extracted geometry, machine/tool constraints, and a deterministic validator.

**Opportunity:** CAD → manufacturing-feature graph → feasible operation plan →
DFM/cost explanation. The risk is not model training; it is obtaining trustworthy
ground truth for full process plans and quotations. The fallback is a rigorously
evaluated feature-recognition and rule-valid DFM system.

## Welding and joining

- [Intel Robotic Welding Multimodal Dataset](https://huggingface.co/datasets/IntelLabs/Intel_Robotic_Welding_Multimodal_Dataset) is a 39.9 GB research dataset with more than 4,000 annotated samples from an automotive production floor. Each weld can include video, 16 kHz audio, welding time-series data, five post-weld images, and process settings across 236 sessions and 12 intended defect categories.
- [Intel's associated paper](https://arxiv.org/abs/2409.02290) demonstrates unsupervised defect detection from audio and video.
- [Predictive Quality in Arc Welding data](https://zenodo.org/records/15101072) provides high-frequency current and voltage measurements as a non-gated fallback.
- [Multimodal thermographic welding dataset and paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12301811/) combine thermography, voltage/current, wire feed, laser profilometry, and penetration-related information.

The Intel dataset is gated under a research-only license, and its card explicitly
warns that labels represent intended defects without expert post-weld validation,
that one weld can contain multiple defects, and that devices can be slightly
misaligned. Those are research opportunities—robust learning, alignment,
uncertainty, and cross-modal ablation—but also schedule risks.

**Opportunity:** predict defect risk early in a weld, show which sensor/modal
window caused the warning, quantify uncertainty, and search the process-setting
space for a feasible rescue action. This is materially stronger than post-weld
image classification.

## Forming, forging, and simulation-to-reality

- [Sim-to-real sheet-forming dataset](https://tudatalib.ulb.tu-darmstadt.de/items/5fff86aa-5a8c-4b80-b1ce-470744bd0f06) is a 2.92 GB open dataset explicitly designed to study how finite-element model complexity affects prediction on a real progressive deep-drawing process.
- [STRATH radial-forging sensor dataset](https://zenodo.org/records/3405265) contains sensor traces for 81 forged parts, 18 post-process CMM dimensions, a machine-failure episode, and public tutorial notebooks.
- [Multi-stage transfer-press setup dataset](https://doi.org/10.25835/r9yt5ut7) provides recent experimental sheet-metal forming data.
- [NUMISHEET 2025 benchmark data](https://research.aalto.fi/en/datasets/numisheet-2025-scientific-benchmark-dataset/) provide experimental forming data for calibrating and validating material models.

**Opportunity:** use simulation data to learn a fast quality surrogate, calibrate
or fine-tune it on limited real data, quantify the reality gap, and recommend
process settings. The mechanics are visible and the ML can remain a small neural
network, Gaussian process, or gradient-boosted model.

## Virtual metrology and adaptive inspection

NIST's 2025 study of semiconductor virtual metrology proposes an online Gaussian
process that adapts to drift and uses uncertainty to decide when expensive
physical metrology is necessary. It is validated on a public chemical mechanical
planarization dataset.

- [NIST publication page](https://www.nist.gov/publications/comparative-study-semiconductor-virtual-metrology-methods-and-novel-algorithmic)
- [NIST paper PDF](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=958452)
- [Virtual-metrology review](https://www.sciencedirect.com/science/article/pii/S095741742400424X)

**Opportunity:** compare random, periodic, uncertainty-based, and cost-aware
inspection policies under drift. The core model is extremely explainable; the
ambition comes from the online decision system and operational evaluation.

## Additive manufacturing

- [NIST AM Bench](https://www.nist.gov/ambench) and its [data/challenge portal](https://www.nist.gov/ambench/am-bench-data-and-challenge-problems-0) connect feedstock, process monitoring, thermal behavior, microstructure, residual strain, geometry, and mechanical behavior.
- [NIST AM Metrology Testbed dataset](https://www.nist.gov/publications/process-monitoring-dataset-additive-manufacturing-metrology-testbed-ammt-three) provides traceable process-monitoring data.
- [NIST AM data portal](https://pages.nist.gov/REPO/sections/AM_dataset/datasets.html) indexes additional process, thermography, and qualification datasets.
- [NIST thermography data](https://www.nist.gov/publications/thermography-single-line-scans-performed-commercial-powder-bed-fusion-machine-additive) support melt-pool/thermal modeling.
- [Open dual-scan thermography defect data](https://zenodo.org/records/15727369) provide another accessible experiment route.
- [Bayesian optimization in additive manufacturing](https://pmc.ncbi.nlm.nih.gov/articles/PMC11743787/) establishes an explainable low-trial optimization pattern.

**Opportunity:** a “born-qualified” build twin that predicts quality with
uncertainty and chooses the next parameter experiment. The data are excellent,
but cross-dataset synchronization and physical interpretation make this a higher
execution-risk flagship than welding or forming.

## Inspection and quality under real-world shift

- [MVTec LOCO AD](https://www.mvtec.com/research-teaching/datasets/mvtec-loco-ad) has 3,644 industrial images and distinguishes structural from logical anomalies.
- [MVTec AD 2](https://www.mvtec.com/research-teaching/datasets/mvtec-ad-2) has more than 8,000 high-resolution images across eight difficult scenarios, deliberately includes lighting shifts, and reserves part of the test ground truth for its evaluation server.
- [Robust-AD](https://openaccess.thecvf.com/content/CVPR2025W/VAND/papers/Pemula_Robust_AD_A_Real_World_Benchmark_Dataset_For_Robustness_in_CVPRW_2025_paper.pdf) directly evaluates robustness challenges in industrial anomaly detection.
- [Conformal defect segmentation](https://arxiv.org/abs/2504.17721) supplies a recent path for pixel-level uncertainty.

**Opportunity:** a calibrated quality gate that chooses accept/reject/reinspect
under shift and inspection cost. **Caution:** visual anomaly detection is one of
the most crowded manufacturing-AI areas; uncertainty and decision economics are
required for differentiation.

## Supply networks and factory logistics

- [Learning Production Functions for Supply Chains with GNNs](https://ojs.aaai.org/index.php/AAAI/article/view/35004) introduces SupplySim and shows graph-based forecasting on synthetic and real supply networks.
- [AnonNet](https://supplychaindatahub.org/datasets/anonnet/) contains a real anonymized manufacturing supply network with more than 7,000 nodes and 40,000 edges.
- [SupplyGraph](https://arxiv.org/abs/2401.15299) supplies a temporal FMCG graph benchmark.
- [Automotive production-network dataset](https://data.mendeley.com/datasets/pr3sdy5vp3/1) includes 28,049 products, a BOM/network, production nodes and arcs, and demand information.
- [Real footwear-manufacturing warehouse dataset](https://www.sciencedirect.com/science/article/pii/S2352340925005645) includes WMS-derived orders, product locations, operator/temporal data, CAD layouts, and scripts for routing, batching, storage, workload, and AGV studies.

**Opportunity:** predictive graph + disruption simulator + mitigation optimizer,
or a dynamic factory-logistics twin. **Class-overlap warning:** an LLM-agent
supply-shock proposal already exists, so our system would need to be quantitatively
different: graph forecasting, explicit constraints, and optimization/RL rather
than dialogue among agents.

## Maintenance and process monitoring

- [NASA C-MAPSS](https://catalog.data.gov/dataset/cmapss-jet-engine-simulated-data) is the standard turbofan degradation/RUL benchmark.
- [PHM Society data repository](https://data.phmsociety.org/) includes tool-wear, machine-health, and challenge datasets.
- [UCI AI4I 2020](https://archive-beta.ics.uci.edu/dataset/601/ai4i%2B2020%2Bpredictive%2Bmaintenance%2Bdataset/files) is a synthetic tabular predictive-maintenance dataset.
- [UCI SECOM](https://doi.org/10.24432/C54305) contains 1,567 semiconductor examples, 591 process features, and pass/fail labels.
- [UCI hydraulic-system condition monitoring](https://archive.ics.uci.edu/dataset/447/condition%2Bmonitoring%2Bof%2Bhydraulic%2Bsystems) contains 2,205 cycles and high-dimensional raw multi-sensor measurements for several component conditions.
- [Tennessee Eastman reference data](https://data.dtu.dk/articles/dataset/Tennessee_Eastman_Reference_Data_for_Fault-Detection_and_Decision_Support_Systems/13385936) provide a 132.96 GB process benchmark with 28 faults, six modes, and 500 simulations per condition.

**Interpretation:** datasets are abundant, but generic fault classification and
RUL are crowded and overlap the class audio-maintenance proposal. A competitive
project would need prescriptive scheduling, calibrated risk, a recovery policy,
or cross-machine/domain generalization.

## Human factors, digital thread, and circular manufacturing

- [Working Gesture Dataset](https://pmc.ncbi.nlm.nih.gov/articles/PMC8619710/) provides motion-capture data for assembly-line handling, hammering, and screwing with ergonomic indicators.
- [Overhead Car Assembly IMU dataset](https://fordatis.fraunhofer.de/handle/fordatis/195?locale=en) contains 360 minutes of synchronized video and four-IMU data across 282 industrial-task repetitions.
- [NIST digital-thread roadmap](https://www.nist.gov/publications/roadmap-strengthen-us-manufacturing-supply-chain-digital-thread-technology) and [Extended Digital Thread program](https://www.nist.gov/programs-projects/extended-digital-thread) identify interoperability, causal analytics, and engineering-change impact as major manufacturing needs.
- [NIST Data-Driven Design for Product Recovery](https://www.nist.gov/programs-projects/data-driven-design-product-recovery) connects design information to end-of-life recovery decisions.
- [REASSEMBLE](https://tuwien-asl.github.io/REASSEMBLE_page/) provides multimodal robotic assembly/disassembly data.
- [Fraunhofer robotic vacuum disassembly data](https://publica.fraunhofer.de/entities/publication/410a71b2-1bfa-47e5-ba9d-45914bd47590) cover 37 experiments, 21 manufacturers, and 1,113 images.

**Opportunities:** engineering-change impact over a BOM/CAD/process/supplier graph,
or condition/value-aware disassembly sequence planning. Both are distinctive and
mechanically grounded; both have weaker end-to-end labels than welding, forming,
or inspection and therefore need a simulator/rule-generated ground truth.

## Sustainability and materials

- [NIST data-driven sustainability assessment](https://www.nist.gov/publications/data-driven-approach-improving-sustainability-assessment-advanced-manufacturing) and [NIST circular-systems research](https://www.nist.gov/circular-economy/research-areas/system-and-decision-science) support life-cycle and recovery decision framing.
- [NREL industrial process heat data](https://doi.org/10.7799/1461488) provide a public basis for energy and emissions work.
- [Causal ML for manufacturing rework decisions](https://arxiv.org/abs/2406.11308) reports a real semiconductor application where intervention modeling, rather than plain yield prediction, improved the rework decision.
- [Matbench](https://docs.materialsproject.org/collaborations/matbench) defines 13 materials-property prediction tasks ranging from hundreds to more than 100,000 samples.
- [NIST Autonomous Laboratories](https://www.nist.gov/autonomous-laboratories) and [Autonomous Formulation Lab](https://www.nist.gov/programs-projects/autonomous-formulation-lab) establish the surrogate + uncertainty + experiment-selection pattern.

**Opportunity:** energy-aware production decisions or autonomous process/material
parameter search. Materials-property prediction alone drifts away from
manufacturing unless it is tied to a process, part, and experiment decision.

## Evidence-backed research conclusion

The most defensible underserved pattern is:

> **multimodal or physics-grounded state estimation + calibrated uncertainty + a
> constrained manufacturing decision + an operational evaluation.**

That pattern keeps the ML teachable while allowing the final system to be
technically ambitious. LLMs are useful as a grounded interface and explanation
layer, not as the sole manufacturing intelligence.
