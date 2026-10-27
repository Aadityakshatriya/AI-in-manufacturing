"""LUH Hannover tool-wear data (Denkena, Klemme, Stiehl; Data in Brief 2023; Mendeley zpxs87bjt8).

data/raw/luh/: one HDF5 file per run, named M<machine>T<tool>R<run>C<contact s>VB<wear µm>.h5, plus
filelist.csv with the same labels. 9 solid-carbide end mills, 3 per machine, cast iron 600-3/S.

Assumptions and facts:
- Machines: M1 DMG Mori Milltap 700 (Sinumerik 840D sl), M2 DMG Mori HSC 30 linear, M3 DMG Mori
  HSC 55 linear (Heidenhain iTNC 530) [paper]. Same cutting settings on all three.
- Settings: vc 200 m/min, vf 1,592 mm/min, ap 2 mm, 4 teeth. Our own check: the force spectra
  carry their tooth-pass line at ~531 Hz and the spindle torque its order-1 line at ~132.7 Hz,
  i.e. 7,960 rpm, which is vc 200 m/min on an 8 mm cutter (fz = 0.050 mm). So tool_diam_mm = 8
  (the survey's 10 mm guess was wrong). ae = 4 mm comes from the MU-TCM comparison table and is
  unverified; cum_volume_mm3 = ap·ae·vf·C = 212.3 mm³/s × C on that assumption.
- One run = one straight cut (tool entry, ~100 mm straight path, exit) of ~4.4 s. Runs that crossed
  mounting holes, layer-first/last runs and corrupted ones were removed by the authors and the rest
  renumbered, so run numbers are consecutive but the clock is not.
- Clock: C in the file name is the cumulated tool contact time. Its HDF5 attribute says "min" but
  the values are SECONDS (+4 per ~4 s run; 3,400–5,200 per life). cum_time_s = C. It still counts
  the removed runs, which is what we want.
- End of life: VB = 150 µm (mean of 4 edges). VB in the name is measured about every 40 runs and
  linearly interpolated over contact time by the authors (which runs were measured is not given,
  so vb_measured is NaN). End-of-life run = first run with VB ≥ 150 µm; four tools stop at
  145–149 µm (inside the stated ±5 µm measurement uncertainty), so their last run is end of life,
  still counted as reached. T8 (M3) has no files before C = 177 s (VB 34 µm): its early-life
  baseline is therefore not a new tool.
- Life columns come from filelist.csv (complete even while the download is not), so life_frac and
  rul_native are right even if some run files are still missing; rows without a file are dropped.
- Signals: controller at 500 Hz (torque_spindle in Nm, axis torques on M1 or axis forces on
  M2/M3, position-control deviations, tool positions) and a Kistler 9257B table dynamometer at
  25 kHz (Fx, Fy, Fz in N). The two clocks are aligned only to about 100 ms, so each gets its own
  cutting mask. M2 had its control filter off, so torque_spindle aliases there: use means only.
- Spindle load: torque_spindle smoothed over 50 ms; idle = median over the last 0.25 s of the file
  (after the exit, spindle still turning); load = |torque − idle| (cutting torque is more negative
  than idle on M1); cutting = load more than half of its 95th percentile. spindle_load_abs = mean
  net torque during cutting (Nm). No vibration sensor exists.
- Force: each axis has its zero offset (median of the last 0.2 s) removed; in-plane resultant
  √(Fx²+Fy²) smoothed over 10 ms gives the force mask (more than half of its 95th percentile).
  force_res_abs = mean resultant during cutting (N). Fz changes sign with wear (+25 N new,
  −45 N worn on M1T1), so it gets statistics but no ratio.
- Spindle orders on the 25 kHz force channels: force_<ax>_o1 / _tp / _hi as in
  common.order_features (spindle ~132.7 Hz, tooth-pass ~531 Hz, harmonics at 1,061 and 1,592 Hz).
"""

import re
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from toollife.datasets.common import RAW, basic_stats, finalize, life_columns, order_features, parallel_map, smooth

DIR = RAW / "luh"
FS_MACHINE = 500.0
FS_FORCE = 25_000.0
RPM = 200_000 / (np.pi * 8)  # 7,958 rpm: vc 200 m/min on an 8 mm cutter
TEETH = 4
AP, AE, VF = 2.0, 4.0, 1592.0
MRR_MM3_S = AP * AE * VF / 60
VB_LIMIT_UM = 150.0
VB_REACHED_UM = 145.0  # final VB within the ±5 µm measurement uncertainty of the limit
MACHINES = {1: "M1 DMG Mori Milltap 700", 2: "M2 DMG Mori HSC 30 linear", 3: "M3 DMG Mori HSC 55 linear"}
NAME = re.compile(r"M(\d)T(\d)R(\d+)C(\d+)VB(\d+)\.h5")
INFO = {
    "end_of_life": "flank wear VB 150 um (first run reaching it; 4 tools stop at 145-149 um = last run)",
    "signals": "spindle torque + axis torques/forces + positions (controller), Kistler force Fx/Fy/Fz; no vibration",
    "rates": "controller 500 Hz, dynamometer 25 kHz, ~4.4 s per run",
}
REL_COLS = ["spindle_load_abs", "force_res_abs"] + [f"force_{a}_{k}" for a in "xyz" for k in ("rms", "o1", "tp", "hi")]


def run_features(path: Path) -> dict:
    """Physics features of one LUH run file."""
    with h5py.File(path, "r") as h:
        mach = {k: h["signals_machine"][k][0].astype(float) for k in h["signals_machine"]}
        force = {a: h["signals_sensor"][f"force_sensor_{a}"][0].astype(float) for a in "xyz"}
    out = {"file": path.name, "signal_ok": True}

    # Spindle torque: idle after the exit, load = |net torque|.
    tq = mach["torque_spindle"]
    s = smooth(tq, 25)
    idle = float(np.median(s[-125:]))
    load = np.abs(s - idle)
    cut = load > 0.5 * np.percentile(load, 95)
    if cut.sum() < 50:
        return {"file": path.name, "signal_ok": False}
    out["cut_time_s"] = cut.sum() / FS_MACHINE
    out["spindle_idle"] = idle
    out["spindle_load_abs"] = float(np.abs(tq[cut] - idle).mean())
    for name, x in mach.items():
        if name.startswith(("torque", "force", "position_control")):
            out.update(basic_stats(name, x[cut]))

    # Dynamometer: offsets from the last 0.2 s, in-plane resultant for the mask.
    f = {a: x - np.median(x[-5000:]) for a, x in force.items()}
    fxy = np.hypot(f["x"], f["y"])
    sm = smooth(fxy, 250)
    fcut = sm > 0.5 * np.percentile(sm, 95)
    out["force_cut_time_s"] = fcut.sum() / FS_FORCE
    out["force_res_abs"] = float(fxy[fcut].mean())
    out["force_z_abs"] = float(f["z"][fcut].mean())
    for a in "xyz":
        out.update(basic_stats(f"force_{a}", f[a][fcut]))
        out.update(order_features(f"force_{a}", f[a], fcut, FS_FORCE, RPM / 60, TEETH))
    return out


def labels() -> pd.DataFrame:
    """All runs from filelist.csv, with life columns (end of life = first VB >= 150 µm)."""
    fl = pd.read_csv(DIR / "filelist.csv")
    df = pd.DataFrame({
        "dataset": "luh", "tool": "M" + fl["machine"].astype(str) + "T" + fl["tool"].astype(str),
        "run_native": fl["run"], "file": fl["filename"], "end_type": "wear",
        "cum_time_s": fl["cumulated_tool_contact_time"].astype(float),
        "cum_volume_mm3": MRR_MM3_S * fl["cumulated_tool_contact_time"].astype(float),
        "machine": fl["machine"].map(MACHINES), "material": "cast_iron_600-3/S", "rpm": RPM,
        "feed_mm_min": VF, "ap_mm": AP, "ae_mm": AE, "tool_diam_mm": 8.0, "teeth": TEETH,
        "vb_um": fl["wear"].astype(float), "vb_measured": np.nan,
        "spindle_source": "spindle torque (controller)", "spindle_unit": "Nm",
    }).sort_values(["tool", "cum_time_s"]).reset_index(drop=True)
    eol_pos = {}
    for tool, g in df.groupby("tool", sort=False):
        hit = np.flatnonzero(g["vb_um"].to_numpy() >= VB_LIMIT_UM)
        eol_pos[tool] = int(hit[0]) if len(hit) else len(g) - 1
        df.loc[g.index, "eol_reached"] = g["vb_um"].max() >= VB_REACHED_UM
    return life_columns(df, eol_pos, rul_unit="runs")


def load(workers: int = 8) -> pd.DataFrame:
    """One row per LUH run file present on disk, up to each tool's end of life."""
    lab = labels()
    present = lab[lab["file"].map(lambda f: (DIR / f).exists())]
    feats = pd.DataFrame(parallel_map(run_features, [DIR / f for f in present["file"]], workers))
    df = present.merge(feats, on="file", how="left")
    df.attrs["dropped_after_eol"] = lab.attrs["dropped_after_eol"]
    df.attrs["files_missing"] = int(len(lab) - len(present))
    out = finalize(df, REL_COLS)
    out.attrs["files_missing"] = df.attrs["files_missing"]
    return out


if __name__ == "__main__":
    out = load()
    print(out.groupby("tool").agg(runs=("run_idx", "size"), end_s=("cum_time_s", "max"), vb_end=("vb_um", "last"),
                                  load_end=("spindle_load_rel", "last"), force_end=("force_res_abs_rel", "last")))
    print("missing files:", out.attrs["files_missing"], "dropped after end of life:", out.attrs["dropped_after_eol"])
