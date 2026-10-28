"""Is the signal rise wear, or just where the cutter is in the block?

Inside a layer the rings get smaller towards the middle, so a signal could change with ring position
rather than with wear. For each cutter we remove the straight-line effect of ring number from both
the signal and the fraction of life used, then correlate what is left (a partial rank correlation).
If the signals still track life after that, the rise is not a ring-position effect.
Writes results/audit/position_check.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_parquet(ROOT / "data" / "processed" / "rzeszow_physics.parquet")
df = df[df["tool"] != 11].copy()
df["ring"] = df["file"].str.extract(r"_C(\d+)$").astype(int)
df["life_frac"] = (df["age"] + 1) / df["life"]

rows = []
for feature, label in (("table_cut_a", "table motor current"), ("spindle_net_a", "spindle current above idle"),
                       ("X_Driving_axle_pZ__rms", "table vibration")):
    for tool, g in df.groupby("tool"):
        if len(g) < 10:
            continue
        X = np.column_stack([np.ones(len(g)), g["ring"]])
        resid = lambda y: y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
        rows.append(dict(signal=label, tool=tool,
                         with_life=spearmanr(g[feature], g["life_frac"]).statistic,
                         with_ring=spearmanr(g[feature], g["ring"]).statistic,
                         with_life_after_removing_ring=spearmanr(resid(g[feature]), resid(g["life_frac"])).statistic))
out = pd.DataFrame(rows)
out.to_csv(ROOT / "results" / "audit" / "position_check.csv", index=False)
print(out.groupby("signal")[["with_life", "with_ring", "with_life_after_removing_ring"]].mean().round(2).to_string())
sys.exit(0)
