"""Figures for the physics explainer, made from cutter 8's real raw signals.

Cutter 8: Type 1, depth 5 mm, sideways 4.5 mm, 80 mm holder, 116 cycles from new to broken.
Writes PNGs to docs/img/physics/.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import welch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.rawzip import SPINDLE_HZ, TOOTH_HZ, read_cycle, tidy
from toollife.rzeszow import ROOT, load_table

OUT = ROOT / "docs" / "img" / "physics"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
NEW, WORN = "#2f4a5c", "#c2410c"
ACC = "X Driving axle +Z"  # the table-side sensor that hears the teeth most clearly

df = load_table()
t8 = df[(df.tool == 8) & ~df.file.str.endswith("_C1")]  # cycle-1 files include corner clean-up
early = t8[t8.age >= 3].iloc[0]
worn = t8[t8.rul >= 1].iloc[-1]
picked = {"new": early, "worn": worn}
sig = {k: tidy(read_cycle(r.file)) for k, r in picked.items()}
label = {k: f"{'Nearly new' if k == 'new' else 'Worn'}: cycle {r.age + 1} of 116 ({r.rul} left)" for k, r in picked.items()}
print({k: r.file for k, r in picked.items()})

# 1. Motor currents over one whole cycle.
fig, axes = plt.subplots(2, 1, figsize=(9, 5.5), sharex=True)
for k, color in (("new", NEW), ("worn", WORN)):
    s = sig[k]
    t0 = s["t_cur"][np.flatnonzero(s["cutting_cur"])[0]]  # line both cycles up at the first bite
    keep = (s["t_cur"] - t0 > -8) & (s["t_cur"] - t0 < 40)
    axes[0].plot(s["t_cur"][keep] - t0, s["spindle"][keep], color=color, lw=1.2, label=label[k])
    axes[1].plot(s["t_cur"][keep] - t0, s["x_axis"][keep], color=color, lw=1.2)
axes[0].set_ylabel("Spindle motor\ncurrent (A)")
axes[1].set_ylabel("Table (X) motor\ncurrent (A)")
axes[1].set_xlabel("seconds since the cutter first bit into the steel")
axes[0].legend(frameon=False, loc="upper left", fontsize=8)
axes[0].set_title("Cutter 8: the motors work harder when the cutter is worn", loc="left")
fig.tight_layout()
fig.savefig(OUT / "currents_one_cycle.png", dpi=160)

# 2. 40 ms of raw vibration: the tooth hits.
fig, axes = plt.subplots(2, 1, figsize=(9, 4.8), sharex=True, sharey=True)
for ax, (k, color) in zip(axes, (("new", NEW), ("worn", WORN))):
    s = sig[k]
    idx = np.flatnonzero(s["cutting_vib"])
    start = idx[len(idx) // 2]
    n = int(0.040 * 25000)
    seg = s["vib"][ACC][start : start + n]
    tt = np.arange(n) / 25.0  # ms
    ax.plot(tt, seg - seg.mean(), color=color, lw=0.9)
    for m in np.arange(0, 40, 1000 / TOOTH_HZ):
        ax.axvline(m, color="grey", lw=0.4, alpha=0.5)
    ax.set_title(label[k], loc="left", fontsize=9)
    ax.set_ylabel("m/s²")
axes[1].set_xlabel("milliseconds (grey lines: one tooth every 4.69 ms = 213 hits per second)")
fig.suptitle("Vibration of the table during 40 ms of cutting (about 2 turns of the cutter)", x=0.01, ha="left")
fig.tight_layout()
fig.savefig(OUT / "vibration_tooth_hits.png", dpi=160)

# 3. Vibration spectrum: which rhythms are present.
fig, ax = plt.subplots(figsize=(9, 4.2))
for k, color in (("new", NEW), ("worn", WORN)):
    s = sig[k]
    x = s["vib"][ACC][s["cutting_vib"]]
    f, p = welch(x - x.mean(), fs=25000, nperseg=16384)
    keep = f <= 1100
    ax.semilogy(f[keep], p[keep], color=color, lw=1, label=label[k])
for order in range(1, 21):
    hz = order * SPINDLE_HZ
    ax.axvline(hz, color="#8a96a0" if order % 4 else "#1b2228", lw=0.6 if order % 4 else 1, ls=":" if order % 4 else "-", alpha=0.6)
ax.text(SPINDLE_HZ, ax.get_ylim()[1], " 53 Hz\n once per turn", va="top", fontsize=8)
ax.text(TOOTH_HZ, ax.get_ylim()[1], " 213 Hz\n tooth hits", va="top", fontsize=8)
ax.set_xlabel("frequency (Hz)   solid lines: tooth rhythm and its multiples   dotted: once-per-turn multiples")
ax.set_ylabel("vibration power")
ax.legend(frameon=False, loc="lower left")
ax.set_title("What the table 'hears' while cutting", loc="left")
fig.tight_layout()
fig.savefig(OUT / "vibration_spectrum.png", dpi=160)
