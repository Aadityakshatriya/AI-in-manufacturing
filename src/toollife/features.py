"""Physics features for one Rzeszów cycle, computed from the converted raw arrays.

Each feature has a physical reason to change with wear (research/next-phase/physics-brief.md, Part D):
  - net spindle current while cutting      -> twisting effort (cutting power)
  - table (X, Y) current while cutting      -> how hard the steel pushes back; rises fastest with flank wear
  - spindle charge per mm³ removed          -> energy spent per unit of steel (setting-independent)
  - tooth-pass orders (4, 8, 12 × 53.3 Hz)  -> size of each tooth's hammer blow
  - other spindle orders (1, 2, 3, 5, 6, 7) -> one tooth differs from the others: chipping, runout
  - synchronous fraction                    -> drops when chatter puts energy off the spindle rhythm
  - high-band RMS (2–12 kHz), kurtosis      -> rubbing noise and short impacts
Values are absolute here; ratios to each cutter's first cycles are taken later, per cutter.
"""

from pathlib import Path

import numpy as np
from scipy.signal import welch
from scipy.stats import kurtosis

from toollife.rawzip import AMPS_PER_COUNT, MS2_PER_COUNT, SPINDLE_HZ
from toollife.rzeszow import ROOT

CYCLES = ROOT / "data" / "rzeszow_cycles"
FS_VIB = 25_000

# Tool-centre path length per ring, from the companion paper's per-tool totals
# (physics-brief.md C3): about 366 mm at 8 mm sideways bite, 352 mm at 4.5 mm.
PATH_MM = {8.0: 366.0, 4.5: 352.0}

# Sensors on the table drives hear the teeth best; the spindle-head ones mostly hear the spindle.
TABLE_ACC = ["X Driving axle +Z", "X Driving axle -X", "Y Driving axle +Z", "Y Driving axle +Y", "Y Driving axle -X"]
HEAD_ACC = ["Spindle +Y", "Spindle -Z", "Spindle -X"]


def load_cycle(file: str) -> dict:
    """Converted arrays of one cycle in physical units, with a cutting mask on both clocks."""
    z = np.load(CYCLES / f"{file}.npz")
    vib_names = [n.replace("Accelerometer - ", "") for n in z["vib_names"]]
    cur_names = list(z["cur_names"])
    t_cur = z["cur_t_ms"].astype(np.float64) / 1000.0
    t_vib = (float(z["vib_t0_ms"]) + np.arange(len(z["vib"])) * 0.04) / 1000.0
    cur = z["cur"].astype(np.float64) * AMPS_PER_COUNT

    def phase(name):
        return cur[:, [cur_names.index(f"Current - {name} L{i}") for i in (1, 2, 3)]].mean(axis=1)

    spindle, x_axis, y_axis, z_axis = (phase(n) for n in ("Spindle", "Driving axle X", "Driving axle Y", "Driving axle Z"))
    on = spindle > 2.0
    idle = np.percentile(spindle[on], 20) if on.any() else np.nan
    window = np.zeros_like(on)
    if on.any():
        t_on = t_cur[np.flatnonzero(on)[0]]
        off = np.flatnonzero(on)[-1]
        at_idle = np.flatnonzero(np.abs(spindle[: off + 1] - idle) < 0.1)
        t_stop = t_cur[at_idle[-1]] if len(at_idle) else t_cur[off]
        window = (t_cur > t_on + 4.0) & (t_cur < t_stop)
    cutting_cur = window & (spindle > idle + 0.3)
    j = np.clip(np.searchsorted(t_cur, t_vib, side="right") - 1, 0, len(t_cur) - 1)
    return dict(
        t_cur=t_cur, spindle=spindle, x_axis=x_axis, y_axis=y_axis, z_axis=z_axis, idle=idle,
        cutting_cur=cutting_cur, cutting_vib=cutting_cur[j],
        vib={n: z["vib"][:, i].astype(np.float64) * MS2_PER_COUNT for i, n in enumerate(vib_names)},
    )


def _order_power(f, p, order, half_width_hz=2.0):
    band = np.abs(f - order * SPINDLE_HZ) <= half_width_hz
    return p[band].sum()


def cycle_features(d: dict, adoc_mm: float, rdoc_mm: float) -> dict:
    out = {}
    cut = d["cutting_cur"]
    dt = np.median(np.diff(d["t_cur"]))
    out["cut_seconds"] = cut.sum() * dt
    out["idle_spindle_a"] = d["idle"]
    if cut.sum() < 50:  # less than 0.1 s of cutting: nothing reliable to measure
        return out

    net = d["spindle"][cut] - d["idle"]
    out["spindle_net_a"] = net.mean()
    out["spindle_net_p95_a"] = np.percentile(net, 95)
    out["x_cut_a"] = d["x_axis"][cut].mean()
    out["y_cut_a"] = d["y_axis"][cut].mean()
    out["z_cut_a"] = d["z_axis"][cut].mean()
    out["table_cut_a"] = out["x_cut_a"] + out["y_cut_a"]
    out["table_over_spindle"] = out["table_cut_a"] / max(out["spindle_net_a"], 1e-6)
    volume = adoc_mm * rdoc_mm * PATH_MM[float(rdoc_mm)]
    out["spindle_charge_per_mm3"] = net.sum() * dt / volume  # A·s per mm³, proxy for energy per mm³

    vmask = d["cutting_vib"]
    for name, sig in d["vib"].items():
        key = name.replace(" ", "_").replace("+", "p").replace("-", "m")
        x = sig[vmask]
        if len(x) < 4096:
            continue
        x = x - x.mean()
        out[f"{key}__rms"] = np.sqrt(np.mean(x**2))
        out[f"{key}__kurt"] = kurtosis(x, fisher=False)
        f, p = welch(x, fs=FS_VIB, nperseg=min(16384, len(x)))
        total = p.sum()
        tooth = sum(_order_power(f, p, k) for k in (4, 8, 12, 16))
        other = sum(_order_power(f, p, k) for k in (1, 2, 3, 5, 6, 7))
        sync = sum(_order_power(f, p, k) for k in range(1, 41))
        out[f"{key}__order1"] = np.sqrt(_order_power(f, p, 1))
        out[f"{key}__tooth"] = np.sqrt(tooth)
        out[f"{key}__asym"] = other / max(tooth, 1e-12)
        out[f"{key}__sync_frac"] = sync / max(total, 1e-12)
        out[f"{key}__hiband_rms"] = np.sqrt(p[(f >= 2000) & (f <= 12000)].sum() * (f[1] - f[0]))
    return out
