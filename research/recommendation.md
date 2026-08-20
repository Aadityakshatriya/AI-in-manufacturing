# Recommendation: build WeldSense, with FormTwin as the no-drama fallback

> **Expansion note (21 August 2026):** the second detailed research pass found two
> unusually strong new candidates. **MoldRx** now has the cleanest public
> end-to-end data path, while **PackRecover** has the strongest combination of
> originality, mechanical engineering, GNN/RL explainability, and circular
> manufacturing. See `additional-projects-detailed.md`. WeldSense remains the
> preferred multimodal process-monitoring project, but the final selection should
> now explicitly compare these three.

## The decision

Start with a one-week data-access and signal-quality spike for **WeldSense**, a
multimodal robotic-welding early-warning and process-rescue system. If the Intel
research-data request is not approved quickly or its labels cannot support honest
evaluation, switch immediately to **FormTwin**, the simulation-to-real
sheet-forming quality twin.

This is not “easy slop.” WeldSense combines four modalities, temporal early
prediction, calibration, domain-shift tests, explainability, constrained setting
search, and a polished live demo. Yet every component can be taught using familiar
building blocks: one encoder per sensor, fusion, classifier, uncertainty wrapper,
and optimizer. No new ML theory is required.

## Exact research hypothesis

> Time-aligned multimodal signals can identify high-risk welds substantially before
> completion, with calibrated confidence, and a response surrogate can turn that
> warning into feasible offline process-setting candidates.

The defensible contribution is the **early, calibrated, decision-oriented system**,
not the claim that CNNs, attention, welding defect detection, or parameter
optimization are individually new.

## Deliverable definition

By the end, the repository should contain:

1. Reproducible dataset manifests, preprocessing, synchronization, and leakage-safe
   grouped splits.
2. Simple baselines: process-settings MLP, electrical 1D CNN, audio CNN, and video
   encoder.
3. Multimodal late-fusion model and ablations.
4. Early-warning experiments at multiple fractions of weld completion.
5. Calibration/selective-prediction layer and domain-shift analysis.
6. Constrained offline parameter-response and recommendation module.
7. Interactive application with synchronized video/audio/electrical traces,
   timeline risk, uncertainty, explanations, and what-if settings.
8. An evaluation report, model card, dataset/license note, architecture diagram,
   five-minute demo, and presentation-ready results.

## 12-week plan based on Codex doing the implementation

| Week | Technical outcome | What the student team must do |
|---:|---|---|
| 1 | Data-access decision, dataset card audit, sample loader, EDA, label and synchronization checks | Confirm research-license access and understand welding variables |
| 2 | Reproducible preprocessing, manifests, session-grouped splits, tabular baseline | Review leakage logic and defect definitions |
| 3 | Electrical time-series baseline and early-window experiment | Learn the 1D CNN/feature baseline |
| 4 | Audio spectrogram baseline | Learn spectrogram → CNN reasoning |
| 5 | Video/image baseline with transfer learning | Understand transfer learning and overfitting checks |
| 6 | Late-fusion model plus modality ablations | Explain why fusion helps or fails |
| 7 | Calibration, conformal/selective prediction, domain-shift tests | Learn confidence versus accuracy |
| 8 | Response surrogate and constrained setting search | Validate that recommendations respect welding ranges |
| 9 | Interactive timeline/what-if application | Review the operator workflow |
| 10 | Robustness, error analysis, stress tests, reproducibility | Inspect failures and choose honest claims |
| 11 | Report, diagrams, model card, demo script | Own the manufacturing story and results |
| 12 | Buffer, polish, reruns, presentation rehearsal | Present and defend the system |

Because Codex handles the implementation, this schedule reserves time for proper
experiments and failure analysis rather than spending eight weeks wiring a basic
notebook.

## First-week kill criteria

Switch to FormTwin if any of the following holds after the spike:

- Intel access is unavailable and the open welding datasets cannot support an
  honest early-warning target.
- Session/parameter metadata are insufficient for a leakage-safe split.
- Intended-defect labels are so noisy that a process-settings-only model explains
  nearly all apparent performance.
- The modalities cannot be synchronized well enough for windowed fusion.
- No reasonable fallback label such as quality score, penetration, profile, or
  electrical instability is available.

These criteria prevent attachment to a flashy but invalid result.

## FormTwin fallback deliverable

FormTwin uses the 2026 sim-to-real sheet-forming dataset to compare:

1. a physics/simulation-only surrogate;
2. zero-shot performance on the real process;
3. residual correction or fine-tuning with increasing amounts of real data;
4. uncertainty under material/process shift; and
5. constrained parameter optimization.

The app becomes a forming-process twin with force/trajectory inputs, predicted
springback/thinning/quality, reality-gap visualization, and parameter what-if
analysis. This fallback is still a serious final project, not a reduced demo.

## Why not choose CADPlan first

CADPlan may create the most impressive product, and it is the best option if the
team strongly prefers CAD/CAM. It ranks fourth because feature-recognition ground
truth is good while full operation-plan, tooling, setup, cycle-time, and quotation
ground truth is fragmented. In twelve weeks, it is easier to build something that
*looks* intelligent than to prove that the plan is correct. Welding and forming
have cleaner scientific claims.

## Final position

The selection should be ambitious in **system behavior**, not obscure in ML:

> sense several aspects of a real process, predict early, know when uncertain,
> recommend a constrained action, and prove the value under realistic splits.

That is both explainable to first-years and substantially stronger than the three
ideas currently visible in the class sheet.
