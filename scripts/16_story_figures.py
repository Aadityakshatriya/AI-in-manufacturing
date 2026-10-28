"""Figures for the slides and results page, from the saved results (no training).

  replay_cutters.png   predicted vs true cycles left for three held-out cutters, with where the
                       fixed interval and our decision rule would have changed the cutter
  models.png           remaining-life error of each model, overall and in the last 20% of life
  settings_vs_sensors.png  settings alone vs sensors: on 12 ordinary cutters by stage of life, and on cutter 10
  zoo.png              every model we tried, grouped by family, on the same rows (zoo_slide.png: 16:9)
  cross_dataset.png    our cutters' life-fraction error by what the model was trained on
  decisions.png        cost per good cycle at typical Indian costs, and breakages
  learning_curve.png   the TCN's error when it learns from 4, 6, 9 or all 12 training cutters
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
fig.legend(handles, labels_, frameon=False, fontsize=10, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.01))
fig.subplots_adjust(bottom=0.2)
fig.suptitle("Dotted line: where the cutter really broke. Coloured lines: where each rule would have changed it.", x=0.01, ha="left", fontsize=10, color=INK2)
fig.tight_layout(rect=(0, 0.07, 1, 1))
for o in OUTS:
    fig.savefig(o / "replay_cutters.png", dpi=170, facecolor=SURFACE)
plt.close(fig)

# 2. Model comparison, all models on the same rows (results/models/comparison_summary.csv).
cmp = pd.read_csv(ROOT / "results" / "models" / "comparison_summary.csv").set_index("model")
order = ["Survival model: settings + age", "TCN: settings + age only", "LightGBM: same inputs as the TCN",
         "TCN: physics + autoencoder", "TCN: autoencoder health score", "LightGBM: 120 summaries only", "TCN: physics features"]
tab = cmp.reindex([m for m in order if m in cmp.index])
fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.4), sharey=True)
y = np.arange(len(tab))
for ax, col, title in ((axes[0], "whole_life", "Average error over the whole life"), (axes[1], "last20", "Average error in the last 20% of life")):
    colors = [BLUE if m == "TCN: physics features" else "#9ec5f4" for m in tab.index]
    ax.barh(y, tab[col], color=colors, height=0.6)
    for yi, v in zip(y, tab[col]):
        ax.text(v + 0.4, yi, f"{v:.1f}", va="center", color=INK, fontsize=10)
    ax.set_title(title, loc="left", fontsize=11)
    ax.set_xlabel("cycles (lower is better)")
    ax.grid(axis="y", visible=False)
axes[0].set_yticks(y, tab.index)
fig.suptitle("Remaining-life error on cutters hidden from training (13 cutters, same rows for every model)", x=0.01, ha="left", fontsize=12)
save(fig, "models.png")

# 2b. Settings vs sensors: on cutters whose settings were seen in training, and on the one that was not.
pcc = pd.read_csv(ROOT / "results" / "models" / "comparison_per_cutter.csv")
NOSENS, SENS = "Survival model: settings + age", "TCN: physics features"
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.3), gridspec_kw={"width_ratios": [1.5, 1]})
stages = [("first_third", "first third\nof life"), ("middle_third", "middle\nthird"), ("last_third", "last\nthird"), ("last20", "last 20%\nof life")]
x = np.arange(len(stages))
for i, (m, color, label) in enumerate(((NOSENS, "#c9c8c3", "settings + age, no sensors (survival model)"), (SENS, BLUE, "TCN with sensor features"))):
    g = pcc[(pcc["model"] == m) & (pcc["tool"] != 10)]
    vals = [g[c].mean() for c, _ in stages]
    a1.bar(x + (i - 0.5) * 0.36, vals, width=0.34, color=color, label=label)
    for xi, v in zip(x, vals):
        a1.text(xi + (i - 0.5) * 0.36, v + 0.5, f"{v:.0f}", ha="center", fontsize=10, color=INK)
a1.set_xticks(x, [l for _, l in stages])
a1.set_ylabel("average error, cycles")
a1.legend(frameon=False, fontsize=9, loc="upper right")
a1.set_title("12 cutters whose settings appear in training:\nsettings explain most of the life; sensors help near the end", loc="left", fontsize=11)
a1.grid(axis="x", visible=False)
c10 = [(NOSENS, "settings + age\n(survival model)", "#c9c8c3"), ("TCN: settings + age only", "settings + age\n(TCN)", "#c9c8c3"),
       (SENS, "TCN, sensor\nfeatures", BLUE), ("Zoo: TCN on the 120 summaries", "TCN, 120 sensor\nsummaries", "#9ec5f4")]
vals = [pcc[(pcc["model"] == m) & (pcc["tool"] == 10)]["whole_life"].iloc[0] for m, _, _ in c10]
a2.bar(range(len(c10)), vals, color=[c for _, _, c in c10], width=0.6)
for xi, v in enumerate(vals):
    a2.text(xi, v + 2, f"{v:.0f}", ha="center", fontsize=10, color=INK)
a2.set_xticks(range(len(c10)), [l for _, l, _ in c10], fontsize=9)
a2.set_title("Cutter 10, the only one on the long holder\n(a setting never seen in training): only sensors cope", loc="left", fontsize=11)
a2.grid(axis="x", visible=False)
save(fig, "settings_vs_sensors.png")

# 2c. The model zoo: every model on the same rows, grouped by family. The TCN on physics features was
# chosen before the zoo was run; we did not switch to whichever came out best on the test cutters.
GROUPS = ["No sensors", "Classical ML, TCN inputs", "120 released summaries", "Neural networks, TCN inputs",
          "TCN, other inputs", "Raw vibration, end to end"]
z = cmp[cmp["group"].isin(GROUPS)].copy()
z["label"] = z.index.str.removeprefix("Zoo: ")
XMAX = max(z["whole_life"].max(), z["last20"].max()) * 1.12
spread = ROOT / "results" / "models" / "zoo_seed_spread.csv"
sp = pd.read_csv(spread) if spread.exists() else None
if sp is not None:
    sp = sp[(sp["name"] == "tcn") & sp["model"].str.startswith("seed")]


def draw_zoo(ax, groups, fontsize=9.5):
    rows_, ys, y = [], [], 0
    for g in groups:
        part = z[z["group"] == g].sort_values("whole_life")
        if part.empty:
            continue
        rows_.append(("header", g, None)); ys.append(y); y += 1
        for m, r in part.iterrows():
            rows_.append(("model", m, r)); ys.append(y); y += 1
        y += 0.4
    if sp is not None:
        lo, hi = sp["mae_whole_life"].min(), sp["mae_whole_life"].max()
        ax.axvspan(lo, hi, color=BLUE, alpha=0.08, lw=0)
        ax.text(lo - 0.3, -0.9, f"our TCN with one random start: {lo:.1f}–{hi:.1f}", color=BLUE, fontsize=fontsize - 0.5, va="center", ha="right")
    ax.axvline(cmp.loc["TCN: physics features", "whole_life"], color=BLUE, lw=1, ls=":")
    ticks, labels = [], []
    for (kind, m, r), yy in zip(rows_, ys):
        if kind == "header":
            ax.text(0, yy, m.upper(), fontsize=fontsize, fontweight="bold", color=INK2, va="center")
            continue
        ours = m == "TCN: physics features"
        ax.barh(yy, r["whole_life"], height=0.62, color=BLUE if ours else "#9ec5f4")
        ax.plot(r["last20"], yy, "o", ms=6, color=INK, mec=SURFACE, mew=1.5)
        ax.text(max(r["whole_life"], r["last20"]) + 0.6, yy, f"{r['whole_life']:.1f}", va="center", fontsize=fontsize - 0.5, color=INK)
        ticks.append(yy)
        labels.append("★ TCN, physics features (ours)" if ours else r["label"])
    ax.set_yticks(ticks, labels, fontsize=fontsize)
    ax.set_ylim(y, -1.5)
    ax.set_xlim(0, XMAX)
    ax.grid(axis="y", visible=False)
    return y


XLABEL = "average error in cycles left: bars over the whole life, dots in the last 20% of life (lower is better)"
TITLE = "Every model we tried, on the same 13 hidden cutters. The TCN was chosen before this comparison."
# Tall version for the web page.
n_rows = len(z) + len(GROUPS) * 1.4
fig, ax = plt.subplots(figsize=(13, 0.34 * n_rows + 1.6))
draw_zoo(ax, GROUPS)
ax.set_xlabel(XLABEL)
ax.set_title(TITLE, loc="left", fontsize=11.5)
save(fig, "zoo.png")
# Two columns for a 16:9 slide.
fig, axes = plt.subplots(1, 2, figsize=(19.2, 10.2))
for ax, groups in zip(axes, (GROUPS[:3], GROUPS[3:])):
    draw_zoo(ax, groups, fontsize=11)
    ax.set_xlabel("average error, cycles (lower is better)", fontsize=11)
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
axes[1].legend(handles=[Patch(color="#9ec5f4", label="whole life"),
                        Line2D([], [], marker="o", ls="", color=INK, label="last 20% of life")],
               loc="upper right", frameon=False, fontsize=11)
fig.suptitle(TITLE, x=0.01, ha="left", fontsize=14)
save(fig, "zoo_slide.png")

# 3. Cross-dataset transfer.
cd = pd.read_csv(ROOT / "results" / "cross_dataset" / "summary.csv")
ours = cd[cd.dataset == "rzeszow"]
order = ["ours: trained on ours only", "ours: trained on other machines only", "ours: trained on ours + other machines"]
labels = ["Our cutters only", "Four other factories only\n(never saw our machine)", "Ours + four other factories"]
vals = [ours[ours.setting == s].mae.iloc[0] for s in order]
# Median over cutters (as in PROJECT_EXPLAINED.md); summary.csv holds the mean, which one bad cutter drags down.
pcd = pd.read_csv(ROOT / "results" / "cross_dataset" / "per_cutter.csv")
rhos = [pcd[(pcd.setting == s) & (pcd.dataset == "rzeszow")].rho.median() for s in order]
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.barh(range(3), vals, color=[ "#9ec5f4", BLUE, "#9ec5f4"], height=0.55)
for i, (v, r) in enumerate(zip(vals, rhos)):
    ax.text(v + 0.003, i, f"{v:.3f}   (rises with wear: {r:.2f})", va="center", fontsize=10, color=INK)
ax.axvline(0.25, color=MUTED, ls=":", lw=1)
ax.text(0.252, -0.45, "always guessing 0.5", color=INK2, fontsize=9, va="center")
ax.set_yticks(range(3), labels)
ax.invert_yaxis()
ax.set_xlim(0, 0.33)
ax.set_xlabel("error in fraction of life used, on our 13 cutters (lower is better)\n\"rises with wear\": rank correlation with life used, median cutter (1 = perfectly)")
ax.set_title("What other machines teach transfers to ours", loc="left", fontsize=12)
ax.grid(axis="y", visible=False)
save(fig, "cross_dataset.png")

# 4. Decisions at typical Indian costs. "Our rule" is the exact DP with g from the costs (policy "dp"),
# the same rule for every model. The grid-tuned variant ("dp_tuned") was dropped: with 12 training
# cutters its tuned g was unstable (17 to 9,500) and on two cutters it changed a new cutter after one cycle.
s_all = pd.read_csv(ROOT / "results" / "decisions" / "single_cutter.csv")
s_all = s_all[s_all.cost == "india_typical"]
pick = lambda src, pol: s_all[(s_all.source == src) & (s_all.policy == pol)].iloc[0]
fixed = pick("history_physics", "fixed")
rows = [
    ("Run until it breaks", pick("history_physics", "never"), "#d8d7d2"),
    ("Change every N cycles (N tuned on the other cutters)", fixed, "#9ec5f4"),
    ("Change every N, per cutting setting", pick("history_physics", "fixed_group"), "#9ec5f4"),
    ("Our rule, TCN without sensors (settings + age)", pick("history_settings_age", "dp"), "#9ec5f4"),
    ("Our rule, survival model on settings + age", pick("weibull_settings_age", "dp"), "#9ec5f4"),
    ("Our rule, TCN with sensors", pick("history_physics", "dp"), BLUE),
    ("Perfect knowledge (impossible)", pick("history_physics", "oracle"), "#d8d7d2"),
]
fig, ax = plt.subplots(figsize=(11.5, 4.8))
vals = [r[1].cost_per_good for r in rows]
ax.barh(range(len(rows)), vals, color=[r[2] for r in rows], height=0.6)
for i, (_, r, _) in enumerate(rows):
    ax.text(vals[i] + 1, i, f"₹{vals[i]:.0f}   breakages {int(r.breakages)} of 13   life used {r.life_used:.0%}", va="center", fontsize=10, color=INK)
ax.set_yticks(range(len(rows)), [r[0] for r in rows])
ax.invert_yaxis()
ax.set_xlim(0, max(vals) * 1.7)
ax.set_xlabel("cost per good cycle, ₹ (lower is better); replay of 13 real held-out cutters")
ax.set_title("Keep or change: typical Indian shop costs (breakage ≈ 2× a planned change)", loc="left", fontsize=12)
ax.grid(axis="y", visible=False)
save(fig, "decisions.png")

# 5. Learning curve: would more cutters help? (results/models/learning_curve.csv, scripts/24_learning_curve.py)
lc = pd.read_csv(ROOT / "results" / "models" / "learning_curve.csv")
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.fill_between(lc.n_train, lc.whole_life_min, lc.whole_life_max, color=BLUE, alpha=0.15, lw=0)
for col, color, label in (("whole_life", BLUE, "whole life"), ("last20", ORANGE, "last 20% of life")):
    ax.plot(lc.n_train, lc[f"{col}_mean"], "-o", color=color, ms=8, mec=SURFACE, mew=2)
    last = lc.iloc[-1]
    ax.text(last.n_train + 0.25, last[f"{col}_mean"], f"{label}  {last[f'{col}_mean']:.1f}", va="center", color=INK, fontsize=10)
ax.set_xticks(lc.n_train)
ax.set_xlim(3.5, 14.8)
ax.set_ylim(0, None)
ax.set_xlabel("cutters the TCN learned from (band: spread over 3 random picks)")
ax.set_ylabel("error in cycles left (lower is better)")
ax.set_title("Still falling at 12 cutters: more cutter lives would help", loc="left", fontsize=12)
save(fig, "learning_curve.png")
print("figures written")
