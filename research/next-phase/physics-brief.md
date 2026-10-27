# Physics brief: why a milling cutter breaks, and what the sensors can see

Research brief for the ToolLife project (AI in Manufacturing, IITM). Written 27 October 2026.
Purpose: the factual base for a plain-language, illustrated explainer for first-year students. Every number is either quoted from a source (marked [P1], [M2], [B4] and so on, listed at the end) or computed in this document (formula shown). Where a fact comes from our own look at the raw data, it is marked **[our data]** and the method is in Appendix A.

---

## 0. The facts at a glance

| Question | Answer | Source |
|---|---|---|
| Cutters | Type 1: Van Hoorn VHVTR 4 100 070 10 03 050 ("HPM Cutter Standard 10x70 R=0,50 Z=4 TiAlN Gold"). Type 2: PARA Tooling RS4 10,0x70 ("Ruwfrees 50° met afkanting 10,0x70 Z=4 TiAlN", a roughing mill with corner chamfer). PARA Tooling is Van Hoorn's budget line. | [P1], [M1], [M2], [M5] |
| Flutes | **4 on both types.** Manufacturer pages say z = 4. The companion paper on the same dataset says z = 4. The vibration spectrum peaks at 213 Hz = 4 × 53.3 Hz. | [M1], [M2], [P2], [our data] |
| Coating, helix | Type 1: TiAlN Gold coating, variable helix (35°/38° per a distributor listing, not on the maker's page), 0.5 mm corner radius. Type 2: TiAlN coating, 50° helix, 0.2 mm corner chamfer. Both: Ø10 mm, shank 10 mm, overall length 70 mm, cutting length 22 mm, centre-cutting, right-hand. | [M1], [M2] |
| Cutting speed | v = π·D·n = π × 10 mm × 3200 rpm = **100.5 m/min** | computed |
| Feed per tooth | fz = 640 / (4 × 3200) = **0.050 mm per tooth** (0.20 mm per revolution) | computed |
| Spindle and tooth frequencies | Spindle (once per revolution) **53.33 Hz**. Tooth passing **213.33 Hz**, with harmonics at 426.7, 640, 853.3 … Hz. | computed, confirmed [our data] |
| Material removal rate | 14.4 / 25.6 / 28.8 / 51.2 cm³/min for (ADOC, RDOC) = (5, 4.5) / (5, 8) / (10, 4.5) / (10, 8) mm | computed |
| What current channels really are | RMS values from a power-measurement terminal, refreshed **every 200 ms** (5 times per second), then written 500 times per second. They show load level, not individual tooth hits. | [P1], [our data] |
| One "cycle" | One full clockwise lap around the block at one depth layer: about 350–370 mm of tool path and about 31 s of cutting. Each data file is typically 60–85 s because it includes spindle start, approach and stop. | [P1], [P2], [our data] |
| Failure | Complete breakage of the cutter or breakage of one tooth. Decided by looking at the tool. No wear (VB) was measured. | [P1] |
| Licence | Article is **CC BY 4.0**, so its figures can be reused with attribution. | [P1] |
| Best early-warning physics (our data, 7 tools) | Feed-axis (X) drive current rises 1.4–2.7× over life. Net spindle current (cutting minus idle) rises 1.2–1.5×. The once-per-revolution vibration line grows 2–13× near the end when a tooth chips. All three stay flat for the first 30–50 % of life, then climb. | [our data] |

---

## Part A. What the dataset paper actually says (Piecuch & Żabiński 2025)

Primary source: Piecuch, G. & Żabiński, T. "A new open dataset from a milling process – data for classification and estimation of tool life." *Scientific Data* 12, 650 (2025). doi:10.1038/s41597-025-04923-y. Full text also at PMC12006439 [P1]. Data: Figshare doi:10.6084/m9.figshare.28589216 and Kaggle (grzegorzpiecuch/cnc-milling).

A companion paper from the same group uses the same data and adds details [P2]: Paszkiewicz, A. et al. "Estimation of Tool Life in the Milling Process—Testing Regression Models." *Sensors* 23, 9346 (2023). doi:10.3390/s23239346 (CC BY 4.0).

### A1. The cutters

The paper names the two tools only by their catalogue codes: "Van Hoorn VHVTR41000701003050 (MillingToolType – 1)" and "PARA Tooling RS4 10,0 × 70 (MillingToolType – 2)" [P1]. It gives no flute count, coating or helix. We looked both up on the manufacturer's webshop.

| | Type 1 (tools 2–11) | Type 2 (tools 101, 102, 103, 105) |
|---|---|---|
| Maker, product | Van Hoorn Carbide (Weert, NL), series VHVTR4, article VHVTR41000701003050 [M1] | PARA Tooling (Van Hoorn's lower-cost line, "standard carbides … standard coatings") [M5], series RS4, article RS410,0x70 [M2] |
| Maker's description | "HVM HPM Cutter Standard 10x70 R=0,50 Z=4 TiAlN Gold" | "Ruwfrees 50° met afkanting 10,0x70 Z=4 TiAlN" (Dutch: roughing end mill, 50°, with chamfer) |
| Category on webshop | "Stainless steels & Exotic materials" (also rated for steels 42–50 HRC) | PARA Tooling RS4 |
| Number of flutes z | **4** | **4** |
| Coating | TiAlN Gold (gold/copper colour in Figs 14–16) | TiAlN (dark grey in Figs 14–16) |
| Helix angle | "Variabel" (variable). A distributor listing for the 12 mm sibling gives 35°/38°; that page was bot-blocked, so treat 35°/38° as likely, not confirmed. | 50° |
| Corner | 0.5 mm corner radius | 0.2 mm chamfer |
| Diameter / shank / overall length / cutting length | 10.0 / 10 / 70 / 22 mm | 10.0 / 10 / 70 / 22 mm |
| Centre cutting | Yes | Yes |
| Tolerances | Shank h5 (made for shrink-fit holders), diameter e8 | e8 |

How the code decodes (pattern visible across the whole VHVTR4 range on the webshop): VHVTR | 4 flutes | 100 = Ø10.0 mm | 070 = 70 mm long | 10 = 10 mm shank | 03 | 050 = 0.50 mm corner radius. Every one of the 156 VHVTR4 variants is listed with z = 4.

Three independent confirmations of 4 flutes:
1. Manufacturer pages: z = 4 for both [M1], [M2].
2. The companion paper: "z = 4 (number of flutes)" for both tools [P2].
3. Physics **[our data]**: during cutting, the X-axis accelerometer (+Z) puts 70 % of its vibration power in a narrow line at 212.9 Hz, which is 4 × 53.3 Hz (file P002_F01_C3). With 3 flutes the line would sit at 160 Hz; with 2 flutes, at 107 Hz. Fig. 15a of the paper also shows four teeth in end view.

Manufacturer's recommended conditions, used to explain "optimal" and "non-optimal" [M3], [M4]:
- Van Hoorn VHVTR4, shoulder milling at 1×D depth: axial depth (ap) up to 1.0×D, **radial depth (ae) up to 0.45×D (4.5 mm for Ø10)**, fz 0.040–0.070 mm for Ø10. Cutting speed 70–160 m/min for steel group P1.3 (< 1400 N/mm², < 400 HB) and 80–140 m/min for hardened steel 42–50 HRC. This is exactly why the paper calls RDOC 4.5 mm "optimal" ("not exceeding 45 % of the tool diameter") and RDOC 8 mm (80 % of D) non-optimal [P1].
- PARA Tooling roughing (contouring): ap up to 1.25×D, ae up to 0.40×D, fz = 0.040 mm for Ø10, with the same speed table. So for the Type 2 cutter even the "optimal" 4.5 mm is slightly above the 4.0 mm guideline, and fz = 0.05 mm is 25 % above the roughing value. (This PDF covers the whole PARA range, not RS4 alone.)

Our settings sit inside Van Hoorn's ranges: 100.5 m/min and fz 0.050 mm.

### A2. Machine, holder, workpiece

- Machine: "3-axis Haas VF-1 milling machine" (Fig. 1) [P1].
- Holder: "the tool was mounted in thermal holders ensuring repeatability of assembly" [P1]. These are shrink-fit holders: the holder bore is heated, the shank is slid in, and the bore grips it as it cools. Metadata field ToolHolderLength: 80 mm or 160 mm. The paper does not say how far the cutter sticks out of the holder. Figs 14–15 suggest about 25–35 mm (the 22 mm fluted part plus a little shank).
- Workpiece: 42CrMo4 (a chromium-molybdenum alloy steel), blocks 80 × 80 × 150 mm, "heat hardened to 38 ± 2 HRC". The measured hardness ranged from 35.33 to 41.67 HRC. "20 mm depth excluded from cutting to allow for secure mounting in a vice" [P1]. That leaves 60 mm of cuttable height, which matches the layer counts below.
- Coolant: not stated. Coolant nozzles are visible near the spindle in Fig. 2.
- Acquisition: Beckhoff C6920 industrial PC, EL3632 modules (accelerometers), EL3413 modules (currents), EK1100 EtherCAT coupler [P1].

### A3. The 20 sensor channels: what each measures and where it sits

**Accelerometers (channels 1–8), Table 1 of [P1].** These are IEPE piezoelectric accelerometers, sampled at 25 kHz. The paper lists them as Dytran 3055D2, plus one 3056D2T; the companion paper says 3055A2. Each measures acceleration (vibration) along one direction only.

| Ch | Column name in files | Mounted on | Direction | Sensitivity (mV/g) |
|---|---|---|---|---|
| 1 | Accelerometer - Spindle +Y | spindle housing (head), near the nose | +Y | 100.32 |
| 2 | Accelerometer - Spindle -Z | spindle housing | −Z (vertical) | 101.29 (3056D2T) |
| 3 | Accelerometer - Spindle -X | spindle housing | −X | 99.56 |
| 4 | Accelerometer - X Driving axle +Z | X-axis drive: top of the ball-screw nut housing under the table | +Z | 98.83 |
| 5 | Accelerometer - X Driving axle -X | X-axis drive: side bracket of the same nut housing | −X | 100.99 |
| 6 | Accelerometer - Y Driving axle +Z | Y-axis drive: top of the ball-nut housing (saddle) | +Z | 101.71 |
| 7 | Accelerometer - Y Driving axle +Y | Y-axis drive: end face facing the ball screw | +Y | 99.49 |
| 8 | Accelerometer - Y Driving axle -X | Y-axis drive: side face | −X | 99.17 |

- **"Driving axle" means the feed drive of an axis.** The paper calls it "the drives of the worktable" and "drive axis X" [P1]. Fig. 3 shows the sensors on the housings of the ball-screw nuts that push the table (X) and the saddle (Y). There is no X-direction-Y sensor "due to the lack of space" [P1].
- Why the two groups differ physically: the workpiece is clamped to the table, so the cutting force travels workpiece → vice → table → X ball-nut and guides → saddle → Y ball-nut. The axis sensors therefore sit on the workpiece side of the force path. The spindle sensors sit on the tool side, but next to the spindle bearings and motor.
- Conversion to g: Acc = data × 5 V / (2¹⁵ × S), with S in V/g [P1].
- **[our data]** The spindle-housing sensors are dominated by non-cutting vibration. Spindle +Y measures about 3–7 m/s² RMS with the spindle running in air and 6–9 m/s² while cutting. 40–80 % of the spindle sensors' power lies above 3 kHz. The axis sensors are quiet in air (X +Z: about 0.2–0.3 m/s²) and show clean cutting lines while cutting (0.3–0.8 m/s²). In plain words, the table sensors "hear" the cutting teeth better than the head sensors do.

**Current channels (9–20).** These are 12 clip-on current transformers, WAGO 855-4001/0100-0001 (100 A primary to 1 A secondary, 0.2 VA, accuracy class 1) [P1], [M6]. They are read by Beckhoff EL3413 three-phase power-measurement terminals. The data are logged at 0.5 kHz [P1]. Conversion: current [A] = data × 0.00002 [P1].

| Ch | Column name | Measures |
|---|---|---|
| 9–11 | Current - Spindle L1 / L2 / L3 | the three phase currents of the spindle motor's power supply |
| 12–14 | Current - Driving axle X L1 / L2 / L3 | the three phases of the X-axis servo drive (moves the table left/right) |
| 15–17 | Current - Driving axle Y L1 / L2 / L3 | the three phases of the Y-axis servo drive (moves the saddle in/out) |
| 18–20 | Current - Driving axle Z L1 / L2 / L3 | the three phases of the Z-axis servo drive (holds the spindle head up and down) |

- **L1, L2, L3 are the three phase conductors of a three-phase AC supply.** Every motor here is three-phase, so there is one transformer per conductor. With a healthy, balanced motor the three phases carry almost the same RMS current. **[our data]** At spindle idle they read 2.576, 2.569 and 2.577 A. Averaging the three phases is therefore a good noise-reduction step, and phase imbalance would point to an electrical problem, not a tool problem.
- **Yes, there is a spindle current** (channels 9–11).
- The paper does not say whether the transformers sit on the motor cables (after the drive) or on the drive's supply (before it).
- **Important [our data]: the current values only change every 200 ms.** In every file we checked (spindle, X and Z channels), each value repeats for 100 consecutive 2 ms samples (100–102 for the axis channels). This fits the EL3413 being a power meter that reports RMS (average-strength) values, not raw waveforms. The paper's own Table 2 sample also shows identical repeated values. The current channels can therefore follow load changes slower than about 2.5 Hz (5 updates per second), and nothing faster.
- Typical levels **[our data]**: spindle idle (running in air) about 2.57 A, almost identical in every file. Spindle while cutting about 3.3–5.4 A. X/Y axis currents while cutting only about 0.07–0.36 A. Z about 0.01 A at rest, up to about 0.6 A when moving.
- Accuracy caution: these readings are 0.01–5 % of the transformers' 100 A rating. Class-1 transformers are normally only specified from 5 % of rated current upward (IEC 61869-2), so absolute amps are approximate, especially on the axes. Ratios and trends within one machine remain usable.

### A4. What one "cycle" is

From [P1] (Figs 5–9) and the metadata:
- **Sample (P)**: one steel block.
- **Layer (F)**: one slice of the block's height, with thickness equal to the axial depth (ADOC). The paper's text says ADOC 5 or 10 mm gives "6 or 12 [layers], respectively". That is inverted. The metadata show ADOC 5 mm → up to 12 layers (F01–F12) and ADOC 10 mm → up to 6 layers. This matches 60 mm of cuttable height.
- **Cycle (C)**: "a single path of the machining programme … run clockwise" around the contour of the block [P1]. One cycle is one closed lap that removes a ring of width RDOC. Seven rings fit in a layer at RDOC 4.5 mm, and four rings at RDOC 8 mm (Fig. 6). The tool never leaves the material between rings ("continuous milling, without the phase of retracting the tool") [P1].
- After the last ring of a layer, the leftover island in the middle was "planed" level, the tool was lowered, and recording restarted at cycle 1 [P1]. The planing is **not recorded**. It is not stated whether the same cutter did it. If it did, the tool did unrecorded work, so recorded cycles slightly undercount its true usage.
- Cycles per block: minimum 24 (6 layers × 4 rings) and maximum 84 (12 × 7) [P1].
- Path length and duration: the Sci Data paper gives neither. The companion paper's Table 1 [P2] gives per-tool totals. From these, a cycle is about 366 mm of path for RDOC 8 mm and about 352 mm for RDOC 4.5 mm, with about 30.6–31.1 s of operating time. Example: tool 8, 115 cycles, 3531 s, 40,696 mm, 915,660 mm³.
- **[our data]**: a typical file lasts 60–85 s and the spindle runs about 48–60 s of it. The loaded part (spindle current more than 0.3 A above idle) lasts about 24–36 s and gets shorter for inner rings (C2 about 36 s down to C7 about 24 s at RDOC 4.5). Cycle-1 files are longer (about 120–155 s file, about 52–58 s loaded). Fig. 11 shows that cycle 1 also clips the four leftover corners (marked 1A–4A and 1B–4B) before the full lap.
- Direction: clockwise around the outside with a normal right-hand, clockwise-spinning cutter. That means **climb (down) milling**: each tooth bites in at its thickest chip and leaves thin. This is our geometric inference; the paper does not name it.
- Cycles are not all recorded: 968 records exist, but some cycle numbers are missing (for example, tool 3 has 44 records over a 50-cycle life). Use the CycleToFailure column, not row counts.
- **File order is not time order.** Tool 5 cut block P016 first, then P010, then P008 (CycleToFailure 53 → 0), but the metadata lists P008 first. Always sort by CycleToFailure (descending) to get the true sequence.

### A5. How failure was defined and detected

- "Cutter damage was characterized by complete breakage (Fig. 14a and b) or the breakage of one of the blades (Fig. 14c)" [P1].
- The label is CycleToFailure, the number of cycles left until failure, with 0 at the failure cycle. CycleToFailureNormalized runs from 1 (new tool) to 0 (failure cycle) [P1].
- The paper describes no automatic or sensor-based detection. Damage was seen on the tool. No flank-wear (VB) measurements were made, so this is a **run-to-fracture** dataset, not a run-to-VB-limit dataset (see B6).
- Tool 11 (160 mm holder) broke in its very first cycle (P114_F01_C1). The paper calls it "a random event … treated as an outlier but it left in the data set" [P1]; the companion paper says "the breakage was immediate" [P2]. The other 160 mm-holder tool (tool 10) lasted 15 recorded cycles (CycleToFailure 14 at its first cycle). The physics in B8 suggests these early failures are probably not random.
- The paper recommends grouped cross-validation, one tool per group, 13 usable tools [P1].

Tool lives, with total cutting minutes from [P2] Table 1:

| Tool | Type | ADOC | RDOC | Holder | Hardness (HRC) | Cycles to failure | Minutes of cutting |
|---|---|---|---|---|---|---|---|
| 2 | 1 | 5 | 8 | 80 | 35.3–36.7 | 49 | 25.4 |
| 3 | 1 | 10 | 8 | 80 | 37.5–40 | 49 | 25.4 |
| 4 | 1 | 5 | 8 | 80 | 35.3 | 40 | 20.7 |
| 5 | 1 | 10 | 8 | 80 | 37.5–38.3 | 53 | 26.8 |
| 6 | 1 | 5 | 8 | 80 | 40.0 | 29 | 15.1 |
| 7 | 1 | 10 | 4.5 | 80 | 39.3–41.3 | 126 | 64.2 |
| 8 | 1 | 5 | 4.5 | 80 | 39–41.7 | 115 | 58.9 |
| 9 | 1 | 5 | 4.5 | 80 | 37.3–39.3 | 149 | 76.2 |
| 10 | 1 | 10 | 4.5 | **160** | 37.3 | 14 | 8.8 |
| 11 | 1 | 10 | 4.5 | **160** | 37.2 | 0 | 0 |
| 101 | 2 | 10 | 4.5 | 80 | 37.8–39.3 | 83 | 42.1 |
| 102 | 2 | 5 | 4.5 | 80 | 38.3 | 84 | 42.8 |
| 103 | 2 | 10 | 4.5 | 80 | 39.2–39.8 | 59 | 30.1 |
| 105 | 2 | 5 | 4.5 | 80 | 38.3–38.5 | 124 | 63.5 |

Patterns: RDOC 8 mm cuts life to roughly a third. [P2] also notes that ADOC had no noticeable effect on life in this data. Within the same settings, harder blocks gave shorter lives (tool 6 at 40 HRC: 29 cycles, against 40–49 for tools 2 and 4 at 35–37 HRC; tool 8 at 39–41.7 HRC: 115, against 149 for tool 9 at 37–39 HRC). Both long-holder tools failed almost at once.

### A6. Figures in the paper, and the licence

The licence line: "This article is licensed under a Creative Commons Attribution 4.0 International License, which permits use, sharing, adaptation, distribution and reproduction in any medium or format, as long as you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons licence, and indicate if changes were made" [P1]. **CC BY 4.0 is confirmed**, so the figures can go in slides with attribution. The article has no third-party credit lines on the figures.

Attribution text to use: *Figure N from G. Piecuch & T. Żabiński, "A new open dataset from a milling process – data for classification and estimation of tool life", Scientific Data 12, 650 (2025), https://doi.org/10.1038/s41597-025-04923-y, licensed CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). [Cropped/relabelled.]*

Full-size image URL pattern: `https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41597-025-04923-y/MediaObjects/41597_2025_4923_FigN_HTML.png` (replace N).

| Fig | Caption (quoted) | What it shows | Use in explainer |
|---|---|---|---|
| 1 | "Haas VF-1milling machine with coordinate system designation." | The machine with X, Y, Z arrows | Setup slide |
| 2 | "Location of accelerometers on the spindle of the Haas VF-1." | Ch1–Ch3 on the spindle housing, near coolant nozzles | Sensors slide |
| 3 | "Location of accelerometers on the drive axes of the Haas VF-1." | Ch4–5 on the X ball-nut housing, Ch6–8 on the Y ball-nut housing | Sensors slide; explains "driving axle" |
| 4 | "Data recorder." | Beckhoff cabinet | Optional |
| 5 | "Division of the sample into layers depending on ADOC …" | Block sliced into layers | "What is a cycle" |
| 6 | "Division of the sample into cycles depending on RDOC …" | Seven rings (4.5 mm) or four rings (8 mm), milling direction | "What is a cycle" (best one) |
| 7 | "Schematic illustrating the ADOC and RDOC parameters." | Step cut with ADOC and RDOC marked | Depth-of-cut slide |
| 8 | "Numbering scheme for the milling experiment." | P/F/C naming | Data slide |
| 9 | "Experimental and data collection procedures." | Flow chart | Optional |
| 10 | "Sample before and after milling." | Block before and after | Setup slide |
| 11 | "Interpretation of the spindle current signal (L1) for cycle 1." | Spindle current against time: start spike about 7 A, idle about 2.6 A, corner bumps 1A–4B, then about 3.6 A of steady cutting, stop spike about 8 A; with a sketch of the block | Best "current = load" picture |
| 12 | "Interpretation of the spindle current signal (L1) for cycle 3." | Same for cycle 3: idle 2.6 A, cutting about 3.7–4.1 A, small bumps at the four corners | Same |
| 13 | "Location of sites marked as 1 A and 1B in Fig. 11 …" | Photo of a machined corner | Optional |
| 14 | "Different degrees of cutter damage." | (a) snapped off at the holder face, (b) gold Type 1 with broken tip, (c) grey Type 2 with one corner broken (circled) | Failure slide (best one) |
| 15 | "New cutters." | (a) new Type 1, four teeth visible end-on, (b) new tool in holder | Anatomy and stick-out |
| 16 | "Damaged cutters (on the left MillingToolType – 1, on the right MillingToolType – 2)." | All broken tools; most snapped across the fluted part near the shank | Failure slide |
| 17 | "Accelerometer connected to Bruel&Kjaer 4296 vibration exciter before mount inside CNC." | Calibration (159.2 Hz, 10 m/s² RMS) | Optional |

### A7. What the paper says about signals near failure

Nothing quantitative. The paper describes the setup and points to companion work. It only interprets the spindle current within a cycle (Figs 11–12: idle, corners, cutting). [P2] also reports no numerical trends; it trains regression models (best R² about 0.96 in cross-validation) on the six time-domain statistics per channel. The aggregated feature file holds min, max, mean, std, skewness and kurtosis for each of the 20 channels, 120 features in total [P1].

What we measured ourselves **[our data]** (7 Type-1 tools with 80 mm holders, all their recorded cycles; method in Appendix A). Values are relative to each tool's first 10 % of life; cycle-1 files are excluded.

| Life fraction → | 0–10 % | 10–30 % | 30–50 % | 50–70 % | 70–90 % | 90–100 % |
|---|---|---|---|---|---|---|
| Net spindle current (cut − idle), range across 7 tools | 1.00 | 0.92–1.06 | 0.98–1.15 | 1.07–1.21 | 1.13–1.40 | **1.23–1.49** |
| X-axis drive current while cutting | 1.00 | 0.98–1.07 | 1.04–1.34 | 1.17–1.56 | 1.35–2.00 | **1.44–2.66** |
| Once-per-rev vibration line (53.3 Hz, X-axis +Z sensor) | 1.00 | 0.55–1.08 | 0.62–2.36 | 0.87–3.95 | 0.55–9.0 | **0.82–13.0** (above 2 in 6 of 7 tools) |
| Tooth-passing line (213 Hz, X-axis +Z sensor) | 1.00 | 0.86–1.49 | 0.98–3.39 | 1.07–5.78 | 1.27–9.85 | **1.23–10.3** |

The shape is the classic three-stage wear curve: flat for the first third to half of life, then a rising "knee". The spindle idle current (about 2.57 A) did not drift at all, so the rise is cutting load, not machine warm-up. Rank correlation (Spearman) of X-axis current with elapsed life was 0.77–0.96 for every tool, the most consistent of all signals we tried. Type-2 tools and the 160 mm-holder tools were not in the part of the raw archive available when this was written (only blocks P002–P023), so check them later.

### A8. Errata and gotchas found in the paper

1. Layer counts are swapped in the text: ADOC 5 mm gives 12 layers, not 6 (see A4).
2. Table 3 of the paper labels FeedRate as "[rpm]". The metadata file says mm/min, which is correct.
3. The text says Figs 11–12 are from RDOC 4.5 mm experiments, but the files shown (P002_F02_C01/C03) belong to tool 2, which ran at RDOC 8 mm. The drawings show four rings, which also means 8 mm.
4. The time axes of Figs 11–12 are about half what the file timestamps give. For P002_F02_C03 the figure shows about 27 s of spindle running; the file shows 56.8 s. The timestamps are the ones to trust. The spindle line sits at exactly 53.4 Hz (3200 rpm) on the file's timebase. The loaded time (28.6 s) matches the ring's path length at 640 mm/min: the cycle-3 ring at RDOC 8 has its tool centre on a 112 × 42 mm rectangle, 308 mm long, which takes 28.9 s.
5. Accelerometer model: "3055D2" in [P1] and "3055A2" in [P2].
6. Current channels are RMS updated every 200 ms, not 500 Hz waveforms (A3).

---

## Part B. The mechanics, with sources

### B1. Anatomy of an end mill and its holder

- **End mill**: a rotating cutter that cuts with its side and its end [B18], [B20]. Our cutters are solid tungsten-carbide, Ø10 mm.
- **Flutes**: the helical grooves that carry chips away. Each flute has one **cutting edge (tooth)** along its leading side. Our tools have 4 flutes, so 4 teeth.
- **Helix angle**: how steeply the flutes twist (35–38° for Type 1, 50° for Type 2). A helical edge enters the work gradually, not all at once, so the force is smoother. It also pushes chips up the flute, which creates an axial (up/down) force. A **variable helix** (Type 1) spaces the teeth unevenly to break up the regular rhythm that feeds chatter [M1], [B3].
- **Corner**: where the side edge meets the end edge. It is the most fragile point. A corner radius (Type 1, R0.5) or chamfer (Type 2, 0.2 mm) strengthens it.
- **Shank**: the plain cylinder that is clamped (Ø10 mm, h5 tolerance on Type 1).
- **Holder**: the part between spindle and cutter. Here it is a **shrink-fit (thermal) holder** [P1]: its bore is heated, the shank is inserted, and the bore grips it on cooling. This gives high grip and very low runout. A **collet chuck** instead squeezes a slotted sleeve (the collet) around the shank with a nut. It is quicker to change but usually less stiff and less concentric. Neither collet nor runout values are given in the paper.
- **Overhang / stick-out**: the free length from the spindle face (holder length) plus the cutter's stick-out from the holder. It acts as a cantilever beam (B8).

### B2. Axial vs radial depth, and radial engagement

- **Axial depth of cut, ADOC or ap**: how much of the flute length is in the material, measured along the tool axis (5 or 10 mm here). See paper Fig. 7.
- **Radial depth of cut, RDOC or ae**: how far into the side of the material the tool reaches, measured across the tool (4.5 or 8 mm).
- **Radial engagement** = ae / D (45 % or 80 %).
- **Engagement angle** φ = arccos(1 − 2·ae/D): the arc each tooth spends cutting per revolution. 84.3° at 45 %, 126.9° at 80 %. With 4 teeth spaced 90° apart, on average 4·φ/360 teeth are cutting at once: 0.94 or 1.41 teeth.
- **Chip thickness** varies along that arc as h(ψ) = fz·sin ψ. Average chip thickness: hm = fz·(1 − cos φ)/φ. This gives 0.031 mm at 45 % and 0.036 mm at 80 % (with fz = 0.05 mm) [B1], [B3]. Climb milling starts the chip at its thickest (about 0.05 mm).

### B3. The basic formulas [B1]

- Cutting speed (edge speed): **v = π·D·n** (D in m, n in rev/min → m/min).
- Feed per tooth: **fz = vf / (z·n)**. Here vf is the table feed (mm/min) and z the number of teeth.
- Material removal rate: **Q = ap · ae · vf** (mm³/min).
- Cutting power: **Pc = Q · kc** (kc = specific cutting force, which equals specific cutting energy). kc is not constant: by Kienzle's law **kc = kc1.1 · h^(−mc)**, so thin chips cost more energy per mm³. For 42CrMo4: kc1.1 = 2500 N/mm², mc = 0.26 [B2]. (Units: 1 N/mm² = 1 J/mm³ = 1 W·s/mm³.)
- Spindle torque: **M = Pc / (2π·n/60)**.
- Textbook specific energies for steels: about 2–9 W·s/mm³ [B17]. Our estimate below (about 6 J/mm³) sits inside that range.

### B4. The two clocks inside a milling signal

- **Spindle (once-per-revolution) frequency**: f_s = n/60. Anything that differs from one revolution position to another repeats at this rate: runout (the tool spinning slightly off-centre), one tooth longer or shorter than the others, or one chipped tooth.
- **Tooth-passing frequency**: f_t = z·n/60. Each tooth entering the cut is a hammer blow, so the force (and vibration) repeats z times per revolution. The force pulse is not a sine wave, so energy also appears at the harmonics 2f_t, 3f_t and so on [B3], [B4].
- With 4 equal sharp teeth, the spectrum has lines only at multiples of f_t (spindle orders 4, 8, 12 …), plus small runout lines at order 1. Unequal teeth fill in the orders in between (1, 2, 3, 5, 6, 7 …).

### B5. How tools wear and break

Wear mechanisms (Wikipedia gives the basic definitions [B18]; [B7], [B8], [B21], [B22] cover the end-mill view):
- **Flank wear (VB)**: the face below the cutting edge rubs on the freshly cut surface and wears a flat "land" of width VB. It is caused by abrasion from hard carbides in the steel, plus adhesion and diffusion at high temperature. This is the standard measure of gradual wear.
- **Crater wear (KT)**: the hot chip sliding over the top (rake) face scoops a crater, mainly through diffusion and chemical wear at high temperature.
- **Chipping**: small pieces break off the edge from impact and fatigue. Milling is interrupted cutting, so each tooth is hammered on every entry: 213 times per second here.
- **Edge fracture / breakage**: a large piece, a whole tooth, or the whole tool breaks off. It happens when force or bending stress exceeds the carbide's strength, often after chipping has blunted the edge and raised the force. This is how every tool in our dataset ended [P1].
- **Built-up edge (BUE)**: workpiece material welds onto the edge. It is most common at low speeds in soft, sticky materials such as aluminium or low-carbon steel [B18]. It is less likely at 100 m/min in 38 HRC steel.
- **Thermal (comb) cracking**: in interrupted cutting the edge heats while cutting and cools in air (or coolant) many times per second. The cycling cracks the edge across its length. Cracks then join and cause chipping.
- **Three-stage wear curve**: (1) break-in, a short fast wear as the sharp edge rounds off; (2) steady wear, a long slow linear stage; (3) rapid wear, where the worn edge runs hotter and pushes harder, so wear speeds up until failure [B21]. [B21] describes the rapid stage as "severe damage, such as chipping, cracking, or plastic deformation". Our current and vibration trends in A7 follow this shape: flat, then a knee.

### B6. End-of-life criteria

- **ISO 8688-2:1989, "Tool life testing in milling — Part 2: End milling"** [B15]. The standard is paywalled; we could not open it. The values commonly quoted from it: tool life ends at **average flank wear VB = 0.3 mm** (uniform wear) or **maximum flank wear VBmax = 0.5 mm** on any tooth (uneven wear), or at chipping or catastrophic failure.
- For comparison, the turning standard ISO 3685 uses VB = 0.3 mm (uniform) or 0.6 mm (maximum).
- Practical meaning: most public milling datasets label life by measured VB (for example, the PHM 2010 challenge data, cited as ref. 25 in [P1]). **Our dataset labels life by fracture.** The two endpoints are different events, so cross-dataset comparisons must line up "fraction of life", not raw cycles or minutes.

### B7. Taylor's tool-life equation (for "slow down to extend life")

- Basic form: **v · Tⁿ = C**. Here v is cutting speed (m/min), T is tool life (min) at that speed, and n and C are found by experiment [B23], [B18]. Extended form: v·Tⁿ·f^a·d^b = C, which adds feed and depth.
- Typical n (textbook ranges, Kalpakjian & Schmid [B17]): high-speed steel 0.08–0.2; carbide 0.2–0.5; **coated carbide 0.4–0.6**; ceramics 0.5–0.7. For coated carbide on alloy steel, use **n ≈ 0.25–0.4** as a planning range (the low end of coated carbide, conservative) and calibrate C on our data. Textbook C values are for turning tests and do not transfer to a Ø10 end mill.
- Calibrated example (tool 8, 58.9 min of cutting at 100.5 m/min): C = 100.5 × 58.9ⁿ, which gives **C ≈ 278 m/min for n = 0.25** and **≈ 513 m/min for n = 0.4**.
- What slowing the spindle buys. Life in minutes scales as v^(−1/n). If fz is kept constant (feed slowed with the spindle), each cycle takes 1/s times longer, where s is the speed factor (0.9 = 10 % slower). So life in cycles scales as v^(1 − 1/n):

| Change | n = 0.25: life (min) | n = 0.25: life (cycles) | n = 0.4: life (min) | n = 0.4: life (cycles) | Output per hour |
|---|---|---|---|---|---|
| 10 % slower | ×1.52 | ×1.37 | ×1.30 | ×1.17 | ×0.90 |
| 20 % slower | ×2.44 | ×1.95 | ×1.75 | ×1.40 | ×0.80 |

- **Caveat that matters for us.** Taylor describes gradual wear set mostly by temperature (speed). Our tools died by **fracture**, which depends mostly on force per tooth (fz, ae, ap) and on stiffness (overhang). Slowing the spindle at constant fz does not reduce the force per tooth. Reducing fz or ae does. Model "slow down" as two levers: a wear lever (speed, Taylor) and a load lever (feed and engagement, force). The data show the load lever is large: going from RDOC 4.5 to 8 mm cut life about 3×.

### B8. Overhang, stiffness, chatter: why the 160 mm holders failed early

- **Cantilever bending**: a beam of length L, clamped at one end and pushed sideways at the tip by force F, deflects **δ = F·L³ / (3·E·I)**. E is the material stiffness and I = π·d⁴/64 for a round bar [B20]. So **stiffness k = F/δ falls as 1/L³**: double the length and it bends 8× more.
- **Natural frequency** of the same beam falls as 1/L². A longer tool-holder rings at a lower pitch.
- **Chatter** is a self-excited vibration. Each tooth cuts a surface left wavy by the previous tooth. If the waves line up badly, the chip thickness and force oscillate and grow on their own [B3], [B4], [B5], [B6]. Chatter occurs near a natural frequency of the tool-holder-spindle structure, **not** at the tooth-passing frequency. The deepest cut that stays chatter-free is roughly proportional to stiffness × damping (b_lim ≈ 2kζ(1+ζ) / (Ks·N*) in Schmitz & Smith's notation [B4]). So 5–8× less stiffness means a 5–8× smaller safe depth.
- **Our case**: the 160 mm holder doubles the holder length. Counting the cutter's 25–35 mm stick-out, the total overhang rises from about 105–115 mm to 185–195 mm. That makes the setup **about 5–8× less stiff** and lowers its natural frequency **about 3–4×** (see C6). Both 160 mm runs also used the **10 mm** axial depth. The likely story: a much softer structure, a deep cut, chatter or large deflection, and a fast fracture (cycles 0 and 14). This is our physics reading; the paper gives no vibration analysis of those runs. Checking it in the raw files (blocks P112 and P114) is a good first experiment once the archive is complete.
- Where tools snap: bending moment is largest at the clamp edge, and the fluted section has a thinner core than the shank. Most broken tools in Fig. 16 snapped across the flutes near the shank.

### B9. Effect of workpiece hardness

- 42CrMo4 at 35–42 HRC is quenched and tempered steel with tensile strength of roughly 1.1–1.35 GPa (standard hardness-to-strength conversion). Harder, stronger steel needs more force per mm² of chip (kc1.1 rises with strength; compare 2100 N/mm² for 16MnCr5 with 2500 for 42CrMo4 [B2]). It also contains harder particles, so abrasive flank wear is faster, and the edge runs hotter.
- In our data, harder blocks gave shorter lives within the same settings (see A5). Hardness also changes mid-life, because a tool moves between blocks (tool 8 went from 41.7 to 39.0 HRC), so add HardnessMean as a model input.

### B10. How wear changes forces and specific energy

- A worn edge is blunter (larger edge radius) and carries a flank land rubbing on the new surface. Rubbing and ploughing add force without removing more metal. So **specific cutting energy (J per mm³) rises** [B7], [B8], [B12].
- The rubbing force acts mostly **normal to the machined surface**, so the feed and radial (thrust) forces grow faster than the main tangential force. Reviews report that feed and thrust components are more sensitive to flank wear [B8].
- **[our data]** fits this exactly. The feed-drive current (thrust and feed direction) rose 1.4–2.7×, while the net spindle current (tangential, power) rose 1.2–1.5×.
- Chipping makes the teeth unequal. One tooth takes a bigger bite or misses, which adds once-per-revolution force content (B12).

### B11. Why motor current tracks force

- **Spindle**: at a constant speed, mechanical power = torque × speed, and torque = tangential cutting force × tool radius. The drive supplies that power plus a fixed idle loss (bearings, fan, magnetising current). In a vector-controlled motor the stator current is split into a flux-making part (constant at constant speed) and a torque-making part ("the q-axis component is used to control the motor torque" [B19]). So **current above idle rises with cutting torque**. It is not exactly proportional, because the RMS of the two parts does not add linearly and supply-side power factor matters. Spindle power and current have long been used for tool monitoring [B11], [B12].
- **[our data]**: the net spindle current at the start of life is **0.47 ± 0.03 A per kW** of predicted cutting power (Pc = Q·kc with Kienzle values). This holds across all four ADOC×RDOC settings and seven tools, even though power ranges 3.4× (1.5 to 5.1 kW). So on this machine, about 1 A of net spindle current ≈ 2 kW of cutting.
- **Feed axes**: a servo motor turns a ball screw. Motor torque = axial force on the nut × lead / (2π × efficiency) + friction, and servo torque ∝ motor current. So the axis current ≈ friction part + (force along that axis) × constant. Feed-drive currents have been used to estimate milling forces and detect tool breakage since the early 1990s [B10]. Around a rectangle, X and Y swap roles. On the long sides (moving along X), the X drive carries the feed-direction force and Y carries the force pressing into the wall; on the short sides it is the reverse.
- **Z axis**: Z is stationary during these cuts. Its current reflects holding the head plus the axial force that the helix creates.

### B12. Vibration fingerprints [B3], [B4], [B5], [B6], [B7], [B14]

| Condition | What happens physically | Where it shows in the spectrum |
|---|---|---|
| Normal sharp cutting | Each tooth's force pulse repeats at f_t | Lines at f_t = 213.3 Hz and harmonics (426.7, 640, …); small line at f_s = 53.3 Hz from runout |
| Gradual wear | Larger, more rubbing forces | Tooth-pass lines grow; broadband high-frequency noise grows (friction) |
| Runout | Tool axis slightly off spindle axis; one tooth always cuts more | f_s = 53.3 Hz line and its harmonics; sidebands at k·f_t ± f_s |
| Chipped or broken tooth | One tooth cuts less, the next cuts more; force pattern repeats once per revolution | Strong growth at f_s and at orders not divisible by 4 (1, 2, 3, 5, 6, 7 × 53.3 Hz); sidebands around each f_t harmonic; sudden spikes (high kurtosis) |
| Chatter | Self-excited vibration of the tool-holder structure | A strong peak near a structural natural frequency that is **not** a multiple of 53.3 Hz, with sidebands spaced at f_t; the energy share at spindle harmonics drops |

**[our data] spectrum check** (P002_F01_C3, cutting part only). On the axis sensors, the strongest lines sit at 106.8, 159.5, **212.9**, 426.5, 640.1 Hz and so on, and the 4th spindle order (212.9 Hz) holds 70 % of the X-axis +Z power. The spindle-housing sensors also show large non-synchronous peaks near 4.9–5.2 kHz and 9.4–12 kHz, present even in air. These are probably spindle and structure resonances, not cutting. One more effect matters for feature design. The **tooth-pass line is about 5–14× weaker at ADOC 10 mm than at 5 mm** for Type 1, even though the force is larger. The reason is helix cancellation, explained in C7.

---

## Part C. Numbers for our dataset

Inputs: D = 10 mm, z = 4, n = 3200 rpm, vf = 640 mm/min. Kienzle values for 42CrMo4: kc1.1 = 2500 N/mm², mc = 0.26 [B2].

### C1. Speeds and feeds

| Quantity | Formula | Value |
|---|---|---|
| Cutting speed | π·D·n | **100.5 m/min** (1.68 m/s) |
| Feed per revolution | vf / n | 0.200 mm |
| Feed per tooth | vf / (z·n) | **0.050 mm** |
| Spindle frequency | n / 60 | **53.33 Hz** (one revolution = 18.75 ms) |
| Tooth-passing frequency | z·n / 60 | **213.33 Hz** (one tooth = 4.69 ms) |

### C2. Per setting

| ADOC × RDOC (mm) | Radial engagement | Engagement angle | Teeth in cut (average) | Mean chip hm (mm) | MRR Q | Predicted kc | Predicted cutting power | Spindle torque | Mean tangential force at edge |
|---|---|---|---|---|---|---|---|---|---|
| 5 × 4.5 | 45 % | 84.3° | 0.94 | 0.0306 | **14,400 mm³/min** (14.4 cm³/min) | 6190 N/mm² | 1.49 kW | 4.4 N·m | ≈ 890 N |
| 5 × 8 | 80 % | 126.9° | 1.41 | 0.0361 | **25,600 mm³/min** | 5930 N/mm² | 2.53 kW | 7.5 N·m | ≈ 1510 N |
| 10 × 4.5 | 45 % | 84.3° | 0.94 | 0.0306 | **28,800 mm³/min** | 6190 N/mm² | 2.97 kW | 8.9 N·m | ≈ 1770 N |
| 10 × 8 | 80 % | 126.9° | 1.41 | 0.0361 | **51,200 mm³/min** | 5930 N/mm² | 5.06 kW | 15.1 N·m | ≈ 3020 N |

Notes: the kc, power, torque and force columns are order-of-magnitude estimates. Kienzle constants come from turning tests and are stretched here to very thin chips. They also ignore hardness, rake angle and coolant. The power ratios between settings are reliable: the measured net spindle currents follow them within about ±10 % (B11). The maximum chip thickness is about 0.050 mm in all four settings (climb milling, entry chip ≈ fz).

### C3. Volume, path and time per cycle (from [P2] Table 1)

| Setting | Path per cycle | Volume per cycle | Cutting time per cycle |
|---|---|---|---|
| RDOC 8 (ADOC 5 / 10) | ≈ 366 mm | ≈ 14,640 / 29,280 mm³ | ≈ 31.1 s |
| RDOC 4.5 (ADOC 5 / 10) | ≈ 352–354 mm | ≈ 7,960 / 15,840 mm³ | ≈ 30.6 s |

### C4. Frequencies and harmonics

- Tooth-pass harmonics: 213.3, 426.7, 640.0, 853.3, 1066.7, 1280.0, 1493.3, 1706.7, 1920.0, 2133.3 Hz … There are 58 below 12.5 kHz (the last is 12,373 Hz).
- Spindle harmonics (orders): 234 below 12.5 kHz. Orders 4, 8, 12 … are tooth-pass lines. Orders 1–3, 5–7 … are "unequal-teeth" lines.
- Frequency resolution needed: to separate a 53.3 Hz sideband from a tooth line, use bins of a few Hz or less. A Welch FFT with 2¹⁴ = 16,384 points at 25 kHz gives 1.53 Hz bins (0.66 s windows). Our cutting segments are 24–60 s long, so that is plenty.

### C5. Nyquist limits: what each sensor can and cannot see

| | Vibration (accelerometers) | Current (as recorded) |
|---|---|---|
| Logging rate | 25 kHz | 500 Hz |
| Nyquist limit (half the rate) | **12.5 kHz** | 250 Hz nominal, but **the values update only every 200 ms → effective 5 Hz, Nyquist ≈ 2.5 Hz** [our data] |
| Can see | Spindle line 53.3 Hz and its harmonics; tooth-pass 213.3 Hz and 58 harmonics; sidebands; chatter at structural modes below 12.5 kHz; bearing and friction noise | Spindle on/off, start and stop spikes; idle vs cutting; corners (bumps lasting a few seconds); entering and leaving the material; slow cycle-to-cycle drift as the tool wears |
| Cannot see | Anything above 12.5 kHz (acoustic emission at 100 kHz+, high resonances), unless it aliases, which depends on the EL3632's anti-alias filter setting (5th-order low-pass, adjustable up to 25 kHz [M7]; the setting used is not reported). Steady, unchanging forces: an accelerometer only senses change. | Anything per revolution or per tooth: 53.3 Hz runout, 213.3 Hz tooth pass, chatter, single-tooth impacts. Even at a true 500 Hz the 213 Hz line would sit close to Nyquist and its harmonics would alias. |

Plain words: vibration is the fast microphone that hears each tooth. Current is the slow electricity meter that shows how hard the motor is working, five readings a second.

### C6. Holder length: stiffness ratio 160 mm vs 80 mm

Treat the overhang as a uniform cantilever: k ∝ 1/L³ and f_n ∝ 1/L².

| Cutter stick-out assumed | Total overhang 80 → 160 holder | Stiffness ratio (80 holder ÷ 160 holder) | Natural-frequency ratio |
|---|---|---|---|
| 0 (holder only) | 80 → 160 mm | **8.0×** | 4.0× |
| 25 mm | 105 → 185 mm | **5.5×** | 3.1× |
| 35 mm | 115 → 195 mm | **4.9×** | 2.9× |

So the long-holder setup is roughly 5–8× bendier, with a natural frequency 3–4× lower. Real holders are tapered, so this is a bound, not a measurement.

### C7. Helix cancellation of the tooth-pass vibration (why ADOC changes the 213 Hz line)

- Axial pitch of a helix: p = π·D / (z·tan β). For 35° → **11.2 mm**, 38° → **10.1 mm**, 50° (Type 2) → **6.6 mm**.
- A helical edge spreads each tooth's impact along the axis. The tooth-frequency force adds up over the depth as ∫ e^(i2πz/p) dz. Its size is proportional to (p/π)·|sin(π·ap/p)|. When ap is close to a whole number of pitches, the 213 Hz force nearly cancels.
- Type 1 (35–38°): ap = 5 mm → factor 3.2–3.5; ap = 10 mm → factor 0.05–1.2. So the 10 mm cut has **0.02–0.34×** the 213 Hz force of the 5 mm cut. Measured on the X-axis +Z sensor: 0.05–0.09 m/s² at ADOC 10 (tools 3, 5, 7) against 0.44–0.66 m/s² at ADOC 5 (tools 2, 4, 6, 8), a ratio of about 0.07–0.2. This fits.
- Type 2 (50°): the opposite. ADOC 10 should give about 1.45× the 5 mm value.
- Consequence: raw tooth-pass amplitude is **not comparable across ADOC or helix**. Use it only as a ratio to the same tool's early cuts. A rising 213 Hz line in an ADOC 10 run (tool 7: ×10) means wear or chipping has broken the cancellation.

### C8. Energy per volume [our data]

Net spindle charge per cycle ÷ volume per cycle (C3) at the start of life: **2.4–3.5 × 10⁻³ A·s per mm³** across 7 tools and all four settings. By the last eighth of life: 3.2–4.3 × 10⁻³ (×1.22–1.52). Using the 0.47 A/kW factor above, this corresponds to about 6 J/mm³ when new, inside the textbook 2–9 J/mm³ for steels [B17]. The value is circular, because the factor came from the Kienzle estimate. Turning it into true joules needs supply voltage and power factor, or a calibration cut.

---

## Part D. Physics features to compute from the raw signals

Common preprocessing:
1. Average the three phases of each current.
2. Find idle = 20th percentile of spindle current while the spindle is on (about 2.57 A).
3. Mark "cutting" where spindle current > idle + 0.3 A.
4. Map cutting time onto the 25 kHz vibration by timestamp.
5. Drop cycle-1 files, or compare them only to other cycle-1 files, because they include corner clean-up.
6. Sort by CycleToFailure.

Normalise each feature two ways:
- **(a) ratio to the same tool's first N cuts** (removes machine, sensor mount and setting);
- **(b) per unit MRR, or per spindle order** (removes the setting, so values compare across tools and datasets).

| # | Feature | How to compute | Why it should change with wear | What we saw [our data] | Cross-dataset form |
|---|---|---|---|---|---|
| 1 | **Net spindle current** | mean(I_spindle − I_idle) over cutting | Tracks cutting torque and power. A blunt, rubbing edge needs more energy per chip | Flat to mid-life, then ×1.23–1.49 at end; Spearman 0.59–0.84 | Ratio to first cuts; or ÷ MRR (feature 2) |
| 2 | **Specific cutting energy (proxy)** | ∫(I − I_idle)dt over the cycle ÷ volume removed (A·s/mm³); in J/mm³ if voltage, power factor or spindle power are known | Wear adds rubbing and ploughing that removes no metal, so energy per mm³ rises (B10) | 2.4–3.5e-3 A·s/mm³ when new in all 4 settings (±12 %); ×1.22–1.52 at end | **Best single cross-dataset feature**: J/mm³ is setting-independent and many datasets log spindle power |
| 3 | **Feed-axis current while cutting** | mean of X (and Y) phase-averaged current during cutting, minus its value for the same moves in air if available | Feed and thrust forces grow fastest with flank wear (B10) | ×1.44–2.66; Spearman 0.77–0.96 in all 7 tools; the most reliable trend | Ratio to first cuts (absolute amps depend on the machine) |
| 4 | **Force-direction ratio** | feed-axis net current ÷ net spindle current | Wear tilts the force toward the surface normal (thrust grows faster than torque). The ratio cancels MRR | Rises (feature 3 grows faster than feature 1) | Ratio to first cuts |
| 5 | **Tooth-pass band amplitude** | √(power in f_t ± 2 Hz), also 2f_t and 3f_t, on the axis accelerometers | Bigger force pulses as the edge dulls; unequal teeth break helix cancellation | ×1.07–12, last six vs first six cuts (largest at ADOC 10, where the baseline is cancelled) | Use spindle orders (4, 8, 12) and ratio-to-first-cuts only (C7) |
| 6 | **Once-per-rev (asymmetry) index** | power at orders 1, 2, 3, 5, 6, 7 … ÷ power at orders 4, 8, 12 … | A chipped or broken tooth makes revolutions repeat once per turn instead of once per tooth | Order-1 line ×2–13 near the end in 6 of 7 tools; tool 6 asymmetry ×7–13 | Dimensionless; directly comparable across datasets in spindle orders |
| 7 | **Sideband energy** | power at k·f_t ± f_s | Same physics as 6, seen as modulation of each tooth line | Not yet computed | Dimensionless ratio |
| 8 | **Synchronous fraction (chatter check)** | power at spindle orders 1–40 ÷ total power (X-axis +Z sensor) | Chatter puts energy at a structural mode that is not a spindle order, so the fraction drops | 0.86–0.95 at ADOC 5. At ADOC 10 it is 0.46–0.60 when new (tooth lines cancelled, C7), rising to 0.73–0.89 by the end. A few single cycles drop below 0.1: inspect them for chatter or glitches, and check the 160 mm runs | Dimensionless |
| 9 | **High-band RMS (2–12 kHz)** on axis sensors, ÷ same in air | Welch power over 2–12 kHz while cutting and in air | Rubbing of the wear land and micro-impacts add broadband noise | Mixed. Spindle-housing sensors are dominated by spindle noise, so use axis sensors | Ratio to air and to first cuts |
| 10 | **Spectral kurtosis / kurtosis of band-passed vibration** | kurtosis per frequency band (Antoni's spectral kurtosis [B14]) | Chipping and cracking produce short impacts, which make the signal "spiky" (high kurtosis) | Spindle-housing kurtosis was very high (8–127) early and fell later, likely spikes or glitches, not wear. Clean the data before trusting it | Dimensionless |
| 11 | **Corner and entry peak ratio** | peak net spindle current at corners ÷ straight-run net current | Corners briefly raise engagement. A weakened edge shows larger overshoot | Not yet computed | Ratio |
| 12 | **Cumulative load** | running sums of volume removed, cutting time, and net spindle charge since a new tool | Damage accumulates (Taylor and fatigue thinking); lets models compare tools in "work done", not cycles | From [P2]: life ranged 0.22–2.0 million mm³ | mm³, minutes and J are universal units |

Things to avoid or treat carefully:
- Do not compare raw tooth-pass amplitudes across ADOC or helix (C7).
- Spindle-housing accelerometers mostly hear the spindle itself.
- Current channels contain nothing above about 2.5 Hz.
- Absolute currents on the axes are near the transformers' noise floor (A3).
- Hardness changes when a tool moves to a new block.

---

## Part E. Openly licensed images for slides

Licences were checked on the Commons API or the article's licence line. Spot-check: we re-confirmed 1A, 4A, 5A, 4D, 1C and 2D on the Commons API. MDPI figure links open in a browser but refuse scripts (HTTP 403), so save them from the browser.

- **CC BY**: credit the author and licence; add "adapted" or "cropped" if you change the image.
- **CC BY-SA**: same, and an edited version must stay CC BY-SA.
- **Public domain (PD)**: no credit needed; credit as a courtesy.

**From our dataset paper (CC BY 4.0, best for our story):** Figs 1, 2, 3, 6, 7, 11, 12, 14, 15, 16. URLs and attribution are in A6.

| Slot | Image | Licence | Page / image URL | Attribution line |
|---|---|---|---|---|
| Anatomy | **"End Mill 02 labels"**: drawn 2-flute end mill labelled shank, flute, tooth, helix angle (no corner label) | Public domain | https://commons.wikimedia.org/wiki/File:End_Mill_02_labels.png / https://upload.wikimedia.org/wikipedia/commons/c/ca/End_Mill_02_labels.png | "End Mill 02 labels" by Rocketmagnet, via Wikimedia Commons, public domain |
| Anatomy | Bilal et al. 2024, Fig. 1: labelled end-mill geometry (rake face, relief face, helix) plus photos of a TiN-coated end mill | CC BY 4.0 | https://doi.org/10.3390/s24154777 / https://www.mdpi.com/sensors/sensors-24-04777/article_deploy/html/images/sensors-24-04777-g001.png | Fig. 1 from M. Bilal et al., Sensors 24(15):4777 (2024), doi:10.3390/s24154777, CC BY 4.0 |
| Anatomy | "MillingCutterSlotEndMillBallnose": photo of HSS (not carbide) 2-flute slot drill, 4-flute end mill and ball-nose | CC BY-SA 2.0 | https://commons.wikimedia.org/wiki/File:MillingCutterSlotEndMillBallnose.jpg | "MillingCutterSlotEndMillBallnose" by Glenn McKechnie, via Wikimedia Commons, CC BY-SA 2.0 |
| Wear | **Wei et al. 2021, Fig. 1**: camera images of an end mill showing (a) crater wear, (b) flank wear, (c) edge chipping, (d) broken tip | CC BY 4.0 | https://doi.org/10.3390/ma14195690 / https://www.mdpi.com/materials/materials-14-05690/article_deploy/html/images/materials-14-05690-g001.png | Fig. 1 from W. Wei et al., Materials 14(19):5690 (2021), doi:10.3390/ma14195690, CC BY 4.0 |
| Wear | K. Wang et al. 2024 (Sensors 24:2652), Fig. 8: end-mill corner at initial, normal and rapid wear; Fig. 7: three-stage wear curve (…-g007.png) | CC BY 4.0 | https://doi.org/10.3390/s24082652 / https://www.mdpi.com/sensors/sensors-24-02652/article_deploy/html/images/sensors-24-02652-g008.png | Fig. 8 (or 7) from K. Wang, A. Wang, L. Wu, G. Xie, Sensors 24(8):2652 (2024), doi:10.3390/s24082652, CC BY 4.0 |
| Wear | Zhao et al. 2024, Fig. 3: electron-microscope images of built-up edge and wear on an end-mill edge | CC BY 4.0 | https://doi.org/10.3390/ma17112744 / https://www.mdpi.com/materials/materials-17-02744/article_deploy/html/images/materials-17-02744-g003.png | Fig. 3 from X. Zhao et al., Materials 17(11):2744 (2024), doi:10.3390/ma17112744, CC BY 4.0 |
| Wear (schematic) | "Freiflaechenverschleiss.svg": flank-wear land VB on a generic tool edge (German labels); crater companion "Kolkverschleiss.svg" | Public domain | https://commons.wikimedia.org/wiki/File:Freiflaechenverschleiss.svg | "Freiflaechenverschleiss" by David W., via Wikimedia Commons, public domain |
| Broken | **K. Wang, A. Wang, L. Wu 2024 (Sensors 24:8107), Fig. 11**: coated end mill (a) new, (b) normal wear, (c) rapid wear, (d) broken corner | CC BY 4.0 | https://doi.org/10.3390/s24248107 / …/sensors-24-08107-g011a.png and …-g011b.png (base: https://www.mdpi.com/sensors/sensors-24-08107/article_deploy/html/images/) | Fig. 11 from K. Wang, A. Wang, L. Wu, Sensors 24(24):8107 (2024), doi:10.3390/s24248107, CC BY 4.0 |
| Broken (hook) | 1940s US poster "Carelessness is sabotage! It will take 90 days to replace this end mill …" with a drawing of a snapped end mill | Public domain (US Gov) | https://commons.wikimedia.org/wiki/File:Carelessness_is_sabotage%5E_It_will_take_90_days_to_replace_this_end_mill_broken_through_carelessness%5E_-_NARA_-_535065.jpg | U.S. Treasury Dept. poster (c. 1942–43), U.S. National Archives 535065, via Wikimedia Commons, public domain |
| Setup | **"Machining NICER's Patches"**: end mill in a holder cutting aluminium in a CNC mill, with chips and coolant (5472×3648) | Public domain (NASA) | https://commons.wikimedia.org/wiki/File:Machining_NICER%E2%80%99s_Patches_(SVS14610_-_NICER_MachineShop-11).jpg | "Machining NICER's Patches", NASA Scientific Visualization Studio, via Wikimedia Commons, public domain |
| Setup | "Makino-S33-MachiningCenter-example": vertical machining centre spindle, holder and end mill cutting | CC BY-SA 2.0 | https://commons.wikimedia.org/wiki/File:Makino-S33-MachiningCenter-example.jpg | "Makino-S33-MachiningCenter-example" by Glenn McKechnie, via Wikimedia Commons, CC BY-SA 2.0 |
| Setup | K. Wang, A. Wang, L. Wu 2024, Fig. 5: annotated machining centre with end mills, a Hall current sensor and data acquisition (matches our current theme) | CC BY 4.0 | …/sensors-24-08107-g005.png | Fig. 5 from K. Wang, A. Wang, L. Wu, Sensors 24(24):8107 (2024), CC BY 4.0 |
| Holder | "Fräser und Spannmittel": shrink-fit chuck with a carbide end mill, collet chuck, indexable mill (small, 740×528) | CC BY-SA 3.0 | https://commons.wikimedia.org/wiki/File:Fr%C3%A4ser_und_Spannmittel.jpg | "Fräser und Spannmittel" by Julius Schröder, via Wikimedia Commons, CC BY-SA 3.0 |
| Holder | Lai et al. 2022, Fig. 1: photo and drawing of a shrink-fit holder (no tool) | CC BY 4.0 | https://doi.org/10.3390/mi13081263 / https://www.mdpi.com/micromachines/micromachines-13-01263/article_deploy/html/images/micromachines-13-01263-g001.png | Fig. 1 from Z. Lai et al., Micromachines 13(8):1263 (2022), CC BY 4.0 |
| Diagram | **"Climb Milling 01" / "Conventional Milling 01"**: matched down- and up-milling diagrams | Public domain | https://upload.wikimedia.org/wikipedia/commons/8/83/Climb_Milling_01.png and https://upload.wikimedia.org/wikipedia/commons/4/41/Conventional_Milling_01.png | "Climb Milling 01" / "Conventional Milling 01" by Rocketmagnet, via Wikimedia Commons, public domain |
| Diagram | Zawada-Michałowska 2025, Fig. 1: end mill with ap and ae marked | CC BY 4.0 | https://doi.org/10.3390/ma18225219 / https://www.mdpi.com/materials/materials-18-05219/article_deploy/html/images/materials-18-05219-g001.png | Fig. 1 from M. Zawada-Michałowska, Materials 18(22):5219 (2025), CC BY 4.0 |
| Chatter + worn tool | **Ströbel et al. 2025, Fig. 16**: chatter marks on a machined part (circled) beside a new and a worn end mill | CC BY 4.0 | https://doi.org/10.1016/j.dib.2025.112207 / https://ars.els-cdn.com/content/image/1-s2.0-S235234092500928X-gr16_lrg.jpg | Fig. 16 from R. Ströbel et al., Data in Brief 63:112207 (2025), doi:10.1016/j.dib.2025.112207, CC BY 4.0 |
| Chatter | Casuso et al. 2022, Fig. 9: milled thin floors with chatter marks outlined | CC BY 4.0 | https://doi.org/10.3390/ma15030731 / https://www.mdpi.com/materials/materials-15-00731/article_deploy/html/images/materials-15-00731-g009.png | Fig. 9 from M. Casuso et al., Materials 15(3):731 (2022), CC BY 4.0 |

**Best six**:
1. Paper Fig. 14 (broken cutters, ours);
2. Paper Fig. 11 (current tells the story of a cycle);
3. "End Mill 02 labels" (anatomy);
4. Wei et al. Fig. 1 (four wear and breakage types);
5. "Machining NICER's Patches" (milling in action);
6. "Climb/Conventional Milling 01" (how teeth bite).

Gaps: no properly licensed clean photo of a 4-flute carbide end mill exists on Commons (use paper Fig. 15a, which is CC BY). No Commons photo of chatter marks. No Commons photo of a fully snapped carbide end mill (use paper Figs 14 and 16).

---

## Sources

Dataset and companion
- [P1] Piecuch G., Żabiński T. (2025). A new open dataset from a milling process – data for classification and estimation of tool life. *Scientific Data* 12:650. https://doi.org/10.1038/s41597-025-04923-y ; https://pmc.ncbi.nlm.nih.gov/articles/PMC12006439/ . Data: https://doi.org/10.6084/m9.figshare.28589216 . CC BY 4.0.
- [P2] Paszkiewicz A. et al. (2023). Estimation of Tool Life in the Milling Process—Testing Regression Models. *Sensors* 23:9346. https://doi.org/10.3390/s23239346 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC10708711/ . CC BY 4.0.

Manufacturer and hardware
- [M1] Van Hoorn Carbide webshop, VHVTR 4 100 070 10 03 050: https://webshop.hoorn-carbide.com/en/end-mills/vhc/stainless-steels-and-exotic-materials/vhvtr4/vhvtr41000701003050
- [M2] Van Hoorn Carbide webshop, PARA Tooling RS4 10,0x70: https://webshop.hoorn-carbide.com/en/end-mills/para-tooling/rs4/rs4100x70
- [M3] VHVTR4 cutting data (catalogue p. 61): https://webshop.hoorn-carbide.com/media/wysiwyg/images/snijgegevens/PDF/VHVTR4-snijgegevens.pdf
- [M4] PARA Tooling cutting data (catalogue p. 159): https://webshop.hoorn-carbide.com/media/wysiwyg/images/snijgegevens/PDF/Paratooling-snijgegevens.pdf
- [M5] Van Hoorn Carbide, PARA Tooling: https://www.hoorn-carbide.com/en/portfolio-item/para-tooling/
- [M6] WAGO 855-4001/0100-0001 plug-in current transformer (100 A / 1 A, 0.2 VA, class 1): https://www.wago.com/global/current-measurement/plug-in-current-transformer/p/855-4001_0100-0001
- [M7] Beckhoff EL3632 (2-channel IEPE input, max 50 ksamples/s, 16 bit, 5th-order low-pass up to 25 kHz): https://www.beckhoff.com/en-en/products/i-o/ethercat-terminals/el3xxx-analog-input/el3632.html . (The EL3413 product page was not reachable; its description as a three-phase power-measurement terminal is from general knowledge and matches the 200 ms RMS updates we measured.)

Mechanics and monitoring
- [B1] Sandvik Coromant, Milling formulas and definitions: https://www.sandvik.coromant.com/en-us/knowledge/machining-formulas-definitions/milling-formulas-definitions
- [B2] Wikipedia (de), Spezifische Schnittkraft (Kienzle; 42CrMo4 kc1.1 = 2500 N/mm², mc = 0.26; from Tschätsch / Schönherr): https://de.wikipedia.org/wiki/Spezifische_Schnittkraft
- [B3] Altintas Y. (2012). *Manufacturing Automation*, 2nd ed. Cambridge Univ. Press. https://doi.org/10.1017/CBO9780511843723
- [B4] Schmitz T.L., Smith K.S. (2019). *Machining Dynamics*, 2nd ed. Springer. https://doi.org/10.1007/978-3-319-93707-6
- [B5] Altintas Y., Weck M. (2004). Chatter stability of metal cutting and grinding. *CIRP Annals* 53:619–642. https://doi.org/10.1016/S0007-8506(07)60032-8
- [B6] Quintana G., Ciurana J. (2011). Chatter in machining processes: a review. *Int. J. Machine Tools & Manufacture* 51:363–376. https://doi.org/10.1016/j.ijmachtools.2011.01.001
- [B7] Teti R. et al. (2010). Advanced monitoring of machining operations. *CIRP Annals* 59:717–739. https://doi.org/10.1016/j.cirp.2010.05.010
- [B8] Dimla D.E. (2000). Sensor signals for tool-wear monitoring in metal cutting operations — a review of methods. *IJMTM* 40:1073–1098. https://doi.org/10.1016/S0890-6955(99)00122-4
- [B9] Zhou Y., Xue W. (2018). Review of tool condition monitoring methods in milling processes. *IJAMT* 96:2509–2523. https://doi.org/10.1007/s00170-018-1768-5
- [B10] Altintas Y. (1992). Prediction of cutting forces and tool breakage in milling from feed drive current measurements. *J. Eng. Ind.* 114:386–392. https://doi.org/10.1115/1.2900688
- [B11] Ammouri A.H., Hamade R.F. (2014). Current rise criterion: a process-independent method for tool-condition monitoring and prognostics. *IJAMT* 72:509–519. https://doi.org/10.1007/s00170-014-5679-9
- [B12] Drouillet C. et al. (2016). Tool life predictions in milling using spindle power with the neural network technique. *J. Manuf. Processes* 22:161–168. https://doi.org/10.1016/j.jmapro.2016.03.010
- [B13] Nouri M. et al. (2015). Real-time tool wear monitoring in milling using a cutting condition independent method. *IJMTM* 89:1–13. https://doi.org/10.1016/j.ijmachtools.2014.10.011 (normalising force-model coefficients so the wear signal does not depend on cutting conditions; the idea behind our "per MRR" features)
- [B14] Antoni J. (2006). The spectral kurtosis: a useful tool for characterising non-stationary signals. *Mech. Syst. Signal Process.* 20:282–307. https://doi.org/10.1016/j.ymssp.2004.09.001
- [B15] ISO 8688-2:1989, Tool life testing in milling — Part 2: End milling. https://www.iso.org/standard/16092.html (paywalled; VB values given as commonly quoted, not read from the standard)
- [B17] Kalpakjian S., Schmid S.R. *Manufacturing Engineering and Technology* (Pearson): Taylor n ranges by tool material; specific-energy table (steels about 2–9 W·s/mm³). Textbook values, not re-checked online.
- [B18] Wikipedia, Tool wear: https://en.wikipedia.org/wiki/Tool_wear ; Milling cutter: https://en.wikipedia.org/wiki/Milling_cutter
- [B19] Wikipedia, Vector control (motor): https://en.wikipedia.org/wiki/Vector_control_(motor)
- [B20] Wikipedia, Deflection (engineering) (cantilever δ = FL³/3EI): https://en.wikipedia.org/wiki/Deflection_(engineering)
- [B21] Wang K., Wang A., Wu L., Xie G. (2024). Machine Tool Wear Prediction Technology Based on Multi-Sensor Information Fusion. *Sensors* 24:2652. https://doi.org/10.3390/s24082652 (three wear stages; vibration in each stage)
- [B22] Wei W. et al. (2021). Wear and Breakage Detection of Integral Spiral End Milling Cutters Based on Machine Vision. *Materials* 14:5690. https://doi.org/10.3390/ma14195690 ("crater wear, flank wear, edge chipping and tool tip breakage are the main failure forms of end mills")
- [B23] Taylor F.W. (1907). On the art of cutting metals. *Transactions of the ASME* 28:31–350.

Every DOI above was checked against Crossref on 27 Oct 2026. Web search ran out partway through this research. Two items therefore rest on textbook knowledge rather than a page we opened: the ISO 8688-2 VB values and the Kalpakjian n ranges. Both are flagged where used.

---

## Appendix A. How the [our data] numbers were produced

- Input: the user's partially downloaded `data/raw/raw_data.zip` (Figshare file 52969793). At the time it held 535 complete per-cycle CSV files, blocks P002–P023. That is every recorded cycle of Type-1 tools 2, 3, 4, 5, 6 and 8, and 123 of 124 cycles of tool 7. Files were read straight from the zip without unpacking it. Type-2 tools (blocks P026+, P036+, P108+) and the 160 mm-holder tools (P112, P114) were not yet available.
- Each CSV has 22 columns: vibration timestamps (ms), 8 accelerometers, current timestamps (ms), 12 currents. The current columns end early and are padded with blanks. Unit conversions as in [P1] (A3).
- Per cycle:
  - idle = 20th percentile of the 3-phase-mean spindle current while above 1 A; cutting = spindle current > idle + 0.3 A;
  - net spindle current, net charge (A·s), mean X/Y/Z currents during cutting;
  - on accelerometers: RMS in cutting and in air; Welch PSD (2¹⁴ points); √power within ±2 Hz of 53.33 Hz and 213.33 Hz; power at spindle orders 1–40 split into tooth orders (multiples of 4) and the rest; 2–12 kHz RMS; kurtosis.
- Trends: cycles sorted by CycleToFailure (true time order). Cycle-1 files excluded. Values normalised by each tool's first 10 % of life, then medians taken over life-fraction bins. Spearman correlation against elapsed cycles.
- Power check: predicted Pc = Q·kc (Kienzle, hm from C2) against the median net spindle current of the first six non-cycle-1 cuts of each tool. Result 0.42–0.52 A/kW, mean 0.47.
- Limits: 7 tools, one cutter type, one holder length. This is a sanity check of the physics, not a model result.
