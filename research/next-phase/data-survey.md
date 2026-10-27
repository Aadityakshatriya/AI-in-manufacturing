# Public datasets for milling-cutter remaining life: verified survey

Prepared 27 October 2026 for the ToolLife Policy project (predict when a CNC milling cutter will fail, then decide when to replace it).

Our current dataset, for reference: Piecuch & Żabiński 2025, *Scientific Data*, Figshare 10.6084/m9.figshare.28589216. Haas VF-1, 42CrMo4 steel, 14 end mills run until breakage, 968 cycles, 8 accelerometers at 25 kHz and 12 spindle/axis phase currents at 0.5 kHz. It is already in `data/raw/`.

## How this was checked

Every dataset below was checked against its landing page, its repository API, or the files themselves on 27 October 2026. Small files were downloaded and opened: the NASA `mill.mat` (15 MB), one LUH HDF5 run, the LUH, MSTW and QIT-CEMC label tables, and the HES-SO and MSTW zip directories, read through HTTP range requests. No file larger than about 200 MB was downloaded.

Each fact is tagged with where it came from:

- **[V]** I saw it in the API, the file listing or the data.
- **[P]** It is stated in the dataset paper or its documentation.
- **[U]** It comes from memory or a secondary source, and I could not confirm it.

The general web-search quota for this session ran out partway through. After that, the wider sweep used the repositories' own APIs (Zenodo, Figshare, Mendeley Data, GitHub, Hugging Face, Kaggle listings) and the dataset comparison tables printed in the 2025–2026 data papers. A further round of open web searching could still turn up a few more items.

---

## 1. The short answer

There are now five public milling datasets that do what ours does: several cutters run to the end of their life, wear or failure labels on every cut, and a spindle-load or vibration signal. All five can be downloaded today without asking anyone.

- **LUH Hannover** has 9 cutters run to a flank wear (VB) of about 150 µm on three different machines, with spindle torque from the machine controller.
- **MSTW EndMill** is a new 2026 Figshare upload. It has 25 cutters run to VB of about 300 µm, with spindle current, spindle vibration and table vibration recorded together.
- **NASA Ames milling** is small and old, but it has spindle motor current.
- **PHM 2010** has 3 labelled cutters with vibration. It is the standard benchmark.
- **MATWI** has 17 cutters run to failure with vibration. Its wear labels are noisy.

Two more datasets have real lifecycles but weaker labels: **HES-SO micro-milling** (6 cutters run until they broke, with spindle current, but no measured wear) and a **2026 production dataset from a VMC 650** (24 cutters run until the operator declared them failed, with spindle current, but very coarse sampling).

Answers to the specific questions:

- **PHM 2010 test cutters (c2, c3, c5).** Their wear labels were never released. The official download links are dead. A complete raw mirror exists on Kaggle.
- **The 2026 graph neural network paper.** Its data is not public ("available from the corresponding author upon reasonable request"). The same research group did, however, publish the MSTW EndMill dataset on Figshare in May 2026.
- **The Rzeszów 2023 "database".** It is the same 14-tool experiment as our 2025 dataset. It sat behind a password-protected web page, and the 2025 Figshare release replaces it.
- **MU-TCM.** It is not a run-to-failure dataset. The inserts were deliberately pre-worn to target VB levels. Its host server could not be reached from our network.
- **MSM 2026.** It is an anomaly-detection dataset with no wear progression, so it cannot be used for remaining-life prediction.

---

## 2. Ranked table

"Tools to end of life" counts tools whose recording runs from a new cutter to a stated end point. "Spindle load" means spindle current, power or torque.

### Tier 1: tools run to end of life, with labels and a spindle-load or vibration signal, downloadable now

| Rank | Dataset | Tools to end of life | End-of-life definition | Labels | Spindle load | Vibration | Size | Access |
|---|---|---|---|---|---|---|---|---|
| 1 | **LUH Hannover 2023** (Mendeley zpxs87bjt8) | 9 (on 3 machines) | VB ≈ 150 µm | VB per run. Measured about every 40 runs and linearly interpolated in between | Spindle torque, 500 Hz (controller) | None. Force at 25 kHz instead | 10.6 GB | Open, no login, CC BY 4.0 |
| 2 | **MSTW EndMill 2026** (Figshare 31801795) | 25 | VB ≈ 300 µm (final values 301–318 µm) | VB per run | Spindle current, 1 kHz (raw volts) | Spindle and table, 1 kHz | 13.1 GB zip (≈63 GB unpacked) | Open, no login, CC BY 4.0. Machine, material and cutter are not documented |
| 3 | **NASA Ames milling** (PCoE S3) | 15 usable of 16 cases | Not stated. VB 0.3 mm is the usual choice, and 15 cases cross it | VB after most runs (20 of 167 missing) | Spindle motor current (AC and DC), 250 Hz | RMS-processed only, 250 Hz | 15 MB | Open, no login, US government work |
| 4 | **PHM 2010** (Kaggle mirror) | 3 labelled (c1, c4, c6) | Maximum flute wear; challenge range 66–165 µm | VB per flute per cut | None | Triaxial, 50 kHz (plus force, AE) | 6.8 GB (18.7 GB unpacked) | Free Kaggle login. Official links are dead |
| 5 | **MATWI** (KU Leuven RDR) | 17 | "Ran to failure"; no numeric criterion | Expert wear in 15 µm steps, per measurement | None | One accelerometer, about 1.6 kHz (plus force, microphone) | 19.05 GB | Open, no login, CC BY-SA 4.0. Labels are noisy |
| 6 | **NUAA Ideahouse** (IEEE DataPort) | 13 pocket tools (W1–W13) | VBmax = 0.3 mm | VBmax per edge, once per pocket layer | Spindle current and power, 300 Hz | 400 Hz | 125 MB | Free IEEE account needed. CC BY 4.0. Whether every tool reached 0.3 mm is unverified |
| 7 | **HES-SO micro-milling** (Zenodo 6505073) | 6 | Tool broke or became unusable | None measured. Life fraction comes from position in the run | Spindle and 5 axis currents, 1 kHz nominal | 8 accelerometers, 2 kHz (plus AE at 100 kHz) | 14.1 GB | Open, but **no license stated** |
| 8 | **VMC 650 production, low-cost DAQ** (Zenodo 21608174) | 24 | Operator-declared failure | Linear time-based remaining life, 0 to 1 | Clamp-on current transformer (A), burst-sampled | MPU6050 IMU, burst-sampled | 34 MB | Open, CC BY 4.0. Signals are very coarse |
| (—) | **SDU-QIT** (Qilu/Shandong) | 6 | VB at ap/2 = 0.3 mm | VB per edge per cut | None | Triaxial, 10 kHz | Unknown | Baidu Netdisk only (needs a Baidu account). Tier 1 content, but not practically downloadable |

### Tier 2: useful for pretraining or external testing only

| Dataset | Why it is only Tier 2 |
|---|---|
| **QIT-CEMC 2024** (Figshare 27323346) | One tool, 68 cycles, no end-of-life criterion, noisy non-monotonic VB. Force, torque, vibration and sound at 10 kHz. 11.7 GB |
| **MU-TCM 2025** (Mondragon eBiltegia) | Single-insert face mill pre-worn to VB 0, 0.1, 0.2 and 0.3 mm, giving 32 experiments in short steps rather than lifecycles. Very rich CNC signals (spindle power, current and torque at 250 Hz) plus force, vibration and AE. Host unreachable from our network |
| **HMoTP** (Shandong, GitHub/Google Drive) | 3 tools × 100 cuts, force, torque and acceleration, wear per flute per cut. No license on the data |
| **Mudestreda / Nonastreda** (Zenodo 8238653 / Mendeley m892d2wtzh) | 10 tools with 10–15 rides each, run until destroyed or sparking. Force only (Nonastreda adds raw 1 kHz forces and numeric flank wear). The two datasets hold the same 512 samples |
| **KIT multimodal milling** (RADAR4KIT) | Anomaly dataset. The only wear content is one tool over 6 passes, labelled by cutting time. Excellent 500 Hz spindle current, torque and power, useful for learning load features. 44.6 GB |
| **Aqifi desktop-CNC vibration 2026** (Zenodo 21845441) | 3 tools in aluminium, not run to failure, no per-block wear labels. Vibration at 64 kHz |
| **Vicomtech turning** (GitHub) | Secondary: turning, not milling. 13 tools with per-segment wear, but features only (including spindle current, power and torque) |
| **Drilling tool wear** (Mendeley th4yv974r2) | Secondary: drilling. 4 drills run from new to blunt, 1 kHz accelerometer, no numeric wear |
| **UMich CNC Mill Tool Wear** (Kaggle) | Wax workpiece, per-experiment worn/unworn label, controller spindle power at 10 Hz. Pretraining for load features at most |

### Unusable for remaining-life prediction

| Dataset | Reason |
|---|---|
| **GNN paper data** (Discover Applied Sciences 2026, 10.1007/s42452-026-08390-x) | Not public: "available from the corresponding author upon reasonable request". See §6.6 |
| **Rzeszów 2023 database** (Sensors 23:9346) | The same 14 tools as our 2025 dataset. The old site's data page is password-protected. Superseded by Figshare 28589216 |
| **MSM 2026** (Kaggle, Sci Data s41597-026-07255-7) | Anomaly labels (normal, abnormal, tool defect) and no wear progression |
| **Bosch CNC_Machining** | Good/bad process labels only. Vibration at 2 kHz |
| **Hugging Face AI4Manufacturing/PHM2010** | Gated (manual approval), a 46 MB image/text derivative, placeholder card, no license |
| **Fraunhofer Fordatis 480** | One sharp and one worn recording |
| **TUGMCL_BasicMilling** (Zenodo 7753181) | No wear labels |
| **Trochoidal milling force/power 2026** (Zenodo 23688554) | No wear labels |
| **Sheffield ORDA 24125715**, **JUST_CAS_milling** (Mendeley 8jk3kyxmbn), Kaggle `ziya07/*` (synthetic), single-value tabular sets | No wear progression, no labels, or synthetic data |

---

## 3. Recommended downloads, in order

1. **LUH Hannover** (10.6 GB, no login). This is the closest match to our problem: real lifecycles, a spindle-load channel (spindle torque) and three different machines. Our weakest point is generalising to a new machine, and this dataset lets us test exactly that. Download `filelist.csv` first (240 KB) and fetch the runs through the Mendeley API.
2. **NASA Ames milling** (15 MB). It is already sitting in the scratchpad from this survey, so getting it costs nothing. It gives a second, older spindle-current dataset on a different tool type (a 70 mm face mill with 6 inserts).
3. **MSTW EndMill** (13.1 GB zip, no login). It has the most lifecycles of any public set (25) with spindle current and vibration together. The zip unpacks to about 63 GB, so features can be extracted file by file using range reads rather than unpacking it all. Before relying on it, ask the authors for the machine, workpiece, cutter and units (see §5).
4. **PHM 2010, c1, c4 and c6** from the Kaggle mirror `rabahba/phm-data-challenge-2010` (6.8 GB, free Kaggle login). Use it as the standard vibration benchmark that reviewers will expect to see. It has no spindle load.
5. **Optional extras:**
   - **HES-SO** `toolwear_2020_axes.zip` (1.7 GB) and `toolwear_2020_acc.zip` (1.15 GB). Skip the 11.2 GB AE file. These give breakage-defined lifecycles with spindle current, which is the same end-of-life definition as ours.
   - **The VMC 650 production set** (34 MB). It is a cheap source of 24 real production tool lifetimes, useful for testing the replacement policy rather than the signal model.
   - **MATWI** (19 GB), as a vibration-only external test set.
   - **NUAA** (125 MB, free IEEE login), as a spindle-current test set on titanium.

Disk needed for items 1–4: about 31 GB as downloaded, or about 80 GB if MSTW is fully unpacked.

---

## 4. Putting the datasets on a common basis with ours

### 4.1 Common target: fraction of life used

For every cut *k* of a tool, define

> φ(k) = (cumulative cutting time at the end of cut k) ÷ (cumulative cutting time at end of life), with remaining-life fraction = 1 − φ(k).

When cutting time is not available, cut count is used instead. This is the same idea as our `CycleToFailureNormalized` column, but measured on a time axis rather than in cycles.

End of life is defined per dataset:

| Dataset | End of life | How it is applied |
|---|---|---|
| Ours, HES-SO, VMC 650 | Breakage, or operator-declared failure | The last cut is end of life |
| LUH | VB = 150 µm (mean of 4 edges) | First interpolated crossing |
| PHM 2010 | Maximum flute wear = 165 µm (top of the challenge's 66–165 µm range) | c1, c4 and c6 all go beyond this; c4 ends at about 196–211 µm |
| NASA | VB = 0.3 mm | Linearly interpolate VB over the `time` field. 15 of 16 cases cross it; drop case 6, which has a single run |
| NUAA, SDU-QIT | 0.3 mm (VBmax; VB at ap/2 for SDU-QIT) | Stated in the documentation and paper |
| MSTW | ≈300 µm | The last run of each case is end of life (final VB 301–318 µm) |
| MATWI | No criterion stated | Use the last measurement, or a chosen threshold, and report sensitivity to that choice |

**Caveat.** A wear threshold is a human policy choice, while breakage is a physical event. φ makes the two kinds of dataset look alike, but the spread of lifetimes and the behaviour close to end of life differ between them. The other datasets are best used to learn signal features and to check that the features rise steadily with φ. The final replace-or-continue decision should still be calibrated on our breakage data, and on HES-SO and VMC 650 if they are added.

### 4.2 Common time axis: material removed

Material removed is the cleanest physical clock, but only some datasets give enough cutting parameters to compute it. The volume removed in a cut is ap × ae × path length, or equivalently MRR × engaged time, where MRR = ap × ae × vf.

| Dataset | Computable? | How |
|---|---|---|
| Ours | Yes | Sensors 2023 Table 1 gives the total volume for each tool. That works out to about 8–16 cm³ per cycle at RDOC 4.5 mm and 15–29 cm³ per cycle at RDOC 8 mm. Whole-tool totals range from 0.22 to 2.0 million mm³ |
| LUH | Yes | Cumulated contact time C is in every file name. ap = 2 mm [P]; ae = 4 mm and vf = 1,592 mm/min come from the MU-TCM comparison table [U]. That gives MRR ≈ 212 mm³/s and about 0.7–1.1 million mm³ per tool life, the same order as ours |
| PHM 2010 | Roughly | ap 0.2 mm × ae 0.125 mm × an assumed 108 mm per cut [U] gives about 2.7 mm³ per cut, which is roughly 1,000 times smaller than ours |
| NASA | No | ae is not given (face mill on a 178 mm-wide block). Use the `time` field as cutting time |
| MSTW | No | ae is not given and the feed units are unclear. Use cutting time (about 600 s per run) |
| NUAA | Partly | ap and fz are known, but ae varies along the pocket path |
| HES-SO, VMC 650 | No | Use cutting time (pass durations, or rows with current above 0.5 A) |

**Recommendation.** Use cumulative engaged cutting time as the shared clock and material removed as a second axis wherever it can be computed. Always express the target as φ. Absolute volumes differ by up to three orders of magnitude between datasets (PHM 2010 against ours), so absolute remaining-life numbers cannot be pooled across datasets. Normalised ones can.

### 4.3 Common "spindle load" channel

For each cut, compute the **relative spindle load**:

> L_rel(k) = (L_cut(k) − L_idle) ÷ median over the first 10% of the tool's life of (L_cut − L_idle)

L_cut is the mean load during engagement. L_idle is the spindle running without cutting (an air cut or rapid move). Where no idle segment exists, use the lowest 5th percentile of the cut. Dividing by each tool's own early-life value removes units, sensor gain and machine size, so a value of 1.3 means 30% more load than when the tool was fresh.

| Dataset | Source channel | Preprocessing |
|---|---|---|
| Ours | Spindle phase currents L1–L3, 0.5 kHz | True RMS per phase over the cut, averaged across the three phases |
| LUH | `signals_machine/torque_spindle` (Nm), 500 Hz | Mean over the run. Machine M2 aliases this channel, so use means rather than spectra |
| NASA | `smcDC` (and `smcAC`), 250 Hz, 9,000 samples per run | Mean over the steady middle of the run |
| MSTW | `Current` (V), 1 kHz. It looks like the raw AC waveform [V] | RMS over 20 ms windows, then the mean |
| NUAA | Spindle current and power from the controller, 300 Hz | Mean per layer file |
| HES-SO | `stSig…Spindle…` and axis current CSVs (one per day, Windows FILETIME timestamps, 0.5 ms steps, stored newest-first) | Cut into passes using the acc/AE file timestamps, then take the mean |
| VMC 650 | `Current_A` | Keep rows with current above 0.5 A only |
| MU-TCM, KIT | Spindle power, current and torque, 250 Hz and 500 Hz | Mean |
| Force-only sets (PHM 2010, MATWI, HMoTP, Nonastreda) | No spindle load | Proxy: mean in-plane resultant force √(Fx² + Fy²), or the dynamometer torque Mz where one exists (QIT-CEMC, HMoTP). Label it as a proxy |

Treat vibration the same way: band RMS per cut in a few fixed bands (for example 0–500 Hz, 0.5–2 kHz and 2–8 kHz, capped at each dataset's Nyquist frequency), each normalised by the same tool's first 10% of life. Many of the public sets sample slowly (NASA at 250 Hz RMS, NUAA at 400 Hz, MSTW at 1 kHz). Our 25 kHz vibration should therefore be low-pass filtered and decimated when training jointly, otherwise the model learns features the other datasets cannot supply.

---

## 5. What needs you

1. **Kaggle login (free).** Needed to download the PHM 2010 raw mirror (`rabahba/phm-data-challenge-2010`, 6.8 GB). Its uploader marked it CC0, but that marking is not authoritative.
2. **IEEE DataPort account (free).** NUAA Ideahouse is open access, but the file download needs a login.
3. **Baidu Netdisk account.** This is the only route to SDU-QIT (link `https://pan.baidu.com/s/1BmKaKhedU7QKB3t9TzThOw`, extraction code `rw97`, published on `https://www.qlit.edu.cn/datasets/`). It is optional. QIT-CEMC does not need Baidu because Figshare hosts it directly.
4. **Author emails.** I have not drafted or sent any of these.
   - **Satish Kumar / Sameer Sayyad / Arunkumar Bongale (Symbiosis).** Ask for the MSTW EndMill metadata (machine, workpiece material, cutter diameter, flutes and coating, feed units, sensor calibration, and what one 600 s "run" contains). Also ask whether the 120-run data in their 2026 GNN paper is a subset of MSTW, or whether it can be shared.
   - **MU-TCM (mcuesta@mondragon.edu).** `ebiltegia.mondragon.edu` and `www.mondragon.edu` both timed out from this network on 27 October. Either retry from another network (for example the IITM campus or a VPN), or ask the authors for a link.
   - **HES-SO (Dreyer, Carrino, Ghorbel).** The Zenodo record has no license. Ask for one before redistributing anything derived from it.
5. **Hugging Face AI4Manufacturing/PHM2010** needs manual approval. Not recommended, because it is a processed image/text derivative.

---

## 6. Dataset details

### 6.1 LUH Hannover 2023 (Denkena, Klemme, Stiehl): Tier 1, rank 1

| Field | Value |
|---|---|
| Download | Landing page `https://data.mendeley.com/datasets/zpxs87bjt8` (version 3). API: `https://data.mendeley.com/public-api/datasets/zpxs87bjt8` returns HTTP 200 and lists every file with a direct `download_url`, e.g. `https://data.mendeley.com/public-files/datasets/zpxs87bjt8/files/01d97477-db7e-480d-b448-1e6c3fc8fe08/file_downloaded` for `filelist.csv` [V] |
| Paper | Data in Brief 50:109574 (2023), doi 10.1016/j.dib.2023.109574, PMC10558710 |
| License | CC BY 4.0 [V, Mendeley `data_licence`] |
| Size | 10.62 GB: 6,418 `.h5` files of 1.49–1.70 MB each, plus `filelist.csv` [V] |
| Tools | 9 solid-carbide end mills from two batches (T1–T3 and T7–T9 batch A, T4–T6 batch B), 3 per machine [P] |
| Runs per tool | 609, 609, 638 (M1: T1–T3); 928, 928, 928 (M2: T4–T6); 609, 560, 609 (M3: T7–T9) [V] |
| End of life | Worn from new to VB ≈ 150 µm. Final VB per tool is 145–160 µm [V] |
| Labels | VB in µm in each file name and in `filelist.csv`. Measured on all 4 edges with a Keyence VHX600 at 100×, averaged, uncertainty about 5 µm. Measured after each layer early and late in life and every second layer in the middle, about every 40 runs. Every other run is **linearly interpolated over contact time** [P]. Tools have 104–142 distinct VB values each [V] |
| Signals | Kistler 9257B table dynamometer, Fx/Fy/Fz at 25 kHz (110,250 samples ≈ 4.41 s per run) [V]. Controller at 500 Hz (2,205 samples per run): `torque_spindle` (Nm), `torque_axis_x/y/z`, `tool_position_x/y/z`, `position_control_deviation_axis_x/y` [V]. Machines M2 and M3 log `force_axis` instead of axis torque [P]. **Spindle load: yes (spindle torque).** **Vibration: none** |
| Machines | M1 DMG Mori Milltap 700 (Sinumerik 840D sl, 4 kW); M2 DMG Mori HSC 30 linear (Sinumerik, 15 kW); M3 DMG Mori HSC 55 linear (Heidenhain iTNC 530, 55 kW) [P] |
| Workpiece | Cast iron 600-3/S (ISO 1083), a single material batch [P] |
| Cutter | Solid carbide, 4 edges, TiN-TiAlN coating. Diameter is only shown in a figure [P]; 10 mm is inferred from vc and feed [U] |
| Cutting parameters | 3-axis shoulder milling, ap = 2 mm [P]. vc = 200 m/min, vf = 1,592 mm/min and ae = 4 mm per the MU-TCM comparison table [U]. Identical on all machines [P] |
| Segmentation | One file per run: tool entry, straight path, exit, cut using feed velocity. The first and last run of each layer, runs crossing mounting holes, and corrupted runs were dropped and the rest renumbered [P] |
| Known problems | M2's control filter was off, so `torque_spindle` and `force_axis` alias. On M3 (T7, T8) the workpiece frame is rotated 1–2°. T8 is missing its early runs (its first file is at C = 177 s, VB 34 µm) [V]. The force and controller clocks are aligned only to about 100 ms. The paper's Table 2 lists `force_axis_x` three times [P] |
| Access | No login |

### 6.2 MSTW EndMill 2026 (Sayyad, Kumar, Bongale): Tier 1, rank 2 (new find)

| Field | Value |
|---|---|
| Download | `https://figshare.com/articles/dataset/_b_Multi-Sensor_Tool_Wear_End_Milling_MSTW_EndMill_Dataset_b_/31801795`, DOI 10.6084/m9.figshare.31801795.v2, published 20 May 2026 [V]. Files: `https://ndownloader.figshare.com/files/64734885` (`Sensor_Data_DAQ_updated.zip`, 13,095,061,412 B) and `https://ndownloader.figshare.com/files/62917744` (`Tool_Wear_Value_Table.xlsx`, 14.9 KB) [V]. The zip download redirects to S3 and accepts range requests [V] |
| License | CC BY 4.0 [V] |
| Size | 13.1 GB zip. 822 CSVs of about 76.7 MB each, so about 63 GB unpacked [V] |
| Tools | 25 "cases", one tool per cutting-parameter combination, folders named like `1_S800_F20_D0.10` (a 5×5 design over speed 800–1200, feed 20–40, depth 0.10–0.30) [V] |
| Runs per tool | 24–39 recordings, 822 in total. The wear table has 824 rows; case 6 has 30 recordings against 33 wear rows, and case 25 has 36 against 35 [V] |
| End of life | Every case ends at VB ≈ 300 µm (final 300.7–318.2 µm) [V] |
| Labels | Flank wear in µm, one value per run. First values are 31–60 µm. Cases 1, 5, 6 and 24 are slightly non-monotonic [V] |
| Signals | One CSV per run with columns `Time, Vib_Spindle, Vib_Table, X_Load_Cell, Y_Load_Cell, Z_Load_Cell, Current`. All in raw volts, 1 kHz (Δt = 0.001 s), about 601 s per run [V]. `Current` swings between about 0.8 and 2.3 V over roughly 20 ms, which looks like the raw AC waveform, so take RMS [V]. **Spindle load: yes (current). Vibration: yes (spindle and table)** |
| Machine, workpiece, cutter | **Not documented.** The record description holds only the title, and there is no README [V]. The 5×5 speed/feed/depth design matches this group's earlier Taguchi L25 tool-wear work [U] |
| Known problems | No metadata, units or calibration. A 1 kHz rate limits vibration analysis. The recording-to-wear mismatch in cases 6 and 25 needs resolving |
| Access | No login |

### 6.3 NASA Ames milling (Agogino & Goebel): Tier 1, rank 3

| Field | Value |
|---|---|
| Download | `https://phm-datasets.s3.amazonaws.com/NASA/3.+Milling.zip` returns HTTP 200, 14,731,306 B, last modified 18 September 2022 [V]. Listed on the NASA PCoE repository page (`https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/`) [V]. The old `data.nasa.gov` and `ti.arc.nasa.gov` links redirect to that page. The zip contains `mill.zip`, which holds `mill.mat` (72.6 MB) and `Readme.pdf` [V] |
| License | No license file. It is a US government work, cited as "NASA Prognostics Data Repository" [V] |
| Size | 15 MB zipped, 73 MB unpacked [V] |
| Tools | 16 cases: 8 conditions × 2 insert sets [P]. Each case is one insert set over its life |
| Runs per case | 17, 14, 14, 7, 6, 1, 8, 6, 9, 10, 23, 15, 15, 9, 7, 6 (167 in total) [V] |
| End of life | No explicit criterion: runs went "up to a wear limit (and sometimes beyond)" [P]. Final VB ranges from 0.44 to 1.53 mm. 15 of 16 cases cross 0.3 mm; case 6 has a single run [V] |
| Labels | VB in mm after runs, irregular, with 20 of 167 missing (NaN) [V] |
| Signals | `smcAC` and `smcDC` spindle motor current, `vib_table`, `vib_spindle`, `AE_table`, `AE_spindle`. All at 250 Hz, 9,000 samples per run (36 s; case 12 has 15,360) [V]. Vibration and AE went through a hardware RMS with an 8 ms time constant; vibration was band-passed 400 Hz – 1 kHz [P]. **Spindle load: yes (current). Vibration: RMS only** |
| Machine | Matsuura MC-510V [P] |
| Workpiece | Material 1 = cast iron, material 2 = stainless steel J45. Block 483 × 178 × 51 mm [P] |
| Cutter | 70 mm face mill with 6 KC710 inserts (TiC/TiC-N/TiN multilayer coating) [P] |
| Cutting parameters | vc 200 m/min (826 rpm). ap 0.75 or 1.5 mm. Feed 0.25 or 0.5 mm/rev (206.5 or 413 mm/min). ae not stated [P] |
| Segmentation | One struct entry per run, including entry and exit cut. `time` is cumulative cutting duration within a case [V/P] |
| Known problems | Sparse and missing VB. Only RMS-processed vibration and AE. Case 6 is unusable. Low sampling rate. Materials differ between cases |
| Access | No login. Kaggle copies exist (`vinayak123tyagi/milling-data-set-prognostic-data`, `s3programmerlead/nasa-milling-dataset`), but the S3 link is the official one |

### 6.4 PHM Society 2010 data challenge: Tier 1, rank 4

| Field | Value |
|---|---|
| Official download | `https://phmsociety.org/phm_competition/2010-phm-society-conference-data-challenge/` lists `http://cdn.teamholistic.net/phmconference.org/c1.zip` … `c6.zip`. **All six are dead**: they redirect (302) to the CDN root, which returns 405 [V]. NASA PCoE item 19 points to the same page [V] |
| Working mirrors | Kaggle `rabahba/phm-data-challenge-2010` is the only complete raw c1–c6 copy found: 6.8 GB download, 18.73 GB unpacked, 1,893 files (6 × 315 cuts plus 3 wear CSVs) [V]. Kaggle `tobbyrui/phm2010` has raw c1, c4 and c6 only (3.5 GB) [V]. GitHub `qingluM/CDAR` has reduced `.npy` copies of c4 and c6 (313 × 20,000) plus wear CSVs [V]. IEEE DataPort 10.21227/jdxd-yy51 needs a subscription and says "Files have not been uploaded" [V]. HF `AI4Manufacturing/PHM2010` is a gated 46 MB image/text derivative [V] |
| License | None stated officially. The Kaggle mirror says CC0 (uploader's own marking) |
| Tools | 6 cutters. Only **c1, c4 and c6 have wear files** [P, V] |
| Cuts per tool | 315 [V, from the c4 wear file and the mirror's file count] |
| End of life | No breakage. Scoring asked for the "maximum safe cut" at each integer wear limit from 66 to 165 µm, with the most-worn flute deciding [P, scoring page]. c4 reaches 196–211 µm at cut 315 [V] |
| Labels | `cut, flute_1, flute_2, flute_3` wear in 10⁻³ mm after every cut [V]. Values carry many decimals. Li et al. (2009) say each cut was measured with a microscope [U] |
| Signals | Fx, Fy, Fz (N), vibration X/Y/Z (g), AE-RMS (V), all at 50 kHz per channel [P]. **Spindle load: none. Vibration: yes** |
| Machine | High-speed CNC (Röders Tech RFM760 per Li et al. 2009) [U] |
| Workpiece | **Sources conflict.** Stainless steel HRC52 per Li et al. 2009 and the MU-TCM table [U]; Inconel 718 per the QIT-CEMC table [U] |
| Cutter | 6 mm ball-nose tungsten carbide [P]. 3 flutes (from the wear-file columns) [V] |
| Cutting parameters | 10,400 rpm, 1,555 mm/min, radial depth 0.125 mm, axial depth 0.2 mm [P] |
| Segmentation | One CSV per cut (one surface pass) |
| **c2, c3, c5 labels** | **Never publicly released.** The evidence: (1) the official page and the IEEE DataPort description list wear files only for the training cutters c1, c4 and c6; (2) the official page warns that a c3.zip containing a wear file "is incorrect. Please discard it"; (3) the scoring page never mentions releasing test ground truth; (4) none of the mirrors listed above claims c2/c3/c5 labels, and a GitHub search for `c2_wear.csv`, `c3_wear.csv` and `c5_wear.csv` returned nothing. Treat c2, c3 and c5 as unlabelled. They are usable for self-supervised pretraining only |

### 6.5 QIT-CEMC 2024 (Li et al., Qilu Institute of Technology): Tier 2

| Field | Value |
|---|---|
| Download | Figshare `https://doi.org/10.6084/m9.figshare.27323346` (v3): `https://ndownloader.figshare.com/files/50069727` (`Milling dataset from QIT.rar`, 11,710,022,704 B) and `mill_data_processing.py` [V]. GitHub `https://github.com/wwz456/QIT-CEMC-dataset` holds the README, `tool_wear.csv` and figures (MIT license) [V]. Baidu link with code `jm7f` as an alternative [V] |
| License | Figshare: CC BY 4.0 [V]. The article itself is CC BY-NC-ND 4.0 [V] |
| Paper | Sci Data 12:16 (2025), s41597-024-04345-2 |
| Tools | **1** four-flute TiAlN-coated carbide end mill (YG3X, 10 mm, 55° helix) [P, V] |
| Runs | 68 machining cycles of about 5 million rows each (10 kHz, so about 500 s per cycle) [P] |
| End of life | No criterion. Mean VBmax over the 4 edges rises from 0.04 to about 0.43 mm, and edge 1 reaches 0.70 mm [V] |
| Labels | Per cycle, per edge: side-edge VBmax, VB at ap/2 and wear area S, plus end-teeth VBmax and S [V]. Noisy and non-monotonic (mean VBmax 0.278 at cycle 41, 0.224 at cycle 49) [V] |
| Signals | Kistler 9170B251 rotating dynamometer: Fx, Fy, Fz and **torque Mz** at 10 kHz. DH5922D triaxial vibration plus sound at 10 kHz [P]. **Spindle load: tool-holder torque (a proxy). Vibration: yes** |
| Machine, workpiece | VDF-850 vertical machining centre. Ti6Al4V bar, Ø113 × 400 mm, circular tool path [P] |
| Cutting parameters | 1,430 rpm (vc 44.8 m/min), 130 mm/min, fz 0.0227 mm. The paper contradicts itself on depths: Table 3 gives "milling depth 8 mm, width 0.2 mm", while Table 2 gives "cutting width 8" [P] |
| Known problems | Vibration for cycle 2 is lost. GMM-based removal of invalid segments plus a moving-average baseline correction was used. Only one tool, so it cannot be split by tool |

### 6.6 GNN remaining-life paper (Discover Applied Sciences 8:480, 2026): unusable, data not public

- **Identity.** "Graph neural network-based remaining useful life prediction of milling tools using multi-sensor data", doi 10.1007/s42452-026-08390-x, published 9 March 2026 [V, Crossref]. Authors: Satish Kumar, Dhruvi Ramaiya, Sameer Sayyad, Arunkumar Bongale, Vivek Warke and Vaibhav Joshi (Symbiosis Institute of Technology, Pune) [V].
- **Data availability, near-verbatim.** "The datasets used and analyzed during the current study are available from the corresponding author upon reasonable request. Due to confidentiality agreements and institutional policies, access to certain data may be restricted…" No code link is given. Only a Docker setup is mentioned [P].
- **Data described.** 120 machining runs (the text also mentions "nine different milling tests"). Vibration X/Y/Z, spindle current/load and a 3-component dynamometer, at 25 kHz through an NI DAQ. Jyoti VMC. D3 tool-steel workpiece, 200 × 100 × 50 mm. Coated carbide insert end mill. Flank wear by toolmaker's microscope, with an end of life of 0.30 mm [P].
- **Does it reuse a known dataset?** No. Its 26 references cite no public dataset (PHM 2010, NASA and others are absent) [V, Crossref reference list]. It is in-house data.
- **Closest public substitute.** Three of its authors (Sayyad, Kumar, Bongale) published **MSTW EndMill** on Figshare in May 2026 (§6.2). MSTW does not match the paper's description (25 cases, 822 runs, 1 kHz versus 120 runs at 25 kHz), so it is not the same release [V]. Whether the paper's 120 runs are a subset of the same rig is unknown; ask the authors (§5).
- **ResearchGate 401787141.** Not checked; ResearchGate needs a login and would not change the availability statement.

### 6.7 Rzeszów Sensors 2023 database (Paszkiewicz, Piecuch, Żabiński et al.): superseded

- **Paper.** "Estimation of Tool Life in the Milling Process — Testing Regression Models", Sensors 23(23):9346, PMC10708711 [V].
- **Data availability statement.** "The data and photos are available publicly and free of charge on the website: https://datasets.kia.prz.edu.pl/" [V].
- **What is there now.** The site (it redirects to `haas.kia.prz.edu.pl`, a WordPress site in Polish) has description pages that are open: the test stand, the data description and the usage rules. The **data page ("Dane", `?page_id=115`) is password-protected** ("Treść jest chroniona hasłem") [V].
- **Comparison with our 2025 dataset.**
  - Same rig: Haas VF-1, Beckhoff C6920, 8 Dytran accelerometers, 12 Wago current transformers.
  - Same material and sample geometry: 42CrMo4, 80 × 80 × 150 mm.
  - Same process: 3,200 rpm, 640 mm/min, ADOC 5/10 mm, RDOC 4.5/8 mm, 25 kHz vibration and 0.5 kHz current.
  - Same 14 tool IDs (2–11, 101, 102, 103, 105).
  - **Identical cycle-to-failure counts per tool**: 49, 49, 40, 53, 29, 126, 115, 149, 14, 0, 83, 84, 59, 124 [V, Sensors Table 1 against Sci Data Table 4].
  - The metadata columns described on the site (cycles to failure, absolute and normalised) are the same as in the 2025 release [V].
- **Conclusion.** It is the same experiment, published earlier behind a password. The 2025 Figshare release is the public, citable version, and nothing extra is gained by chasing the 2023 site.
- **Small inconsistency to check in our own pipeline.** The per-tool `CycleToFailure` values sum to 974 (or 988 if the failure cycle is counted separately), while the 2025 paper says 968 cycles were recorded. Some cycles may be missing from the raw files.
- **Other host.** Kaggle `grzegorzpiecuch/cnc-milling` (26.2 GB, CC BY 4.0) is the same author's upload [V, listing only].

### 6.8 MU-TCM 2025 (Peralta Abadia et al., Mondragon): Tier 2

| Field | Value |
|---|---|
| Download | DOI `https://doi.org/10.48764/3hdp-gf23` → `https://hdl.handle.net/20.500.11984/6926` → `https://ebiltegia.mondragon.edu/xmlui/handle/20.500.11984/6926` [V, redirects]. **The host timed out from this network (curl) and refused the connection (WebFetch) on 27 October 2026**; `www.mondragon.edu` also timed out [V]. A subset (experiments 13–20) is offered separately for evaluation [P]. Code: `https://github.com/spartanjoax/MU-TCM`, Zenodo 10.5281/zenodo.14055658 (AGPL-3.0) [V] |
| License | CC BY 4.0 [V, DataCite] |
| Size | Not known: the host was unreachable and DataCite gives no size [V] |
| Tools | 9 cutting inserts, each a single Ayma SPKR 1203EDSR AFT720 insert in an 80 mm face mill. The same insert and edge are reused across conditions and materials [P] |
| Experiments | 32 conditions × about 2 repetitions = 67 recordings. Cut times are 4.5–18 s each [P] |
| End of life | **Not run to failure.** Inserts were pre-worn by roughing to target VB 0, 0.1, 0.2 and 0.3 mm (ISO 8688 limit 0.3 mm) [P] |
| Labels | VB measured before each experiment (Leica Z16 APO, 3 decimals) with images [P] |
| Signals | External: Kistler 9139AA force and PCB J356A45 triaxial accelerometer at 50 kHz; Kistler 8152C AE at 1 MHz. Internal (Fagor 8065, 250 Hz): SREAL, FREAL, POS_S, POS_X/Y/Z, **TV50 spindle power, TV51 active power, CV3_S/X/Y/Z RMS current, TV2_S/X/Y/Z motor torque** [P]. **Spindle load: yes (three kinds). Vibration: yes** |
| Machine | LAGUN L1000 with Fagor CNC 8065 [P] |
| Workpiece | 316L stainless steel (MQL) and GG30 cast iron (dry), blocks 200 × 292.5 × 50 mm [P] |
| Cutting parameters | vc 50/100 m/min (stainless) and 100/200 m/min (cast iron). f 0.05/0.1 and 0.1/0.2 mm/rev. ap 1.5 mm. ae 58.4 mm (the text also says 58.5) [P] |
| Known problems | Internal and external signals were synchronised by hand. Four first repetitions lack external signals. Actual VB deviates from the targets. Inserts were reused across conditions |

### 6.9 NUAA Ideahouse (Li, Liu, Li, Hua, Wan; NUAA): Tier 1, rank 6 (login)

- **Download.** `https://ieee-dataport.org/open-access/tool-wear-dataset-nuaaideahouse`, DOI 10.21227/3aa1-5e83 [V]. One zip, `Tool wear dataset of NUAA_Ideahouse.zip`, 125.22 MB. Open access, but the file download needs a free IEEE account. The documentation PDF downloads without a login [V].
- **License.** CC BY 4.0 (DataCite), though the page also says copyright is reserved by NUAA [V, sub-agent]. Cite Liu et al., IEEE TII 2021 [U].
- **Design** [P, documentation PDF]:
  - 60 sidewall runs on fresh tools "with the same wear state". These are parameter sweeps: ap 1–20 mm, fz 0.021–0.040, n 820–1,200 rpm, ae 3 mm. They carry no wear progression.
  - 13 pocket experiments run to end of life. W1–W9 are an orthogonal design: fz 0.045/0.05/0.055 mm/tooth, n 1,750/1,800/1,850 rpm, ap 2.5/3/3.5 mm, all with 12 mm solid-carbide tools (12 × 75 × R1) on TC4. W10–W13 use a 16 mm tool, a 20 mm tool, an HSS tool, and a superalloy workpiece.
- **Labels.** VBmax per edge measured once per pocket layer with a Sinico XK-T600 (0.01 mm accuracy), one label per `n.csv`, with interpolation needed in between. **End of life: VBmax = 0.3 mm** [P].
- **Signals.** Spindle current and power from the controller at 300 Hz; PCB W356B11 vibration at 400 Hz; Spike sensory tool holder force at 600 Hz. The documentation also says everything is synchronised to 300 Hz [P]. Non-cutting segments are removed [P].
- **Machine.** DMU 80P duoBLOCK [P].
- **Unverified.** Whether every W-run actually reached 0.3 mm, and the per-tool cut counts, because the zip is behind the login.

### 6.10 MATWI (De Pauw, Jacobs, Goedemé; KU Leuven): Tier 1, rank 5

Verified by the sub-agent through the RDR API and partial reads.

- **Download.** DOI 10.48804/GK6LHH (HTTP 200 to `rdr.kuleuven.be`). Files come from `https://rdr.kuleuven.be/api/access/datafile/<id>` and redirect to signed S3. There are 20 files: `Set1.zip` to `Set17.zip` (0.57–1.97 GB each), `labels.csv` (548 KB) and `sets.csv`. 19.05 GB in total. No login.
- **License.** CC BY-SA 4.0.
- **Design.** Milling, 17 tools (one per set) run to failure. `labels.csv` has 1,803 rows, 51–214 per set. Each measurement pairs one microscope image with one sensor CSV.
- **Labels.** Expert wear in µm (15 µm steps) plus wear type (flank, adhesion or both).
- **Signals.** One accelerometer, one microphone, and Fx/Fy/Fz force at about 1.64 kHz (estimated from timestamps). No spindle load.
- **Cutter and workpiece.** 15 mm cutter with 1 edge (2 in Set 17). CK45 steel in sets 1–11, AISI 304 in sets 12–17.
- **Cutting parameters.** vc 120–174 m/min, fz 0.03–0.08 mm, ae 1 mm, ap 0.5–1 mm. Set 1's parameters are recorded as "?".
- **Known problems.** Wear labels drop near the end of several sets (Set 10 peaks at 270 µm but ends at 45; Set 11 peaks at 750 and ends at 240). Image and sensor pairs are missing in places (72 rows in Set 17 have no sensor file; 66 in Set 6 have no image).
- **Other copies.** Kaggle `quyentran1810/matwi-toolwear-dataset-set2` … `set11` [listing only].

### 6.11 HES-SO micro-milling (Dreyer, Carrino, Ghorbel): Tier 1, rank 7 (new find)

| Field | Value |
|---|---|
| Download | Zenodo `https://zenodo.org/records/6505073` (10.5281/zenodo.6505073, April 2022). Files: `toolwear_2020_axes.zip` (1.72 GB), `toolwear_2020_acc.zip` (1.15 GB), `toolwear_2020_ae.zip` (11.25 GB) [V] |
| License | **None stated** on the record [V] |
| Paper | Dreyer et al., "In production system for tool wear prediction using multi-sensor time series and machine learning models", Discover Applied Sciences 8:776 (2026), PMC13341891 [V]. The GitHub link in the record (`soon-project/MillingToolWear`) returns 404 [V] |
| Tools | 6 tool folders in the acc and AE zips: 1100_007, _009, _010, _011, _014, _015 [V]. The paper lists 14 parts: 2 tests and 3 with machining errors [P] |
| Passes per tool | 936–1,216 files per tool, one per linear pass [V] |
| End of life | "This block starts with a new tool and ends when the tool breaks or becomes unusable" [P] |
| Labels | **No measured wear.** The paper assigns 5 classes (0–4) by position in the tool's life [P]. Life fraction can be taken directly from the pass index |
| Signals | Acceleration at 2 kHz: C-axis X/Y/Z, spindle top X/Y, spindle bottom X/Y/Z. AE at 100 kHz (`.tdms`). **Spindle and axis currents** X/Y/Z/B/C at a stated 1 kHz, although the timestamps step by 0.5 ms. Currents are stored as one CSV per signal per day (3 days), with Windows FILETIME timestamps in descending order [V, P] |
| Machine, cutter | Willemin-Macodel "micro 5" 5-axis micro-milling machine [U for the maker; "micro 5" is P]. 3 mm tungsten carbide end mill (Louis Bélet 3100d3.00). 33,000 rpm. Compressed-air cooling (CO2 on test parts) [P] |
| Workpiece | Cylindrical stock milled in "stairs". The material is not stated in the paper text checked [P] |
| Known problems | Currents are not split by tool, so they must be aligned to the acc/AE timestamps. No license. Micro-milling scale is very different from ours |

### 6.12 VMC 650 production, low-cost DAQ (Rizwan, 2026): Tier 1, rank 8 (new find)

- **Download.** Zenodo `https://zenodo.org/records/21608174` (10.5281/zenodo.21608174, 26 July 2026). 24 CSVs, 33.7 MB. CC BY 4.0 [V].
- **Setup** [V, record description]: SANJI VMC 650 in real production, 38CR alloy steel, 20 mm two-flute indexable end mill with Mitsubishi APMT1135PDER-M2 VP15TF inserts (PVD TiAlN), 1,800 rpm, 1,500 mm/min, ap 0.6 mm, flood coolant.
- **Lifecycles.** 24 tools, each from fresh inserts until the operator declared failure (poor surface finish, chatter, vibration) [V].
- **Labels.** Remaining life from a linear time-based decay, no measured wear [V].
- **Signals.** SCT-013-050 current transformer on the spindle motor (`Current_A`) and an MPU6050 IMU (acceleration and gyroscope), logged by an Arduino UNO in bursts (about 10 rows per second, roughly every 19 s). One sample file covers about 17.8 h in 8,840 rows, and about 89% of its rows are idle [V, sub-agent].
- **Use.** Good for testing the replacement policy on real production lifetimes. Poor for learning signal features.

### 6.13 SDU-QIT (Xin et al., Shandong University / Qilu): Tier 1 content, access-blocked

Verified by the sub-agent from the paper PDF.

- **Access.** Listed on `https://www.qlit.edu.cn/datasets/` (HTTP 200). The only working download is Baidu Netdisk `https://pan.baidu.com/s/1BmKaKhedU7QKB3t9TzThOw` (code `rw97`); the SDU faculty mirror is dead. No license is stated, and the size is unknown.
- **Paper.** Journal of Mechanical Engineering 58(9):166 (2022), doi 10.3901/JME.2022.09.166.
- **Design.** 6 carbide end mills (10 mm, 3 flutes) run from new to scrap under 2 conditions, on a VDF-850 machine, dry. Workpiece is 45 steel, although the data folder is named "Milling_cutter_Cast_iron". Cutting parameters: 2,548 or 4,140 rpm, 764.4 or 1,242 mm/min, ap 0.5 mm, ae 5 mm.
- **Labels.** Per cut and per edge: VBmax, VB at ap/2 and wear area, plus end-teeth VBmax and area. End of life is VB at ap/2 = 0.3 mm, about 30 cuts per tool (tool 1_1 chipped at cut 29).
- **Signals.** KS903 triaxial accelerometer at 10 kHz, one CSV per cut. No current.

### 6.14 University of Michigan "CNC Mill Tool Wear" (Kaggle): Tier 2 at best

- **Download.** `https://www.kaggle.com/datasets/shasun/tool-wear-detection-in-cnc-mill` (HTTP 200). CC0, version 4 (2018), 12.2 MB unpacked. The API download worked without a login [V, sub-agent].
- **Design.** 18 experiments on a wax block. Labels are per experiment only (8 unworn, 10 worn), plus whether machining finished and whether the part passed visual inspection. No VB, no lifecycles, no tool count.
- **Signals.** 48 controller signals at 10 Hz, including `S1_CurrentFeedback`, `S1_OutputCurrent` and `S1_OutputPower`. No vibration.
- **Known problems.** 29% of rows match the documented error markers. Experiments 4, 5, 7 and 16 did not finish.

### 6.15 Bosch CNC machining (Tnani, Feil, Diepold, Procedia CIRP 107, 2022): unusable for remaining life

- **Download.** `https://github.com/boschresearch/CNC_Machining` (HTTP 200). Data CC BY 4.0, code BSD-3. 1,702 `.h5` files, 952 MB [V, sub-agent].
- **Content.** 3 machines (M01–M03), 15 operations, recorded February 2019 to August 2021. Bosch CISS triaxial acceleration at 2 kHz. Labels are good (1,632) or bad (70) process only. No tool-wear or lifecycle labels.

### 6.16 MSM 2026 (Kim et al., Purdue; Sci Data 13:945): unusable for remaining life

- **Download.** DOI 10.34740/kaggle/ds/8392825 → `https://www.kaggle.com/datasets/manufuturetoday/multi-sensor-for-metal-milling-anomaly` (HTTP 200), 14.2 GB, CC BY 4.0 [V].
- **Content.** 8 h 12 min from 3 machines (two lab mills, one production Haas VF-10). Microphones at 48 kHz, two single-axis accelerometers at 51.2 kHz (one machine only), MTConnect controller data, and a current transformer at 0.1 Hz (production machine) [P].
- **Labels.** Per cutting interval: 0 normal, 1 abnormal, 2 tool defect (pre-damaged tools). No wear progression, so no lifecycles [P]. It could only serve as auxiliary data for detecting abnormal cuts.

### 6.17 Other new finds, briefly

- **KIT multimodal CNC milling** (Ströbel et al.), DOI 10.35097/hvvwn1kfwf7qt48z, Data in Brief 2025, 10.1016/j.dib.2025.112207 [V, sub-agent].
  - Access: one 44.6 GB tar, open, CC BY 4.0.
  - Signals: DMC 60 H with SINUMERIK 840D, controller current, torque, power and load at 500 Hz; Kistler force and spindle acceleration at 10 kHz.
  - Content: 32–33 experiments with labelled anomalies. Tool wear appears only as one tool over 6 passes labelled by cutting time. Tier 2.
- **HMoTP** (Shandong University, RCIM 2024, 10.1016/j.rcim.2024.102723) [V, sub-agent].
  - Access: `https://github.com/dataforresearch/HMoTP` (HTTP 200), with data on Google Drive (public). About 700 MB. No license on the data.
  - Content: 3 tools × 100 cuts on thin-walled titanium parts, with Fx, Fy, Fz, Mz and workpiece acceleration at 32,000 samples per cut. Wear per flute per cut, with final means of 208–266 µm. Tier 2.
- **Mudestreda / Nonastreda** (Truchan et al.) [V, sub-agent].
  - Mudestreda: Zenodo 8238653 (GPL-3.0, 234 MB original). Images only (force spectrograms plus tool photos).
  - Nonastreda: Mendeley m892d2wtzh (CC BY 4.0, 1.41 GB). Adds raw 1 kHz Fx/Fy/Fz and numeric flank wear (final 136–347 µm).
  - Shared setup: DMG HSC 55, C45 steel. 10 tools run "until destroyed or sparks". Tier 2.
- **Aqifi 2026 desktop CNC**, Zenodo 21845441 (CC BY 4.0, 2.38 GB) [V].
  - Setup: 3 uncoated 3.175 mm two-flute end mills in 6061 aluminium on a Lunyee 3018 router.
  - Signals: two ADXL1002 accelerometers at 64 kHz, read alternately rather than simultaneously, in raw ADC counts.
  - Labels: the README says "No tool was run to failure and no failure criterion was applied". There are no per-block wear labels. Tier 2 (vibration pretraining).
- **Secondary (turning and drilling).**
  - Vicomtech turning: `https://github.com/Vicomtech/dataset-machine-tool-wear`, CC BY-SA 4.0, 3.3 MB. 13 tools, about 150 features per one-second segment, including spindle current, power and torque. Wear per segment [V, sub-agent].
  - Drilling tool wear: Mendeley th4yv974r2, 22.5 MB, CC BY 4.0. 4 drills from new to blunt, 3-axis accelerometer at 1 kHz, no numeric wear [V].
  - Kaggle turning and drilling sets (`adorigueto/cnc-turning-roughness-forces-and-tool-wear`, `drganeshkumars/flank-wear-of-cnc-lathe-tool-insert-dataset`, `raphaelwallsberger/xai-drilling-dataset`) are small tabular sets. They were not examined further.
- **Derived features.** Zenodo 23687416 (27 October 2026, CC BY 4.0, 3 MB) holds per-cut features for PHM 2010 (945 × 152) and per-run features for NASA (167 × 126). It is useful only as a quick baseline check.

---

## 7. Verification log (27 October 2026)

| Check | Result |
|---|---|
| Figshare API, 28589216 (ours) | 20 files, 25.37 GB in total: `raw_data.zip` 25,345,272,829 B, `FeatureAndMetadata_Milling.csv` 1.8 MB (968 data rows). CC BY |
| Mendeley public API, zpxs87bjt8 | 200. Version 3, 6,419 files, 10,621,168,188 B, CC BY. `filelist.csv` downloaded and per-tool counts computed. One run file (`M1T1R100C570VB55.h5`) opened |
| NASA S3 `3.+Milling.zip` | 200, 14,731,306 B. `mill.mat` parsed: 167 runs, 16 cases |
| PHM 2010 `cdn.teamholistic.net/.../c1–c6.zip` | 302 to the root, then 405 (dead) |
| Kaggle `rabahba/phm-data-challenge-2010` | 200. API listing shows 1,893 files, 6.8 GB |
| IEEE DataPort PHM 2010 (10.21227/jdxd-yy51) | Subscription required; "Files have not been uploaded" |
| HF `AI4Manufacturing/PHM2010` | `gated: manual`. README 200 (placeholder only), data files 401 |
| Figshare API, 27323346 (QIT-CEMC) | 2 files, 11.71 GB, CC BY 4.0. GitHub repository read, `tool_wear.csv` parsed (68 cycles) |
| Figshare API, 31801795 (MSTW) | 2 files, 13.1 GB, CC BY 4.0. Wear table parsed (25 cases, 824 rows). Zip directory read (822 recordings). One CSV header read by range request (1 kHz, 7 columns) |
| Zenodo API, 6505073 (HES-SO) | 3 zips, 14.1 GB, no license. Zip directories read by range request (6 tool folders) |
| Zenodo API, 21608174, 21845441, 8238653, 7753181, 23687416, 23688554, 15551212 | All open. Details as above |
| DOI 10.48764/3hdp-gf23 (MU-TCM) | Resolves to the eBiltegia handle. The host timed out (curl) and refused the connection (WebFetch) |
| `datasets.kia.prz.edu.pl` (Rzeszów 2023) | 200. The data page is password-protected |
| NUAA, MATWI (RDR), KIT (RADAR), Bosch GitHub, UMich Kaggle, qlit.edu.cn, HMoTP GitHub, Vicomtech GitHub, Mendeley m892d2wtzh and th4yv974r2, MSM Kaggle DOI | All returned HTTP 200 |

## Sources

- Our dataset: [Sci Data s41597-025-04923-y](https://www.nature.com/articles/s41597-025-04923-y), [Figshare 28589216](https://doi.org/10.6084/m9.figshare.28589216)
- LUH: [Mendeley zpxs87bjt8](https://data.mendeley.com/datasets/zpxs87bjt8), [Data in Brief PMC10558710](https://pmc.ncbi.nlm.nih.gov/articles/PMC10558710/)
- PHM 2010: [PHM Society challenge page](https://phmsociety.org/phm_competition/2010-phm-society-conference-data-challenge/), [scoring](https://phmsociety.org/competition/phm/10/scoring), [IEEE DataPort](https://ieee-dataport.org/documents/2010-phm-society-conference-data-challenge), [Kaggle mirror](https://www.kaggle.com/datasets/rabahba/phm-data-challenge-2010), [HF AI4Manufacturing/PHM2010](https://huggingface.co/datasets/AI4Manufacturing/PHM2010)
- NASA: [PCoE repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/), [S3 zip](https://phm-datasets.s3.amazonaws.com/NASA/3.+Milling.zip)
- QIT-CEMC: [Sci Data s41597-024-04345-2](https://www.nature.com/articles/s41597-024-04345-2), [Figshare 27323346](https://doi.org/10.6084/m9.figshare.27323346), [GitHub](https://github.com/wwz456/QIT-CEMC-dataset)
- MU-TCM: [Sci Data s41597-025-05168-5](https://www.nature.com/articles/s41597-025-05168-5), [DOI 10.48764/3hdp-gf23](https://doi.org/10.48764/3hdp-gf23), [code](https://github.com/spartanjoax/MU-TCM)
- GNN paper: [doi 10.1007/s42452-026-08390-x](https://link.springer.com/article/10.1007/s42452-026-08390-x)
- Rzeszów 2023: [Sensors 23:9346 (PMC10708711)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10708711/), [datasets.kia.prz.edu.pl](https://datasets.kia.prz.edu.pl/)
- MSM: [Sci Data s41597-026-07255-7](https://www.nature.com/articles/s41597-026-07255-7), [Kaggle](https://www.kaggle.com/datasets/manufuturetoday/multi-sensor-for-metal-milling-anomaly)
- MSTW EndMill: [Figshare 31801795](https://figshare.com/articles/dataset/_b_Multi-Sensor_Tool_Wear_End_Milling_MSTW_EndMill_Dataset_b_/31801795)
- HES-SO: [Zenodo 6505073](https://zenodo.org/records/6505073), [Discover Appl Sci paper PMC13341891](https://pmc.ncbi.nlm.nih.gov/articles/PMC13341891/)
- VMC 650: [Zenodo 21608174](https://zenodo.org/records/21608174)
- NUAA: [IEEE DataPort](https://ieee-dataport.org/open-access/tool-wear-dataset-nuaaideahouse)
- MATWI: [KU Leuven RDR](https://doi.org/10.48804/GK6LHH)
- SDU-QIT: [QLIT datasets page](https://www.qlit.edu.cn/datasets/)
- UMich: [Kaggle](https://www.kaggle.com/datasets/shasun/tool-wear-detection-in-cnc-mill)
- Bosch: [GitHub boschresearch/CNC_Machining](https://github.com/boschresearch/CNC_Machining)
- KIT: [RADAR4KIT](https://radar.kit.edu/radar/en/dataset/hvvwn1kfwf7qt48z)
- Mudestreda / Nonastreda: [Zenodo 8238653](https://zenodo.org/records/8238653), [Mendeley m892d2wtzh](https://data.mendeley.com/datasets/m892d2wtzh)
- HMoTP: [GitHub](https://github.com/dataforresearch/HMoTP)
- Aqifi: [Zenodo 21845441](https://zenodo.org/records/21845441)
- Vicomtech: [GitHub](https://github.com/Vicomtech/dataset-machine-tool-wear)
- Drilling: [Mendeley th4yv974r2](https://data.mendeley.com/datasets/th4yv974r2)
