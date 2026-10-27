"""MSTW EndMill 2026 (Sayyad, Kumar, Bongale; Figshare 31801795), data/raw/mstw/.

Sensor_Data_DAQ_updated.zip holds one folder per "case" (one cutter at one setting), named like
`10_S900_F40_D0.1`, with one CSV per run (`Recording <k>.csv`). Tool_Wear_Value_Table.xlsx gives
flank wear (µm) per case and run. 25 cases, 822 recordings, CC BY 4.0. The archive is read member by
member and never unzipped; while it is still downloading, the partial `.zip.part` is walked header by
header (common.zip_index), and the last case seen is skipped because it may be incomplete.

Assumptions and facts (no README exists; machine, workpiece, cutter, feed units and sensor
calibration are undocumented):
- Settings from the folder name: S = spindle rpm (our check: the table vibration has lines at exact
  multiples of S/60, e.g. 15.0 Hz for S900), D = depth of cut, taken as ap in mm, F = feed with unknown
  units (kept as feed_native; feed_mm_min is null). ae, cutter diameter and teeth are unknown, so
  cum_volume_mm3 is null. Teeth: ASSUMED 4 for the tooth-pass features (the spectra show many spindle
  orders, 2 and 4 among the strongest, so this is not confirmed); order 2 is also given.
- Signals, all raw volts at 1 kHz: Vib_Spindle, Vib_Table, X/Y/Z_Load_Cell, Current. A unit row
  follows the header. Recordings last 300–600 s.
- Current is the raw AC motor current riding on a DC offset (a clean sine at 2.4 × spindle Hz, e.g.
  36 Hz at 900 rpm, in case 10; much noisier in cases 11–12). Its RMS is taken over 100 ms windows
  (3.2–4.8 electrical periods at 800–1,200 rpm) after removing each window's mean; the brief's
  "~20 ms" assumed 50 Hz mains and would hold less than one period here.
- Cutting mask: the recordings contain no idle or air-cut stretch (the current envelope and vibration
  never drop to a spindle-only level), so the whole recording is treated as cutting. There is
  therefore no idle level: spindle_idle is null and spindle_load_abs is the mean current RMS
  (magnetising plus load current), so its ratio to early life understates the true change in cutting
  load. spindle_net_p5 = mean − 5th percentile of the 1 s envelope is given as the survey's fallback
  ("lowest 5th percentile of the cut" as idle), with its _rel.
- Clock: cum_time_s = running sum of recording durations in recording order (Recording 1, 2, … sorted
  numerically). end of life = the last recording of each case (wear table: every case ends at
  VB 300.7–318.2 µm). end_type 'wear'.
- Wear: recording k ↔ wear-table row k. Cases 1, 5, 6 and 24 have one small drop in VB. Cases 6
  (30 recordings, 33 wear rows) and 25 (36 vs 35) do not line up; vb_aligned = False marks them and
  their vb_um should not be trusted near the end.
- Load cells: X and Y barely move (≈ noise) and Z drifts slowly within and across recordings, so
  they do not show cutting force. loadcell_xy_abs (mean √(X²+Y²), V) and loadcell_z_abs (mean Z, V)
  are kept under their own names and the shared force_rel stays empty for MSTW. Recordings where Z
  sits at ~0 V (load-cell chain off, e.g. case 14 runs 1–4) get empty load-cell features.
- Current channel set-ups: the Current DC offset is ~5.1 V (clean sine) in some recordings and
  ~2.6 V (noisy) in others, sometimes switching inside one case (case 14 runs 1–4 vs 5–34; case 13
  runs 8–9 at ~3.7 V). These are different sensor set-ups whose RMS values are not comparable, so a
  recording whose DC offset is more than 0.5 V from its case's median gets empty spindle/current
  features (current_ok = False).
- Duplicates: some recordings are byte-identical copies across cases (case 12 runs 7–22 equal case
  11 runs 7–22). md5 of every recording is kept; the first copy in archive order keeps its features,
  later copies get duplicate_of = the original member, signal_ok = False and empty features. Which
  case truly owns the data is unknown.
"""

import hashlib
import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv

from toollife.datasets.common import (RAW, basic_stats, finish, order_features, parallel_map, window_rms,
                                      zip_index, zip_read)

DIR = RAW / "mstw"
ZIP = DIR / "Sensor_Data_DAQ_updated.zip"
PART = DIR / "Sensor_Data_DAQ_updated.zip.part"
WEAR = DIR / "Tool_Wear_Value_Table.xlsx"
FS = 1000.0
TEETH_ASSUMED = 4
ENV_WINDOW = 100  # samples = 100 ms
FOLDER = re.compile(r"(\d+)_S(\d+)_F([\d.]+)_D([\d.]+)")
VIB = {"Vib_Spindle": "vib_spindle", "Vib_Table": "vib_table"}
LOADCELL = {"X_Load_Cell": "load_x", "Y_Load_Cell": "load_y", "Z_Load_Cell": "load_z"}
INFO = {
    "end_of_life": "last recording of each case (VB 300.7-318.2 um in the wear table)",
    "signals": "spindle current (raw AC, V), spindle + table vibration (V), X/Y/Z load cells (V, unresponsive)",
    "rates": "all 1 kHz, 300-600 s per recording",
}
REL_COLS = (["spindle_load_abs", "spindle_net_p5", "loadcell_xy_abs", "loadcell_z_abs"]
            + [f"{v}_{k}" for v in VIB.values() for k in ("rms", "o1", "o2", "tp", "hi")])


def archive() -> tuple[Path, bool]:
    """(path, complete?) of the sensor archive."""
    if ZIP.exists():
        return ZIP, True
    return PART, False


def parse_recording(data: bytes) -> pd.DataFrame:
    """One recording CSV (header, then a unit row, then 1 kHz samples) as a DataFrame.

    A few recordings contain broken lines (2 values instead of 7) or a repeated header line inside
    the data; such lines are dropped. Seven recordings of case 4 were published damaged (they start
    mid-file with no header, one is binary); those raise ValueError and are marked unusable.
    """
    if not data.startswith(b"Time,"):
        raise ValueError("recording has no header (damaged in the published archive)")
    try:
        table = pacsv.read_csv(io.BytesIO(data), read_options=pacsv.ReadOptions(skip_rows_after_names=1, use_threads=False))
        df = table.to_pandas()
        if all(pd.api.types.is_numeric_dtype(t) for t in df.dtypes):
            return df
    except (pa.ArrowInvalid, ValueError):
        pass
    df = pd.read_csv(io.BytesIO(data), skiprows=[1], on_bad_lines="skip", dtype=str, encoding="latin-1")
    raw_rows = len(df)
    df = df.apply(pd.to_numeric, errors="coerce").dropna().reset_index(drop=True)
    if len(df) < 0.95 * raw_rows:
        raise ValueError(f"recording damaged: only {len(df)} of {raw_rows} lines readable")
    return df


def run_features(job: tuple) -> dict:
    """Physics features of one recording. job = (zip path, member name, zip entry)."""
    path, name, entry = job
    data = zip_read(path, entry)
    try:
        d = parse_recording(data)
    except (ValueError, UnicodeDecodeError) as e:  # a damaged recording: keep the row, mark it unusable
        return {"member": name, "signal_ok": False, "cut_time_s": np.nan, "md5": hashlib.md5(data).hexdigest(), "error": str(e)[:80]}
    rpm = float(FOLDER.search(name).group(2))
    out = {"member": name, "signal_ok": len(d) > 10 * FS, "cut_time_s": len(d) / FS,
           "md5": hashlib.md5(data).hexdigest()}
    if not out["signal_ok"]:
        return out
    cut = np.ones(len(d), bool)  # no idle stretches in these recordings (see module docstring)

    env = window_rms(d["Current"].to_numpy(), ENV_WINDOW)
    sec = env[: len(env) // 10 * 10].reshape(-1, 10).mean(axis=1)  # 1 s envelope
    out["spindle_idle"] = np.nan
    out["spindle_load_abs"] = float(env.mean())
    out["spindle_net_p5"] = float(env.mean() - np.percentile(sec, 5))
    out.update(basic_stats("current_env", env))
    out.update(basic_stats("current", d["Current"].to_numpy()))

    for col, short in VIB.items():
        x = d[col].to_numpy()
        out.update(basic_stats(short, x))
        out.update(order_features(short, x, cut, FS, rpm / 60, TEETH_ASSUMED, extra_orders=(2,)))
    lc = {short: d[col].to_numpy() for col, short in LOADCELL.items()}
    for short, x in lc.items():
        out.update(basic_stats(short, x))
    out["loadcell_xy_abs"] = float(np.hypot(lc["load_x"], lc["load_y"]).mean())
    out["loadcell_z_abs"] = float(lc["load_z"].mean())
    return out


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Blank features that come from a broken or copied recording (see module docstring)."""
    df = df.copy()
    # Byte-identical recordings: keep the first copy in archive order, blank the later ones.
    first = df.drop_duplicates("md5").set_index("md5")["member"]
    df["duplicate_of"] = df["md5"].map(first).where(lambda m: m != df["member"])
    feat = [c for c in df.columns if c.startswith(("spindle_", "current", "vib_", "load_", "loadcell_"))
            and c not in ("spindle_source", "spindle_unit")]
    dup = df["duplicate_of"].notna()
    df.loc[dup, feat] = np.nan
    df.loc[dup, "signal_ok"] = False
    # Current channel: other DC offset than the tool's usual one = another sensor set-up.
    off = (df["current_mean"] - df.groupby("tool")["current_mean"].transform("median")).abs() > 0.5
    df["current_ok"] = ~off & df["current_mean"].notna()
    df.loc[off, [c for c in feat if c.startswith(("spindle_", "current"))]] = np.nan
    # Load cells: Z at ~0 V means the load-cell chain was not connected.
    lc_off = df["load_z_mean"].abs() < 0.01
    df.loc[lc_off, [c for c in feat if c.startswith(("load_", "loadcell_"))]] = np.nan
    return df


def wear_table() -> dict[int, np.ndarray]:
    """case -> VB (µm) per run, in run order."""
    x = pd.read_excel(WEAR, header=0)
    out = {}
    for col in x.columns[1:]:
        case = int(re.search(r"(\d+)", col).group(1))
        out[case] = x[col].dropna().to_numpy(float)
    return out


def load(workers: int = 8) -> pd.DataFrame:
    """One row per MSTW recording for every complete case in the archive."""
    path, complete = archive()
    idx = zip_index(path)
    members = [n for n in idx if n.lower().endswith(".csv")]
    order = []  # cases in archive order, to spot the one still downloading
    for n in members:
        case = n.split("/")[-2]
        if case not in order:
            order.append(case)
    skipped = [] if complete else order[-1:]
    members = [n for n in members if n.split("/")[-2] not in skipped]
    feats = pd.DataFrame(parallel_map(run_features, [(path, n, idx[n]) for n in members], workers))

    vb = wear_table()
    rows = []
    for n in members:
        m = FOLDER.search(n.split("/")[-2])
        case = int(m.group(1))
        k = int(re.search(r"Recording (\d+)\.csv", n).group(1))
        rows.append({
            "dataset": "mstw", "tool": f"case{case:02d}", "member": n, "run_native": k, "end_type": "wear",
            "cum_volume_mm3": np.nan, "machine": "MSTW rig (undocumented)", "material": "unknown",
            "rpm": float(m.group(2)), "feed_mm_min": np.nan, "feed_native": float(m.group(3)),
            "ap_mm": float(m.group(4)), "ae_mm": np.nan, "tool_diam_mm": np.nan, "teeth": np.nan,
            "vb_um": vb[case][k - 1] if k <= len(vb[case]) else np.nan, "vb_measured": 1.0,
            "spindle_source": "spindle current AC RMS (100 ms)", "spindle_unit": "V (raw)",
        })
    df = pd.DataFrame(rows).merge(feats, on="member", how="left")
    df = df.sort_values(["tool", "run_native"]).reset_index(drop=True)
    eol_pos = {}
    for tool, g in df.groupby("tool", sort=False):
        df.loc[g.index, "cum_time_s"] = g["cut_time_s"].cumsum()
        case = int(tool[4:])
        df.loc[g.index, "vb_aligned"] = len(g) == len(vb[case])
        eol_pos[tool] = len(g) - 1
    df["eol_reached"] = True
    df = clean(df)
    out = finish(df, eol_pos, rul_unit="runs", rel_cols=REL_COLS)
    out.attrs["archive_complete"] = complete
    out.attrs["skipped_cases"] = skipped
    return out


if __name__ == "__main__":
    out = load()
    print(out.groupby("tool").agg(runs=("run_idx", "size"), end_s=("cum_time_s", "max"), vb_end=("vb_um", "last"),
                                  aligned=("vb_aligned", "first"), load_end=("spindle_load_rel", "last")))
    print("archive complete:", out.attrs["archive_complete"], "skipped (incomplete):", out.attrs["skipped_cases"])
