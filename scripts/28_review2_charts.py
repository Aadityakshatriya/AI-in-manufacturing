"""Charts for the Review 2 deck, drawn at slide size from the saved results (no training).

One style for every chart: off-white ground, one blue for our model, grey for the others, orange for
breakage; labels only where they carry the point. Writes results/figures/review2/*.png.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from toollife.features import load_cycle

OUT = ROOT / "results" / "figures" / "review2"
OUT.mkdir(parents=True, exist_ok=True)
BG, INK, INK2, GRID, GREY = "#FAFAF8", "#1C2430", "#4F5B66", "#E3E6E8", "#B4BCC4"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({
    "font.family": "Helvetica Neue", "font.size": 15, "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": GREY, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK,
    "figure.facecolor": BG, "axes.facecolor": BG, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.9,
    "axes.axisbelow": True, "axes.titlesize": 16, "axes.titleweight": "regular",
})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=200, facecolor=BG)
    plt.close(fig)


def lives():
    ph = pd.read_parquet(ROOT / "data" / "processed" / "rzeszow_physics.parquet")
    t = ph.groupby("tool").agg(life=("life", "first"), rdoc=("rdoc_mm", "first"), holder=("holder_mm", "first")).reset_index()
    t = t.sort_values("life")
    col = [GREY if r.tool == 11 else AQUA if r.holder == 160 else ORANGE if r.rdoc == 8 else BLUE for r in t.itertuples()]
    fig, ax = plt.subplots(figsize=(9.6, 6.4))
    y = np.arange(len(t))
    ax.barh(y, t.life, color=col, height=0.66)
    for yi, v in zip(y, t.life):
        ax.text(v + 2, yi, str(v), va="center", fontsize=13, color=INK)
    ax.set_yticks(y, [f"cutter {x}" for x in t.tool], fontsize=12.5)
    ax.set_xlabel("cycles until it broke")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, 170)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="4.5 mm bite"), Patch(color=ORANGE, label="8 mm bite"),
                       Patch(color=AQUA, label="long holder")], frameon=False, loc="lower right", fontsize=13)
    save(fig, "lives.png")


def one_cycle():
    d = load_cycle("P012_F01_C4")
    t, cut = d["t_cur"], d["cutting_cur"]
    v = d["vib"]["X Driving axle +Z"]
    tv = np.arange(len(v)) * 4e-5 + t[0]
    fig, ax = plt.subplots(2, 1, figsize=(9.6, 5.6), sharex=True)
    edges = np.flatnonzero(np.diff(np.r_[0, cut.astype(int), 0]))
    spans = [(s, e) for s, e in zip(t[edges[::2]], t[np.minimum(edges[1::2], len(t) - 1)]) if e - s > 2]
    for a in ax:
        for s, e in spans:
            a.axvspan(s, e, color=BLUE, alpha=0.10, lw=0)
    ax[0].plot(t, d["spindle"], color=INK, lw=1.2)
    ax[0].set_ylabel("spindle current (A)")
    nb = 500
    vv = v[: len(v) // nb * nb].reshape(-1, nb)
    tb = tv[: len(v) // nb * nb].reshape(-1, nb).mean(1)
    ax[1].fill_between(tb, vv.min(1), vv.max(1), color=ORANGE, lw=0, alpha=0.85)
    ax[1].set_ylabel("vibration (m/s²)")
    ax[1].set_xlabel("seconds in the recording")
    s0, e0 = spans[0]
    ax[0].text((s0 + e0) / 2, 4.6, "cutting: 27 s of 115 s", ha="center", fontsize=13, color=BLUE)
    ax[0].set_ylim(0, 8.5)
    save(fig, "one_cycle.png")


def features():
    ph = pd.read_parquet(ROOT / "data" / "processed" / "rzeszow_physics.parquet")
    ph = ph[~ph.tool.isin([10, 11])]
    fig, ax = plt.subplots(1, 2, figsize=(9.6, 4.6), sharey=True)
    for a, (c, lab) in zip(ax, (("table_cut_a__rel", "table motor current"), ("X_Driving_axle_pZ__hiband_rms__rel", "high-pitched vibration"))):
        grid = np.linspace(0.02, 1, 50)
        curves = []
        for _, g in ph.sort_values("age").groupby("tool"):
            x, y = ((g.age + 1) / g.life).to_numpy(), g[c].to_numpy()
            a.plot(x, y, color=GREY, lw=0.8, alpha=0.8)
            curves.append(np.interp(grid, x, y))
        a.plot(grid, np.median(curves, 0), color=BLUE, lw=3)
        a.axhline(1, color=INK2, lw=0.8, ls=":")
        a.set_title(lab, loc="left")
        a.set_xlabel("fraction of life used")
        a.set_ylim(0.4, 4)
    ax[0].set_ylabel("÷ value when new")
    ax[0].text(0.04, 3.55, "blue: median of 12 cutters", fontsize=12.5, color=BLUE)
    save(fig, "features.png")


def tcn_diagram():
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    ax.axis("off")
    n, dx = 16, 1.0
    ys = {0: 0, 1: 1.3, 2: 2.6, 4: 3.9, 8: 5.2}
    for t in range(n + 3):
        fut = t >= n
        ax.add_patch(plt.Rectangle((t * dx - 0.32, -0.32), 0.64, 0.64, fill=not fut, fc="white", ec=GREY if fut else INK2, lw=1.2, ls="--" if fut else "-"))
    need, layers = {n - 1}, [8, 4, 2, 1]
    cone = []
    for d in layers:
        cone.append((d, set(need)))
        need = {tau - k * d for tau in need for k in (0, 1, 2) if tau - k * d >= 0}
    for d, nodes in cone:
        y, yb = ys[d], ys[{8: 4, 4: 2, 2: 1, 1: 0}[d]]
        for t in range(n):
            ax.plot(t * dx, y, "o", color=GRID, ms=6)
        for tau in nodes:
            for k in (0, 1, 2):
                s = tau - k * d
                if s >= 0:
                    ax.plot([tau * dx, s * dx], [y - 0.1, yb + (0.34 if yb == 0 else 0.1)], color=BLUE, lw=1.1, alpha=0.8)
            ax.plot(tau * dx, y, "o", color=BLUE, ms=8)
        ax.text(-1.1, y, f"{d}", ha="right", va="center", fontsize=15, color=BLUE)
    ax.text(-1.1, 6.1, "looks back", ha="right", fontsize=12.5, color=INK2)
    ax.plot([(n - 1) * dx + 0.5] * 2, [-0.45, 5.7], color=ORANGE, lw=1.4, ls="--")
    ax.text((n - 1) * dx + 0.5, -1.05, "now", ha="center", fontsize=13, color=ORANGE)
    ax.text(0, -1.0, "one cycle = 29 numbers", fontsize=12.5, color=INK2)
    ax.text(n + 0.6, -1.0, "future: never used", fontsize=12.5, color=INK2)
    ax.set_xlim(-2.6, n + 3.2)
    ax.set_ylim(-1.5, 6.6)
    save(fig, "tcn.png")


def loco_grid():
    tools = [2, 3, 4, 5, 6, 7, 8, 9, 10, 101, 102, 103, 105]
    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    for i in range(13):
        for j in range(13):
            ax.add_patch(plt.Rectangle((j, 12 - i), 0.88, 0.8, color=ORANGE if i == j else BLUE, alpha=1 if i == j else 0.45, lw=0))
    ax.set_xlim(-0.2, 13)
    ax.set_ylim(-0.4, 13.2)
    ax.set_xticks(np.arange(13) + 0.44, tools, fontsize=10.5)
    ax.set_yticks(np.arange(13) + 0.4, [f"test {13 - k}" for k in range(13)], fontsize=10.5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(False)
    ax.set_xlabel("cutter", fontsize=13)
    save(fig, "loco.png")


def splits():
    rng = np.random.default_rng(1)
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    lg = pd.read_csv(ROOT / "results" / "models" / "split_comparison_lgbm.csv")
    tc = pd.read_csv(ROOT / "results" / "models" / "split_comparison_tcn.csv")
    rows = [("random 70/30 of cycles", lg[lg.split == "rows 70/30"].whole, ORANGE),
            ("70/30 by cutter (20 splits)", tc[tc.split == "cutters 70/30"].whole, GREY),
            ("hide one cutter, 13 times", tc[tc.split == "leave one out"].whole, BLUE)]
    for y, (lab, v, col) in enumerate(rows):
        v = v.to_numpy()
        if len(v) == 1:
            ax.plot(v, [y], "D", ms=13, color=col)
            ax.text(v[0] + 1.3, y, f"{v[0]:.1f}", va="center", fontsize=14, color=INK)
        else:
            ax.scatter(v, y + rng.uniform(-0.16, 0.16, len(v)), s=55, color=col, edgecolor=BG, lw=0.8)
            ax.text(v.max() + 1.3, y, f"{v.min():.1f}–{v.max():.1f}", va="center", fontsize=14, color=INK)
    ax.set_yticks(range(3), [r[0] for r in rows], fontsize=14)
    ax.set_ylim(2.6, -0.6)
    ax.set_xlim(0, 46)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("average error in cycles left (lower is better)")
    save(fig, "splits.png")


def results():
    cs = pd.read_csv(ROOT / "results" / "models" / "comparison_summary.csv").set_index("model")
    pick = [("Average life at this age", "Zoo: Mean residual life (age only)"),
            ("TCN, no sensors (age only)", "Zoo: TCN on age only"),
            ("Survival model, settings only", "Survival model: settings + age"),
            ("LightGBM, 120 summaries", "LightGBM: 120 summaries only"),
            ("LSTM", "Zoo: LSTM"),
            ("Transformer", "Zoo: Causal transformer"),
            ("TCN, physics features (ours)", "TCN: physics features")]
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    y = np.arange(len(pick))
    w = [cs.loc[k, "whole_life"] for _, k in pick]
    l = [cs.loc[k, "last20"] for _, k in pick]
    col = [BLUE if "ours" in lab else GREY for lab, _ in pick]
    ax.barh(y - 0.19, w, height=0.36, color=col)
    ax.barh(y + 0.19, l, height=0.36, color=col, alpha=0.45)
    for yi, a, b in zip(y, w, l):
        ax.text(a + 0.6, yi - 0.19, f"{a:.1f}", va="center", fontsize=12.5, color=INK)
        ax.text(b + 0.6, yi + 0.19, f"{b:.1f}", va="center", fontsize=12.5, color=INK2)
    ax.set_yticks(y, [p[0] for p in pick], fontsize=13.5)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, 42)
    ax.set_xlabel("average error in cycles left on unseen cutters (lower is better)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=GREY, label="whole life"), Patch(color=GREY, alpha=0.45, label="last 20% of life")],
              frameon=False, loc="lower right", fontsize=12.5)
    save(fig, "results.png")


def replay():
    p = pd.read_parquet(ROOT / "results" / "predictions" / "history_physics.parquet")
    g = p[p.tool == 103].sort_values("run_idx")
    x = g.run_idx + 1
    fig, ax = plt.subplots(figsize=(8.0, 5.2))
    ax.plot(x, g.rul, color=INK, lw=2.2, label="true cycles left")
    ax.plot(x, g.rul_q50, color=BLUE, lw=2.2, label="predicted (middle)")
    ax.axvline(47, color=AQUA, lw=2.2)
    ax.text(46, 92, "rule changes\nthe cutter\n(cycle 47)", ha="right", va="top", fontsize=12.5, color=INK)
    ax.axvline(60, color=ORANGE, lw=1.6, ls="--")
    ax.text(59.3, 92, "broke at 60", ha="right", va="top", fontsize=12.5, color=ORANGE)
    ax.set_xlabel("cycle")
    ax.set_ylabel("cycles left")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, loc="lower left", fontsize=12.5)
    save(fig, "replay103.png")


def decisions():
    s = pd.read_csv(ROOT / "results" / "decisions" / "single_cutter.csv")
    s = s[s.cost == "india_typical"]
    pick = lambda src, pol: s[(s.source == src) & (s.policy == pol)].iloc[0]
    rows = [("Run until it breaks", pick("history_physics", "never"), GREY),
            ("Change every N cycles", pick("history_physics", "fixed"), GREY),
            ("Our rule, settings-only model", pick("weibull_settings_age", "dp"), GREY),
            ("Our rule, TCN (sensors)", pick("history_physics", "dp"), BLUE),
            ("Perfect knowledge", pick("history_physics", "oracle"), "#DDE1E5")]
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    y = np.arange(len(rows))
    v = [r[1].cost_per_good for r in rows]
    ax.barh(y, v, color=[r[2] for r in rows], height=0.6)
    for yi, (lab, r, _) in zip(y, rows):
        ax.text(r.cost_per_good + 1.5, yi, f"₹{r.cost_per_good:.0f}   ·   {int(r.breakages)} of 13 broke", va="center", fontsize=13, color=INK)
    ax.set_yticks(y, [r[0] for r in rows], fontsize=13.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 175)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("cost per good cycle, ₹ (lower is better)")
    save(fig, "decisions.png")


def risk_curves():
    p = pd.read_parquet(ROOT / "results" / "predictions" / "history_physics.parquet")
    c = p[p.tool == 103].sort_values("run_idx")
    hc = sorted([x for x in p.columns if x.startswith("hazard_")], key=lambda s: int(s.split("_")[1]))
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.2), sharey=True)
    for ax, cyc in zip(axes, (6, 31, 51)):
        row = c[c.run_idx == cyc - 1].iloc[0]
        h = row[hc].to_numpy(float)
        pk = h * np.cumprod(np.r_[1, 1 - h[:-1]])
        ax.bar(np.arange(1, 61), pk, width=0.85, color=BLUE)
        ax.axvline(int(row.rul), color=ORANGE, lw=1.6, ls="--")
        ax.text(int(row.rul) + 1.2, 0.9, f"broke {int(row.rul)}\ncycles later", color=ORANGE, fontsize=12, va="top")
        ax.set_title(f"after cycle {cyc}", loc="left")
        ax.set_xlabel("cycles from now")
        ax.set_xlim(0, 61)
        ax.set_ylim(0, 1)
    axes[0].set_ylabel("chance of breaking\non that cycle")
    save(fig, "risk103.png")


if __name__ == "__main__":
    for f in (lives, one_cycle, features, tcn_diagram, loco_grid, splits, results, replay, decisions, risk_curves):
        f()
    print("written to", OUT)
