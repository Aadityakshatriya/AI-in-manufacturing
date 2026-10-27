"""NASA Ames milling data (Agogino & Goebel; PCoE repository), data/raw/nasa/mill.mat.

One row = one run (one pass of a 70 mm, 6-insert face mill across a 483 × 178 × 51 mm block) of one
"case" (one set of inserts at one setting). 16 cases, 167 runs. Matsuura MC-510V.

Assumptions and facts (Readme.pdf and our own look at the data):
- Settings per case: cutting speed 200 m/min = 826 rpm; ap = DOC (0.75 or 1.5 mm); feed 0.25 or
  0.5 mm/rev (206.5 or 413 mm/min); material 1 = cast iron, 2 = stainless steel J45. ae is not
  stated, so cum_volume_mm3 is null. 6 inserts → tooth-pass 82.6 Hz.
- Clock: `time` is the cumulative cutting time of the case in minutes (it restarts per case); we
  take cum_time_s = 60 · time. A few cases log time = 0 for their first run.
- End of life: flank wear VB = 0.3 mm (not stated by the authors, the usual ISO-style choice).
  VB was measured after some runs only (20 of 167 missing); it is linearly interpolated over `time`
  between measured runs (held flat before the first and after the last measurement). The
  end-of-life run is the first run whose interpolated VB reaches 0.3 mm. Runs after it are dropped
  (cases continue up to VB 1.5 mm). Case 6 has a single run and is dropped. VB is not always
  monotonic (e.g. case 1: 0.29 → 0.28 → 0.29 mm); we interpolate the raw values.
- Signals, all 250 Hz, 9,000 samples (36 s) per run, which covers only part of each pass:
  smcAC = one spindle-motor phase current, raw AC (aliased at 250 Hz, but its RMS is fine);
  smcDC = the same current through a converter (a DC level that SATURATES at 10 V in about half of
  the later runs); vib_table / vib_spindle and AE_table / AE_spindle went through hardware RMS
  (8 ms time constant; vibration band-limited around 0.4–1 kHz) before sampling, so no spectra or
  spindle orders can be computed from them.
- Cutting mask: smcDC smoothed over 0.2 s; idle = its 5th percentile (spindle running, insert not
  engaged; about 1.35–1.4 V), cutting = more than halfway from idle to the 95th-percentile plateau
  (saturation does not hurt the mask). Idle samples = within 10% of the idle level.
- spindle_load_abs = AC RMS of smcAC over cutting minus AC RMS over idle samples (volts of sensor
  output; the readme gives no amps-per-volt). We use smcAC because smcDC clips at 10 V.
- vib_<ch>_rms / ae_<ch>_rms = quadratic mean of the hardware-RMS signal during cutting.
- Corrupt runs: case 2 run 1 (values ~1e29) and case 12 run 1 (all zero, 15,360 samples) are kept
  as rows (they still count toward the clock) with signal_ok = False and empty features.
- Missing runs: run numbers skip in places (case 3 has no run 4 or 13, case 14 no run 7).
"""

import numpy as np
import pandas as pd
import scipy.io as sio

from toollife.datasets.common import RAW, basic_stats, cutting_mask, finish

MAT = RAW / "nasa" / "mill.mat"
FS = 250.0
RPM = 826
TEETH = 6
VB_LIMIT_UM = 300.0
SIGNALS = ["smcAC", "smcDC", "vib_table", "vib_spindle", "AE_table", "AE_spindle"]
MATERIAL = {1: "cast_iron", 2: "steel_J45"}
INFO = {
    "end_of_life": "flank wear VB 0.3 mm (interpolated over time); first run reaching it",
    "signals": "spindle current AC+DC (raw), table/spindle vibration (hardware RMS), table/spindle AE (hardware RMS)",
    "rates": "all 250 Hz, 36 s per run",
}
REL_COLS = ["spindle_load_abs", "vib_table_rms", "vib_spindle_rms", "ae_table_rms", "ae_spindle_rms",
            "smcdc_net"]


def run_features(sig: dict) -> dict:
    """Physics features of one run from its six 250 Hz signals."""
    x = {k: np.asarray(v, dtype=float).ravel() for k, v in sig.items()}
    ok = (all(np.isfinite(v).all() and np.abs(v).max() < 50 for v in x.values())
          and x["smcDC"].max() > 2.0 and len(x["smcDC"]) >= 1000)
    if not ok:
        return {"signal_ok": False}
    dc, ac = x["smcDC"], x["smcAC"]
    cut, idle_dc, top_dc = cutting_mask(dc, FS, smooth_s=0.2)
    s = pd.Series(dc).rolling(50, center=True, min_periods=1).mean().to_numpy()
    idle = s < idle_dc + 0.1 * (top_dc - idle_dc)
    ac = ac - ac.mean()
    rms_cut = float(np.sqrt(np.mean(ac[cut] ** 2)))
    rms_idle = float(np.sqrt(np.mean(ac[idle] ** 2))) if idle.sum() > 25 else np.nan
    out = {
        "signal_ok": True,
        "cut_time_s": cut.sum() / FS,
        "spindle_idle": rms_idle,
        "spindle_load_abs": rms_cut - rms_idle,
        "smcdc_idle": idle_dc,
        "smcdc_net": float(dc[cut].mean() - idle_dc),
        "smcdc_sat_frac": float((dc[cut] >= 9.99).mean()),
    }
    for name in ["vib_table", "vib_spindle", "AE_table", "AE_spindle"]:
        out[f"{name.lower()}_rms"] = float(np.sqrt(np.mean(x[name][cut] ** 2)))
    for name in SIGNALS:
        out.update(basic_stats(name.lower(), x[name][cut]))
    return out


def load(workers: int = 1) -> pd.DataFrame:
    """One row per NASA run up to each case's end of life (VB 0.3 mm). `workers` is unused
    (one 73 MB file; all 167 runs take about a second)."""
    mill = sio.loadmat(MAT, squeeze_me=True)["mill"]
    rows = []
    for r in mill:
        case, material = int(r["case"]), int(r["material"])
        vb = float(r["VB"])
        row = {
            "dataset": "nasa", "tool": f"case{case:02d}", "run_native": int(r["run"]),
            "end_type": "wear", "cum_time_s": 60.0 * float(r["time"]), "cum_volume_mm3": np.nan,
            "machine": "Matsuura MC-510V", "material": MATERIAL[material], "rpm": RPM,
            "feed_mm_min": float(r["feed"]) * RPM, "ap_mm": float(r["DOC"]), "ae_mm": np.nan,
            "tool_diam_mm": 70.0, "teeth": TEETH, "vb_raw_um": vb * 1000 if np.isfinite(vb) else np.nan,
            "spindle_source": "smcAC current RMS", "spindle_unit": "V (sensor output)",
        }
        row.update(run_features({k: r[k] for k in SIGNALS}))
        rows.append(row)
    df = pd.DataFrame(rows).sort_values(["tool", "cum_time_s", "run_native"]).reset_index(drop=True)

    # VB: interpolate between measured runs on the time clock; find the end-of-life run.
    parts, eol_pos = [], {}
    for tool, g in df.groupby("tool", sort=False):
        g = g.copy()
        if len(g) < 3:  # case 6: a single run, no wear history
            continue
        meas = g["vb_raw_um"].notna()
        g["vb_measured"] = meas.astype(float)
        g["vb_um"] = np.interp(g["cum_time_s"], g.loc[meas, "cum_time_s"], g.loc[meas, "vb_raw_um"])
        hit = np.flatnonzero(g["vb_um"].to_numpy() >= VB_LIMIT_UM)
        g["eol_reached"] = len(hit) > 0
        eol_pos[tool] = int(hit[0]) if len(hit) else len(g) - 1
        parts.append(g)
    df = pd.concat(parts, ignore_index=True).drop(columns="vb_raw_um")
    return finish(df, eol_pos, rul_unit="runs", rel_cols=REL_COLS)


if __name__ == "__main__":
    out = load()
    print(out.groupby("tool").agg(runs=("run_idx", "size"), end_s=("cum_time_s", "max"),
                                  vb_end=("vb_um", "last"), load_rel_end=("spindle_load_rel", "last")))
    print("dropped after end of life:", out.attrs["dropped_after_eol"])
