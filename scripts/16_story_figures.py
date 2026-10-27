"""Figures for the slides and results page, from the saved results (no training).

  replay_cutters.png   predicted vs true cycles left for three held-out cutters, with where the
                       fixed interval and our decision rule would have changed the cutter
  models.png           remaining-life error of each model, overall and in the last 20% of life
  cross_dataset.png    our cutters' life-fraction error by what the model was trained on
  decisions.png        cost per good cycle at typical Indian costs, and breakages
Writes to results/figures/ and docs/img/results/.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.rzeszow import ROOT

OUTS = [ROOT / "results" / "figures", ROOT / "docs" / "img" / "results"]
for o in OUTS:
    o.mkdir(parents=True, exist_ok=True)

# Reference palette (dataviz skill): fixed categorical order, recessive chrome.
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, SURFACE = "#0b0b0b", "#52514e", "#898781", "#fcfcfb"
plt.rcParams.update({
    "font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.grid": True, "grid.color": "#e6e5e1",
    "grid.linewidth": 0.8, "axes.axisbelow": True, "lines.linewidth": 2,
})


def save(fig, name):
    fig.tight_layout()
    for o in OUTS:
        fig.savefig(o / name, dpi=170, facecolor=SURFACE)
    plt.close(fig)


# 1. Replay of three held-out cutters.
pred = pd.read_parquet(ROOT / "results" / "predictions" / "history_physics.parquet")
dec = pd.read_csv(ROOT / "results" / "decisions" / "single_cutter_per_cutter.csv")
dec = dec[(dec.source == "history_physics") & (dec.cost == "india_typical")]
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=False)
for ax, tool in zip(axes, [103, 7, 8]):
    g = pred[pred.tool == tool].sort_values("run_idx")
    x = g.run_idx + 1
    ax.fill_between(x, g.rul_lower, g.rul_upper, color=BLUE, alpha=0.12, lw=0, label="range (widened on other cutters)")
    ax.plot(x, g.rul, color=INK, lw=2, label="true cycles left")
    ax.plot(x, g.rul_q50, color=BLUE, lw=2, label="model's middle estimate")
    life = int(g.life.iloc[0])
    ax.axvline(life, color=MUTED, lw=1, ls=":")
    notes = []
    for policy, color, label in (("fixed", ORANGE, "Fixed interval"), ("dp", AQUA, "Our rule")):
        r = dec[(dec.tool == tool) & (dec.policy == policy)]
        if not len(r):
            continue
        if bool(r.broke.iloc[0]):
            notes.append(f"{label}: lets it break")
        else:
            stop = int(r.good.iloc[0])
            ax.axvline(stop, color=color, lw=2)
            notes.append(f"{label}: changes at {stop} ({life - stop} cycles early)")
    ax.text(0.98, 0.97, "\n".join(notes), transform=ax.transAxes, ha="right", va="top", fontsize=9, color=INK2,
            bbox=dict(boxstyle="round,pad=0.3", fc=SURFACE, ec="#e6e5e1"))
    ax.set_title(f"Cutter {tool} (hidden from training), life {life} cycles", loc="left", fontsize=11)
    ax.set_xlabel("cycle")
    ax.set_ylim(bottom=0)
axes[0].set_ylabel("cycles left")
from matplotlib.lines import Line2D
handles, labels_ = axes[0].get_legend_handles_labels()
handles += [Line2D([], [], color=ORANGE, lw=2), Line2D([], [], color=AQUA, lw=2)]
labels_ += ["fixed interval changes the cutter", "our rule changes the cutter"]
axes[0].legend(handles, labels_, frameon=False, fontsize=9, loc="lower left")
fig.suptitle("Dotted line: where the cutter really broke. Coloured lines: where each rule would have changed it.", x=0.01, ha="left", fontsize=10, color=INK2)
save(fig, "replay_cutters.png")

# 2. Model comparison.
rows = []
base = pd.read_csv(ROOT / "results" / "baselines" / "per_cutter.csv")
for model, label in (("lgbm_sensors", "LightGBM on sensor summaries (yardstick)"), ("settings_age", "Survival model on settings + age (yardstick)")):
    b = base[base.model == model]
    rows.append((label, b.mae.mean(), b.mae_last20pct.mean()))
for name, label in (("settings_age", "TCN: settings + age"), ("ae", "TCN: autoencoder fingerprint + health"), ("physics_ae", "TCN: physics + autoencoder"), ("physics", "TCN: physics features")):
    m = pd.read_csv(ROOT / "results" / "models" / f"history_{name}.csv")
    rows.append((label, m.mae.mean(), m.mae_last20.mean()))
tab = pd.DataFrame(rows, columns=["model", "all", "last20"])
fig, axes = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True)
y = np.arange(len(tab))
for ax, col, title in ((axes[0], "all", "Average error over the whole life"), (axes[1], "last20", "Average error in the last 20% of life")):
    colors = [BLUE if "physics features" in m else "#9ec5f4" for m in tab.model]
    ax.barh(y, tab[col], color=colors, height=0.6)
    for yi, v in zip(y, tab[col]):
        ax.text(v + 0.4, yi, f"{v:.1f}", va="center", color=INK, fontsize=10)
    ax.set_title(title, loc="left", fontsize=11)
    ax.set_xlabel("cycles (lower is better)")
    ax.grid(axis="y", visible=False)
axes[0].set_yticks(y, tab.model)
axes[0].invert_yaxis()
fig.suptitle("Remaining-life error on cutters hidden from training (13 cutters, each weighted equally)", x=0.01, ha="left", fontsize=12)
save(fig, "models.png")

# 3. Cross-dataset transfer.
cd = pd.read_csv(ROOT / "results" / "cross_dataset" / "summary.csv")
ours = cd[cd.dataset == "rzeszow"]
order = ["ours: trained on ours only", "ours: trained on other machines only", "ours: trained on ours + other machines"]
labels = ["Our cutters only", "Four other factories only\n(never saw our machine)", "Ours + four other factories"]
vals = [ours[ours.setting == s].mae.iloc[0] for s in order]
rhos = [ours[ours.setting == s].rho.iloc[0] for s in order]
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.barh(range(3), vals, color=[ "#9ec5f4", BLUE, "#9ec5f4"], height=0.55)
for i, (v, r) in enumerate(zip(vals, rhos)):
    ax.text(v + 0.003, i, f"{v:.3f}   (rises with wear: {r:.2f})", va="center", fontsize=10, color=INK)
ax.axvline(0.25, color=MUTED, ls=":", lw=1)
ax.text(0.252, -0.45, "always guessing 0.5", color=INK2, fontsize=9, va="center")
ax.set_yticks(range(3), labels)
ax.invert_yaxis()
ax.set_xlim(0, 0.3)
ax.set_xlabel("error in fraction of life used, on our 13 cutters (lower is better)")
ax.set_title("What other machines teach transfers to ours", loc="left", fontsize=12)
ax.grid(axis="y", visible=False)
save(fig, "cross_dataset.png")

# 4. Decisions at typical Indian costs.
s = pd.read_csv(ROOT / "results" / "decisions" / "single_cutter.csv")
s = s[(s.source == "history_physics") & (s.cost == "india_typical")].set_index("policy")
show = [("never", "Run until it breaks"), ("fixed", "Change every N cycles (tuned)"), ("dp", "Our rule (cost of risk vs cost of change)"), ("oracle", "Perfect knowledge (impossible)")]
fig, ax = plt.subplots(figsize=(10, 3.8))
vals = [s.loc[p, "cost_per_good"] for p, _ in show]
cols = ["#9ec5f4", "#9ec5f4", BLUE, "#d8d7d2"]
ax.barh(range(len(show)), vals, color=cols, height=0.55)
for i, (p, _) in enumerate(show):
    ax.text(vals[i] + 1, i, f"₹{vals[i]:.0f}   breakages: {int(s.loc[p, 'breakages'])} of 13", va="center", fontsize=10, color=INK)
ax.set_yticks(range(len(show)), [l for _, l in show])
ax.invert_yaxis()
ax.set_xlim(0, max(vals) * 1.45)
ax.set_xlabel("cost per good cycle, ₹ (lower is better); replay of 13 real held-out cutters")
ax.set_title("Keep or change: typical Indian shop costs (breakage ≈ 2× a planned change)", loc="left", fontsize=12)
ax.grid(axis="y", visible=False)
save(fig, "decisions.png")
print("figures written")
