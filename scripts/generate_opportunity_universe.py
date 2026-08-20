#!/usr/bin/env python3
"""Generate the systematic breadth map used by the project-selection research.

The 1,000 rows are a morphological search space, not 1,000 claims that every
combination deserves implementation.  Fifty manufacturing contexts are crossed
with twenty AI intervention patterns.  Two deliberately selected interventions
per context form a 100-project longlist for subsequent evidence-based ranking.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"


CONTEXTS = [
    # domain, context, signals, decision, metric, two interventions for the longlist
    ("Product engineering", "Conceptual mechanical design", "requirements, prior designs, simulation outputs", "choose a feasible design concept", "constraint satisfaction and simulated performance", ("inverse_design", "llm_copilot")),
    ("Product engineering", "Topology and geometry optimization", "loads, boundary conditions, meshes, CAD geometry", "choose geometry that meets mass and stiffness targets", "mass, compliance, manufacturability", ("surrogate", "inverse_design")),
    ("Product engineering", "Material and process selection", "material properties, cost, embodied carbon, process limits", "select a material-process pair", "performance, cost, and carbon", ("causal", "llm_copilot")),
    ("Product engineering", "CAD manufacturing-feature recognition", "STEP/B-Rep faces, edges, adjacency, geometry", "identify machinable features and their parameters", "feature-level F1 and topology validity", ("gnn", "multimodal")),
    ("Product engineering", "Engineering drawing interpretation", "2D drawings, symbols, notes, title blocks", "extract dimensions, tolerances, and manufacturing requirements", "entity F1 and drawing-level exactness", ("multimodal", "llm_copilot")),
    ("Product engineering", "Tolerance and GD&T design", "PMI, tolerance stacks, process capability", "allocate tolerances without unnecessary cost", "yield, stack-up risk, and cost", ("optimization", "counterfactual")),
    ("Product engineering", "Design for manufacturability review", "CAD geometry, process rules, tool access", "redesign or accept a part", "violations found and avoidable cost", ("gnn", "counterfactual")),
    ("Process engineering", "Computer-aided process planning", "part features, materials, machines, tools", "select and sequence manufacturing operations", "plan feasibility, time, and cost", ("sequence", "llm_copilot")),
    ("Process engineering", "Machine and cutting-tool selection", "features, materials, machine envelopes, tool catalogs", "assign machines, fixtures, and tools", "feasibility and predicted cycle time", ("optimization", "gnn")),
    ("Commercial manufacturing", "CNC quotation and lead-time estimation", "CAD, tolerances, material, batch size, prior jobs", "price and promise a job", "cost error and on-time quote accuracy", ("virtual_metrology", "counterfactual")),
    ("Supply network", "Supplier discovery and qualification", "capabilities, certifications, parts, quality history", "select suppliers for a part", "qualified-supplier recall and sourcing cost", ("gnn", "llm_copilot")),
    ("Supply network", "Supplier quality and disruption risk", "deliveries, defects, financial and event signals", "audit, dual-source, or accept risk", "calibrated risk and avoided disruption cost", ("forecast", "uncertainty")),
    ("Supply network", "Procurement and component demand", "orders, BOMs, lead times, consumption history", "place purchase orders", "service level and working capital", ("forecast", "counterfactual")),
    ("Supply network", "Multi-tier supply network resilience", "supplier-product graph, flows, capacities, disruptions", "choose mitigation actions after a shock", "time-to-recovery and fulfilled demand", ("gnn", "rl_policy")),
    ("Supply network", "Inventory and spare-parts control", "intermittent demand, criticality, lead time, installed base", "set reorder and safety-stock policies", "availability and inventory cost", ("forecast", "rl_policy")),
    ("Supply network", "Inbound and outbound transportation", "orders, routes, capacity, traffic, emissions", "consolidate and route shipments", "cost, lateness, and emissions", ("routing", "rl_policy")),
    ("Factory logistics", "Warehouse order picking", "orders, CAD layout, locations, worker travel", "batch orders and select pick routes", "distance, throughput, and workload balance", ("routing", "sequence")),
    ("Factory logistics", "Intralogistics and material replenishment", "line demand, AGV state, buffers, plant layout", "dispatch vehicles and replenish stations", "starvation time and travel", ("rl_policy", "forecast")),
    ("Production operations", "Aggregate production planning", "orders, capacities, labor, maintenance, inventory", "set production quantities and overtime", "cost, backlog, and utilization", ("forecast", "optimization")),
    ("Production operations", "Job-shop scheduling", "jobs, routes, machines, setup times", "dispatch and resequence jobs", "makespan, tardiness, and stability", ("rl_policy", "gnn")),
    ("Machining", "CNC milling process control", "forces, vibration, spindle power, toolpath, NC code", "adjust feeds and speeds or stop", "cycle time, chatter, and surface quality", ("control", "surrogate")),
    ("Machining", "Turning process quality", "force, vibration, acoustic emission, parameters", "adjust cutting parameters", "roughness, dimensional error, and tool life", ("virtual_metrology", "parameter_recommendation")),
    ("Machining", "Drilling and hole quality", "thrust, torque, vibration, tool geometry", "change parameters or replace a drill", "burr, diameter, and delamination", ("diagnosis", "parameter_recommendation")),
    ("Machining", "Cutting-tool wear management", "force, vibration, acoustic emission, images", "continue, derate, or replace a tool", "remaining cuts and avoided scrap", ("rul", "uncertainty")),
    ("Machining", "Grinding burn and surface integrity", "acoustic emission, power, temperature, wheel state", "dress the wheel or change parameters", "burn detection and surface quality", ("anomaly", "control")),
    ("Joining", "Robotic arc welding", "video, audio, current, voltage, gas, robot speed", "warn early and correct welding parameters", "defect F1, detection latency, and saved welds", ("multimodal", "parameter_recommendation")),
    ("Primary processes", "Casting quality and yield", "thermal histories, chemistry, mold and X-ray data", "change gating, cooling, or disposition a casting", "porosity, shrinkage, and yield", ("surrogate", "causal")),
    ("Primary processes", "Hot and radial forging", "force, displacement, temperature, vibration, CMM results", "choose temperature and stroke settings", "dimensional quality and material properties", ("surrogate", "parameter_recommendation")),
    ("Primary processes", "Sheet-metal forming", "FE simulation, force curves, material batches, scans", "change blank holder force, tooling, or material setup", "springback, thinning, and split risk", ("surrogate", "uncertainty")),
    ("Polymer processing", "Injection molding", "pressure, temperature, cycle timing, images, part labels", "change settings or reject a part", "quality, cycle time, and scrap", ("virtual_metrology", "counterfactual")),
    ("Additive manufacturing", "Metal powder-bed fusion", "melt-pool video, thermography, scan path, layer data", "alter scan parameters or stop a build", "defect, density, and build success", ("multimodal", "control")),
    ("Additive manufacturing", "Polymer extrusion printing", "video, temperatures, motion and geometry", "correct extrusion or pause a print", "geometric error and print success", ("anomaly", "control")),
    ("Composites", "Automated fiber placement", "laser scans, paths, tow images, compaction data", "repair, rework, or change placement parameters", "gap, overlap, wrinkle, and scrap", ("multimodal", "virtual_metrology")),
    ("Thermal processing", "Heat treatment", "furnace curves, atmosphere, alloy, hardness and microstructure", "choose recipe and release a batch", "hardness, distortion, energy, and cycle time", ("surrogate", "optimization")),
    ("Semiconductor manufacturing", "Chemical mechanical planarization", "equipment sensors and sparse metrology", "select wafers to measure and correct the process", "metrology reduction under bounded error", ("virtual_metrology", "active_sampling")),
    ("Battery manufacturing", "Electrode coating and cell formation", "thickness, images, impedance, process histories", "change process settings or grade cells", "yield, capacity, and early-life quality", ("virtual_metrology", "multimodal")),
    ("Electronics manufacturing", "PCB and electronics assembly", "AOI images, X-ray, paste data, placement logs", "reinspect, rework, or tune printing/placement", "escape rate, false reject, and rework", ("anomaly", "uncertainty")),
    ("Assembly", "Manual assembly verification", "video, tools, torque, work instructions, part state", "detect a skipped or incorrect operation", "step accuracy and error-detection latency", ("multimodal", "sequence")),
    ("Robotics", "Robot manipulation and bin picking", "RGB-D, point clouds, CAD, force-torque", "select grasp and motion", "pick success and cycle time", ("multimodal", "rl_policy")),
    ("Robotics", "Human-robot collaborative assembly", "human pose, task state, robot state, safety zones", "allocate tasks and adapt robot motion", "throughput, ergonomics, and safety", ("forecast", "rl_policy")),
    ("Quality", "Industrial visual inspection", "high-resolution images under domain and lighting shifts", "accept, reject, or reinspect a part", "AU-PRO, false escapes, and review load", ("anomaly", "uncertainty")),
    ("Quality", "Dimensional inspection and metrology", "CMM, scans, process sensors, tolerances", "choose what and how often to measure", "measurement cost and escaped deviation", ("active_sampling", "virtual_metrology")),
    ("Asset management", "Predictive maintenance", "vibration, sound, temperature, work orders", "schedule maintenance and parts", "downtime, false alarms, and maintenance cost", ("rul", "diagnosis")),
    ("Factory sustainability", "Utilities and production energy", "machine states, tariffs, schedules, energy meters", "shift loads and choose energy-efficient settings", "energy, peak demand, carbon, and throughput", ("forecast", "optimization")),
    ("Human factors", "Worker ergonomics", "video or IMUs, anthropometry, task repetition", "redesign a task or trigger coaching", "RULA/EAWS risk and productivity", ("multimodal", "counterfactual")),
    ("Human factors", "Industrial safety and PPE", "video, proximity, machine state, incident history", "warn, slow, or stop equipment", "near-miss recall and nuisance alarms", ("forecast", "uncertainty")),
    ("Digital thread", "Engineering-change impact analysis", "BOM, CAD, process plans, suppliers, requirements", "approve a change and identify affected artifacts", "impact recall and avoided late changes", ("gnn", "llm_copilot")),
    ("Digital thread", "Traceability and cross-stage root cause", "genealogy, process settings, inspections, rework", "contain lots and correct the causal stage", "root-cause accuracy and containment cost", ("causal", "gnn")),
    ("Circular manufacturing", "Product disassembly and remanufacturing", "CAD assembly graph, condition, tool access, part value", "select a safe, value-maximizing disassembly sequence", "recovered value, time, and collisions", ("rl_policy", "gnn")),
    ("Circular manufacturing", "Scrap, waste, and by-product recovery", "material flows, quality, demand, recycling options", "route material to reuse, remanufacture, or recycle", "virgin material, cost, and recovered value", ("routing", "optimization")),
]


INTERVENTIONS = [
    ("forecast", "Forecasting", "predict the future state early enough to act", "gradient boosting, temporal CNN, or transformer"),
    ("classification", "Defect or state classification", "label the part, operation, or condition", "random forest, CNN, or pretrained encoder"),
    ("anomaly", "Novelty and anomaly detection", "identify deviations without exhaustive defect labels", "autoencoder, PatchCore, one-class SVM, or isolation forest"),
    ("diagnosis", "Fault and root-cause diagnosis", "rank plausible causes and the next diagnostic check", "Bayesian network, tree ensemble, or classifier"),
    ("rul", "Remaining useful life", "estimate time or cycles until intervention", "survival model, gradient boosting, or sequence model"),
    ("virtual_metrology", "Virtual metrology", "estimate an expensive or delayed quality measurement", "Gaussian process, gradient boosting, or neural regressor"),
    ("surrogate", "Fast simulation surrogate", "replace slow physics simulation in a decision loop", "Gaussian process, neural operator, or compact neural network"),
    ("parameter_recommendation", "Process-parameter recommendation", "recommend settings subject to process constraints", "surrogate plus constrained optimizer"),
    ("control", "Closed-loop process control", "change the process while the operation is running", "model-predictive control with a learned model"),
    ("sequence", "Operation and sequence planning", "construct a feasible ordered plan", "constraint solver, pointer network, or graph policy"),
    ("routing", "Routing and resource allocation", "assign jobs, material, labor, or vehicles", "mixed-integer optimization plus learned estimates"),
    ("active_sampling", "Active inspection and sampling", "choose the next item or measurement worth paying for", "uncertainty sampling, contextual bandit, or active learning"),
    ("causal", "Causal root-cause and intervention analysis", "separate correlation from controllable causes", "causal graph, uplift model, or double ML"),
    ("uncertainty", "Calibrated uncertainty and abstention", "know when the model should defer, reinspect, or stop", "conformal prediction, ensembles, or calibrated probabilities"),
    ("counterfactual", "Counterfactual decision support", "show the smallest feasible change that improves the outcome", "interpretable surrogate plus constrained search"),
    ("optimization", "Bayesian or constrained optimization", "find good settings with few costly trials", "Gaussian process or tree surrogate plus acquisition function"),
    ("rl_policy", "Reinforcement-learning policy", "learn a sequential policy inside a simulator", "PPO, DQN, or actor-critic with constraints"),
    ("gnn", "Graph dependency learning", "reason over topology, assemblies, BOMs, or operation networks", "message-passing graph neural network"),
    ("llm_copilot", "Grounded LLM or agent copilot", "retrieve evidence, use tools, and explain a recommended action", "RAG/SFT LLM with deterministic tools and citations"),
    ("multimodal", "Multimodal sensor fusion", "combine complementary geometry, vision, audio, and time-series evidence", "late-fusion encoders or cross-attention"),
    ("inverse_design", "Inverse design and constrained generation", "generate candidates that meet target properties", "conditional generative model plus physics/rule validation"),
]


# Keep the matrix exactly 20 interventions. Inverse design replaces generic
# classification in the breadth matrix because classification is already a
# component of several other patterns; classification remains available to the
# catalog through the anomaly/diagnosis patterns.
MATRIX_KEYS = [
    "forecast", "anomaly", "diagnosis", "rul", "virtual_metrology", "surrogate",
    "parameter_recommendation", "control", "sequence", "routing", "active_sampling",
    "causal", "uncertainty", "counterfactual", "optimization", "rl_policy", "gnn",
    "llm_copilot", "multimodal", "inverse_design",
]


INTERVENTION_BY_KEY = {row[0]: row for row in INTERVENTIONS}


def status_for(key: str, selected: tuple[str, str]) -> str:
    if key in selected:
        return "priority combination"
    if key in {"llm_copilot", "rl_policy", "control", "inverse_design"}:
        return "needs a strong decision case"
    return "secondary combination"


def title(context: str, intervention_name: str) -> str:
    return f"{intervention_name} for {context.lower()}"


def write_universe() -> None:
    path = RESEARCH / "opportunity-universe-1000.csv"
    fields = [
        "opportunity_id", "domain", "manufacturing_context", "intervention_family",
        "concept", "available_signals", "manufacturing_decision", "model_family",
        "evaluation_target", "screening_status",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        opportunity_id = 0
        for domain, context, signals, decision, metric, selected in CONTEXTS:
            for key in MATRIX_KEYS:
                opportunity_id += 1
                _, name, purpose, model = INTERVENTION_BY_KEY[key]
                writer.writerow({
                    "opportunity_id": f"OPP-{opportunity_id:04d}",
                    "domain": domain,
                    "manufacturing_context": context,
                    "intervention_family": name,
                    "concept": f"Use {name.lower()} to {purpose} in {context.lower()}.",
                    "available_signals": signals,
                    "manufacturing_decision": decision,
                    "model_family": model,
                    "evaluation_target": metric,
                    "screening_status": status_for(key, selected),
                })
    assert opportunity_id == 1000


def write_longlist() -> None:
    path = RESEARCH / "project-longlist-100.csv"
    fields = [
        "project_id", "domain", "project_concept", "problem_and_action", "data_modalities",
        "explainable_model_core", "evaluation_target", "selection_note",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        project_id = 0
        for domain, context, signals, decision, metric, selected in CONTEXTS:
            for key in selected:
                project_id += 1
                _, name, purpose, model = INTERVENTION_BY_KEY[key]
                writer.writerow({
                    "project_id": f"P-{project_id:03d}",
                    "domain": domain,
                    "project_concept": title(context, name),
                    "problem_and_action": f"Use AI to {purpose}; the system must help operators {decision}.",
                    "data_modalities": signals,
                    "explainable_model_core": model,
                    "evaluation_target": metric,
                    "selection_note": "Selected because the AI output maps to a concrete manufacturing decision.",
                })
    assert project_id == 100


def main() -> None:
    RESEARCH.mkdir(parents=True, exist_ok=True)
    write_universe()
    write_longlist()
    print("Generated 1,000-opportunity universe and 100-project longlist.")


if __name__ == "__main__":
    main()
