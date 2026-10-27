"""Audit of the Rzeszów dataset: cutter lifetimes, settings, and which sensors trend with wear.

Writes figures and tables to results/audit/.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.rzeszow import ROOT, load_table, sensor_columns, usable

OUT = ROOT / "results" / "audit"
OUT.mkdir(parents=True, exist_ok=True)

df = load_table()
tools = (
    df.groupby("tool")
    .agg(
        life=("life", "first"),
        recorded=("cycle", "size"),
        tool_type=("tool_type", "first"),
        adoc_mm=("adoc_mm", "first"),
        rdoc_mm=("rdoc_mm", "first"),
        holder_mm=("holder_mm", "first"),
        hardness_hrc=("hardness_hrc", "mean"),
    )
    .sort_values("life")
)
tools.to_csv(OUT / "cutters.csv")

# Figure 1: how long each cutter lasted, coloured by the setting that matters most.
fig, ax = plt.subplots(figsize=(9, 4.5))
colors = np.where(tools["holder_mm"] == 160, "#b4321f", np.where(tools["rdoc_mm"] == 8, "#c2410c", "#2f4a5c"))
ax.barh([f"cutter {t}" for t in tools.index], tools["life"], color=colors)
for i, (life, a) in enumerate(zip(tools["life"], tools["adoc_mm"])):
    ax.text(life + 1, i, f"{life}  (depth {a} mm)", va="center", fontsize=8)
ax.set_xlabel("cycles until the cutter broke")
ax.set_title("Cutter lifetimes in the Rzeszów data")
from matplotlib.patches import Patch

ax.legend(
    handles=[
        Patch(color="#2f4a5c", label="sideways cut 4.5 mm, holder 80 mm"),
        Patch(color="#c2410c", label="sideways cut 8 mm, holder 80 mm"),
        Patch(color="#b4321f", label="holder 160 mm"),
    ],
    loc="lower right",
    fontsize=8,
)
fig.tight_layout()
fig.savefig(OUT / "cutter_lifetimes.png", dpi=150)

# Which sensor summaries move with wear? Spearman correlation with fraction of life used,
# computed inside each cutter (so differences between cutters do not count), then averaged.
u = usable(df)
cols = sensor_columns(u)
per_tool = []
for t, g in u.groupby("tool"):
    if len(g) < 10:
        continue
    r = g[cols].rank().corrwith(g["life_frac_used"].rank())
    per_tool.append(r.rename(t))
corr = pd.concat(per_tool, axis=1)
summary = pd.DataFrame(
    {
        "mean_within_cutter_spearman": corr.mean(axis=1),
        "cutters_same_sign": (np.sign(corr).eq(np.sign(corr.mean(axis=1)), axis=0)).sum(axis=1),
        "n_cutters": corr.notna().sum(axis=1),
    }
).sort_values("mean_within_cutter_spearman", key=np.abs, ascending=False)
summary.to_csv(OUT / "sensor_trend_with_wear.csv")

# Figure 2: the strongest trending summaries plotted over each cutter's life.
top = summary.index[:6]
fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharex=True)
for ax, col in zip(axes.flat, top):
    for t, g in u.groupby("tool"):
        z = (g[col] - g[col].iloc[:3].mean()) / (u[col].std() + 1e-9)
        ax.plot(g["life_frac_used"], z, lw=1, alpha=0.8)
    ax.set_title(col.replace("Accelerometer - ", "Acc ").replace("Current - ", "I "), fontsize=9)
    ax.axhline(0, color="grey", lw=0.5)
for ax in axes[1]:
    ax.set_xlabel("fraction of cutter life used")
fig.suptitle("Sensor summaries relative to each cutter's first cycles (one line per cutter)")
fig.tight_layout()
fig.savefig(OUT / "top_trending_sensors.png", dpi=150)

print(tools.to_string())
print()
print(summary.head(15).to_string())
