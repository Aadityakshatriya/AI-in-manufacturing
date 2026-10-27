"""Physics features for every Rzeszów cycle, plus the Rzeszów part of the common run table.

Needs data/rzeszow_cycles/*.npz from scripts/03_convert_raw.py.
Writes data/processed/rzeszow_physics.parquet (all features, absolute and relative to each cutter's
first cycles) and data/processed/runs_rzeszow.parquet (PLAN.md §6 columns).
"""

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.features import PATH_MM, cycle_features, load_cycle
from toollife.rzeszow import ROOT, load_table

OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)


def one(row: tuple) -> dict:
    file, adoc, rdoc = row
    try:
        feats = cycle_features(load_cycle(file), adoc, rdoc)
    except FileNotFoundError:
        feats = {}
    return {"file": file, **feats}


def main() -> None:
    df = load_table()
    jobs = list(df[["file", "adoc_mm", "rdoc_mm"]].itertuples(index=False, name=None))
    with ProcessPoolExecutor(8) as pool:
        rows = list(pool.map(one, jobs, chunksize=4))
    feats = pd.DataFrame(rows)
    full = df.drop(columns=[c for c in df.columns if c.startswith(("Accelerometer", "Current"))]).merge(feats, on="file")
    full = full.sort_values(["tool", "age"]).reset_index(drop=True)

    # Relative versions: divide by the median of the cutter's first 10% of cycles
    # (at least 3 cycles), skipping cycle-1 files, which include corner clean-up.
    phys = [c for c in feats.columns if c != "file"]
    for tool, g in full.groupby("tool"):
        clean = g[~g["file"].str.endswith("_C1")]
        base_rows = clean.head(max(3, int(np.ceil(0.1 * len(g)))))
        base = base_rows[phys].median()
        full.loc[g.index, [f"{c}__rel" for c in phys]] = (g[phys] / base.replace(0, np.nan)).to_numpy()
    full.to_parquet(OUT / "rzeszow_physics.parquet")

    # Common run table (PLAN.md §6).
    vol = full["adoc_mm"] * full["rdoc_mm"] * full["rdoc_mm"].map(PATH_MM)
    runs = pd.DataFrame(
        {
            "dataset": "rzeszow",
            "tool": full["tool"].astype(str),
            "run_idx": full["age"],
            "end_type": "break",
            "cum_time_s": full.groupby("tool")["cut_seconds"].cumsum(),
            "cum_volume_mm3": vol.groupby(full["tool"]).cumsum(),
            "rul_native": full["rul"],
            "rul_unit": "cycles",
            "machine": "haas_vf1",
            "adoc_mm": full["adoc_mm"],
            "rdoc_mm": full["rdoc_mm"],
            "holder_mm": full["holder_mm"],
            "hardness_hrc": full["hardness_hrc"],
            "tool_type": full["tool_type"],
            "spindle_load_rel": full["spindle_net_a__rel"],
            "spindle_load_abs": full["spindle_net_a"],
            "table_load_rel": full["table_cut_a__rel"],
            "energy_per_mm3_rel": full["spindle_charge_per_mm3__rel"],
        }
    )
    # Fraction of life used, on the cycle clock: every cycle is one lap of similar length, and
    # counting cycles handles the few cycles that were never recorded. 1.0 = the breaking cycle.
    runs["life_frac"] = (full["age"] + 1) / full["life"]
    runs.to_parquet(OUT / "runs_rzeszow.parquet")
    print(full[phys].notna().mean().round(2).to_string())
    print(runs.groupby("tool")[["spindle_load_rel", "table_load_rel", "energy_per_mm3_rel"]].last().round(2))


if __name__ == "__main__":
    main()
