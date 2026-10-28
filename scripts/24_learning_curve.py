"""Would more cutters help? The TCN's error when it learns from fewer cutters.

For every hidden cutter, the TCN (physics inputs, the same recipe as scripts/13_train_history.py) is
trained on a random 4, 6 or 9 of the other 12 cutters (three different random draws each) and on
all 12, then tested on the hidden one. If the error is still falling at 12, more cutters would
help; if it has flattened, the limit is the information in the signals, not the amount of data.
Two seeds per model (not five) to keep the run short; the 12-cutter point uses the same two seeds.

Writes results/models/learning_curve.csv (one row per training-set size: mean whole-life and
last-20% error over the 13 hidden cutters, and the spread across draws).
"""

import importlib.util
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from toollife.models.hazard import curves


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SIZES = (4, 6, 9, 12)
DRAWS = 3
SEEDS = 2


def one_fold(held):
    torch.set_num_threads(1)
    th = module("th", "13_train_history.py")
    fc = module("fc", "18_fair_comparison.py")
    df, cols = th.load("physics")
    others = sorted(t for t in df["tool"].unique() if t != held)
    rng = np.random.default_rng(held)
    rows = []
    for n in SIZES:
        for draw in range(1 if n == len(others) else DRAWS):
            train_tools = others if n == len(others) else list(rng.choice(others, n, replace=False))
            r, lg, _ = th.fit_predict(df[df["tool"].isin(train_tools)], df[df["tool"] == held], cols, SEEDS)
            p = r[["tool", "age", "rul", "life"]].assign(pred=curves(lg)["rul_q50"])
            pc = fc.per_cutter(p)
            rows.append(dict(held=held, n_train=n, draw=draw, whole_life=pc["whole_life"].iloc[0], last20=pc["last20"].iloc[0]))
    return rows


def main():
    th = module("th", "13_train_history.py")
    tools = sorted(th.load("settings_age")[0]["tool"].unique())
    with ProcessPoolExecutor(4) as ex:
        rows = [r for rs in ex.map(one_fold, tools) for r in rs]
    raw = pd.DataFrame(rows)
    raw.to_csv(ROOT / "results" / "models" / "learning_curve_raw.csv", index=False)
    # Average over the 13 hidden cutters within each draw, then summarise across draws.
    per_draw = raw.groupby(["n_train", "draw"])[["whole_life", "last20"]].mean()
    out = per_draw.groupby("n_train").agg(["mean", "min", "max"]).round(2)
    out.columns = ["_".join(c) for c in out.columns]
    out.to_csv(ROOT / "results" / "models" / "learning_curve.csv")
    print(out.to_string())


if __name__ == "__main__":
    main()
