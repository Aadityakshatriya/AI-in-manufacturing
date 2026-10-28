"""VMC 650 production tool lives, low-cost logger (Rizwan 2026, Zenodo 21608174), data/raw/vmc650/.

One CSV per tool (24 tools, June 2026), each from fresh inserts until the operator declared the tool
failed (poor finish, chatter, vibration). SANJI VMC 650 in real production, 38CR alloy steel,
20 mm two-flute indexable end mill (APMT1135 inserts), 1,800 rpm, 1,500 mm/min, ap 0.6 mm, flood
coolant (record description; the same values sit in every row).

Assumptions and facts (our own look at the files):
- Sampling: an Arduino logs bursts of 10 rows (about 1 s, timestamps to the second). Between bursts
  it waits about 19 s while the spindle is off and 30–100 s (median ~66 s) while it is on. Current
  (SCT-013 clamp, `Current_A`) is an RMS reading and is exactly 0 when the spindle is off.
- One "run" here = one burst taken while the spindle was on (burst mean current > 0.5 A); a tool
  has 63–160 of them. The spindle cannot be told apart from cutting with this sensor, so
  "cutting" = spindle on, and the cutting mask inside a burst = rows with current > 0.5 A.
  On-bursts whose mean current is below the tool's idle level (below) caught only a spin-up or
  spin-down and are dropped (e.g. tool 14's last burst).
- Clock: each on-burst stands for the time until the next burst (capped at 2× the tool's median
  on-to-on spacing; the last burst gets the median), and cum_time_s is the running sum, i.e. the
  estimated spindle-on time. cum_volume_mm3 is null (ae unknown).
- End of life: operator-declared failure = the last on-burst of the file (end_type 'operator').
  The dataset's own label `Tool_Wear_Label` (0 → 1, a linear "time-based" remaining-life label that
  only advances during on-bursts) is kept as label_native; there is no measured wear.
- Spindle load: idle level = 5th percentile of the on-row currents in the tool's first 10% of
  on-bursts (the spindle running lightly loaded, a per-tool constant, early life only so no
  future information leaks in); spindle_load_abs = mean on-row current of the burst − idle (A).
- Vibration: MPU6050 accelerometer; RelAccX/Y/Z (g, the logger's baseline-removed acceleration)
  give vib_x/y/z_rms over the on-rows. At ~10 samples per second no spindle orders exist
  (spindle 30 Hz, tooth-pass 60 Hz), so these are aliased overall levels only.
- With 10 rows per burst every per-run number is noisy; kurtosis of 10 values is mostly noise.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from toollife.datasets.common import RAW, basic_stats, finish, parallel_map

DIR = RAW / "vmc650"
ON_A = 0.5
INFO = {
    "end_of_life": "operator-declared failure (last spindle-on burst)",
    "signals": "spindle current (CT clamp, RMS reading), MPU6050 accel + gyro, temperature",
    "rates": "bursts of ~10 rows at ~10 Hz every 19 s (spindle off) / ~30-100 s (spindle on)",
}
REL_COLS = ["spindle_load_abs", "vib_x_rms", "vib_y_rms", "vib_z_rms"]
STAT_COLS = {"Current_A": "current", "AccX_g": "acc_x", "AccY_g": "acc_y", "AccZ_g": "acc_z",
             "GyroX_dps": "gyro_x", "GyroY_dps": "gyro_y", "GyroZ_dps": "gyro_z", "TempC": "temp"}


def tool_runs(path: Path) -> pd.DataFrame:
    """All on-bursts of one tool file, with features (idle and clock are fixed up in load)."""
    d = pd.read_csv(path)
    ts = pd.to_datetime(d["Date"] + " " + d["Time"])
    d["burst"] = (ts.diff().dt.total_seconds().fillna(0) > 2).cumsum()
    d["ts"] = ts
    bursts = d.groupby("burst").agg(t=("ts", "first"), cur=("Current_A", "mean"))
    bursts["gap_next"] = bursts["t"].shift(-1).sub(bursts["t"]).dt.total_seconds()
    on = bursts[bursts["cur"] > ON_A].copy()
    both_on = (bursts["cur"] > ON_A) & (bursts["cur"].shift(-1) > ON_A)
    med = float(bursts.loc[both_on, "gap_next"].median())
    on["dt_s"] = on["gap_next"].fillna(med).clip(upper=2 * med)

    first = d.iloc[0]
    rows = []
    for k, (b, info) in enumerate(on.iterrows()):
        g = d[d["burst"] == b]
        cut = g[g["Current_A"] > ON_A]
        row = {
            "dataset": "vmc650", "tool": f"tool{int(first['Tool_No']):02d}", "run_native": k,
            "file": path.name, "start_time": info["t"], "end_type": "operator",
            "dt_s": info["dt_s"], "cut_time_s": info["dt_s"], "cum_volume_mm3": np.nan,
            "machine": "SANJI VMC 650", "material": str(first["Workpiece_Material"]),
            "rpm": float(first["Spindle_RPM"]), "feed_mm_min": float(first["Feed_mm_per_min"]),
            "ap_mm": float(first["DoC_mm"]), "ae_mm": np.nan, "tool_diam_mm": 20.0, "teeth": 2,
            "vb_um": np.nan, "vb_measured": np.nan, "signal_ok": len(cut) >= 3,
            "spindle_source": "spindle current (CT clamp, RMS)", "spindle_unit": "A",
            "current_on_mean": float(cut["Current_A"].mean()),
            "label_native": float(g["Tool_Wear_Label"].iloc[-1]),
            "_currents": cut["Current_A"].to_numpy(),
        }
        for ax in "xyz":
            row[f"vib_{ax}_rms"] = float(np.sqrt(np.mean(cut[f"RelAcc{ax.upper()}"] ** 2)))
        for col, name in STAT_COLS.items():
            row.update(basic_stats(name, cut[col]))
        rows.append(row)
    return pd.DataFrame(rows)


IDLE_BURSTS = 10  # bursts used to find the spindle's idle current

def load(workers: int = 8) -> pd.DataFrame:
    """One row per spindle-on burst, for all 24 tools, end of life = operator's call."""
    files = sorted(DIR.glob("*.csv"))
    parts = parallel_map(tool_runs, files, workers)
    df = pd.concat(parts, ignore_index=True).sort_values(["tool", "run_native"]).reset_index(drop=True)
    for tool, g in df.groupby("tool", sort=False):
        # Idle level from the tool's first IDLE_BURSTS bursts: a fixed count, so it never depends on
        # how long the tool will eventually last. (Until 28 Oct this used the first 10% of the
        # tool's bursts, which quietly used its future life length.)
        k = min(len(g), IDLE_BURSTS)
        df.loc[g.index, "spindle_idle"] = float(np.percentile(np.concatenate(g["_currents"].iloc[:k].to_list()), 5))
    # Bursts whose mean current is below the idle level caught only a spin-up or spin-down.
    df = df[df["current_on_mean"] >= df["spindle_idle"]].reset_index(drop=True)
    eol_pos = {}
    for tool, g in df.groupby("tool", sort=False):
        df.loc[g.index, "cum_time_s"] = g["dt_s"].cumsum()
        eol_pos[tool] = len(g) - 1
    df["spindle_load_abs"] = df["current_on_mean"] - df["spindle_idle"]
    df["eol_reached"] = True
    df = df.drop(columns=["_currents", "dt_s"])
    return finish(df, eol_pos, rul_unit="on-bursts", rel_cols=REL_COLS)


if __name__ == "__main__":
    out = load()
    print(out.groupby("tool").agg(runs=("run_idx", "size"), life_min=("cum_time_s", lambda s: s.max() / 60),
                                  idle=("spindle_idle", "first"), load_end=("spindle_load_rel", "last")))
