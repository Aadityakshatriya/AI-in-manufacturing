"""Figure: the autoencoder's health score over each cutter's life, scored by the autoencoder that never heard it."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.rzeszow import ROOT, load_table

GROUPS = {1: [2, 7, 101], 2: [3, 8, 102], 3: [4, 9, 103], 4: [5, 10], 5: [6, 105]}
meta = load_table()[["file", "tool", "age", "life"]]
fig, ax = plt.subplots(figsize=(9, 4.8))
for g, tools in GROUPS.items():
    ae = pd.read_parquet(ROOT / "data" / "processed" / f"ae_g{g}.parquet").merge(meta, on="file")
    for t in tools:
        d = ae[(ae.tool == t) & ~ae.file.str.endswith("_C1")].sort_values("age")
        rel = d.health / d.health.head(3).median()
        style = dict(color="#b4321f", lw=2, label="cutter 10 (long holder, shook from the start)") if t == 10 else dict(color="#2f4a5c", lw=1, alpha=0.6)
        ax.plot((d.age + 1) / d.life, rel, **style)
ax.set_yscale("log")
ax.axhline(1, color="grey", lw=0.6)
ax.set_xlabel("fraction of the cutter's life used")
ax.set_ylabel("rebuild error ÷ error when new (log scale)")
ax.set_title("The autoencoder learned healthy cutting; on cutters it never heard,\nits rebuild error grows as they wear", loc="left")
ax.legend(frameon=False, loc="upper left")
fig.tight_layout()
out = ROOT / "results" / "autoencoders" / "health_vs_life.png"
fig.savefig(out, dpi=160)
fig.savefig(ROOT / "docs" / "img" / "health_vs_life.png", dpi=160)
print(out)
