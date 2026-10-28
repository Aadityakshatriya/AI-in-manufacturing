"""Why "hide one whole cutter" and not a 70/30 split? Run the 70/30 splits and compare.

Three ways to split the same data, scored the same way (average error in cycles left, each test
cutter weighted equally, whole life and last 20% of life):

  rows 70/30     shuffle all cycles, train on 70%, test on 30%. Cycles of the same cutter land on both
                 sides, so the model is tested on near-copies of what it trained on (leak). 20 repeats.
                 Only for a per-cycle model (LightGBM); a sequence model cannot be trained on scattered
                 cycles of a cutter.
  cutters 70/30  9 cutters train, 4 cutters test (whole cutters, no leak). 20 different random splits.
  leave one out  hide one cutter, train on the other 12, repeat for all 13 (what the project uses).

Models: LightGBM on the 120 released summaries (fast, per cycle) and the TCN on physics features
(the project's recipe, 3 random starts instead of 5 to keep the 20 splits affordable).
LightGBM and torch crash in one process on this Mac, so each model runs in its own process:
  python scripts/27_split_comparison.py lgbm
  python scripts/27_split_comparison.py tcn
  python scripts/27_split_comparison.py summary
Writes results/models/split_comparison_<model>.csv and split_comparison.csv.
"""

import importlib.util
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results" / "models"
REPEATS = 20
N_TEST = 4  # of 13 cutters: 9 train / 4 test is the nearest whole-cutter split to 70/30


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def per_cutter(p: pd.DataFrame) -> pd.DataFrame:
    p = p.assign(err=(p["pred"] - p["rul"]).abs(), late=(p["age"] + 1) / p["life"] >= 0.8)
    per = p.groupby("tool").agg(whole=("err", "mean"))
    per["last20"] = p[p.late].groupby("tool")["err"].mean()
    return per


def score(p: pd.DataFrame) -> tuple[float, float]:
    """Average error per test cutter (each counts equally), whole life and last 20% of life."""
    per = per_cutter(p)
    return float(per["whole"].mean()), float(per["last20"].mean())


def cutter_splits(tools):
    rng = np.random.default_rng(27)
    return [sorted(rng.choice(tools, N_TEST, replace=False).tolist()) for _ in range(REPEATS)]


def run_lgbm():
    import lightgbm as lgb
    from toollife.rzeszow import load_table, sensor_columns, usable

    params = dict(n_estimators=400, learning_rate=0.03, num_leaves=15, min_child_samples=20, subsample=0.8,
                  subsample_freq=1, colsample_bytree=0.5, verbose=-1, random_state=0)
    df = usable(load_table())
    df = df[df["rul"] >= 1].drop_duplicates(["tool", "age"]).reset_index(drop=True)
    X = sensor_columns(df)
    fit = lambda tr, te: te[["tool", "age", "rul", "life"]].assign(
        pred=np.clip(lgb.LGBMRegressor(**params).fit(tr[X], tr["rul"]).predict(te[X]), 0, None))
    rows = []
    rng = np.random.default_rng(27)
    for r in range(REPEATS):
        test = rng.random(len(df)) < 0.3
        w, l = score(fit(df[~test], df[test]))
        rows.append(dict(model="lgbm_summaries", split="rows 70/30", repeat=r, test_cutters="all (30% of cycles)", whole=w, last20=l))
    tools = sorted(df["tool"].unique())
    pcs = []
    for r, test_tools in enumerate(cutter_splits(tools)):
        te = df["tool"].isin(test_tools)
        p = fit(df[~te], df[te])
        w, l = score(p)
        pcs.append(per_cutter(p).reset_index().assign(repeat=r))
        rows.append(dict(model="lgbm_summaries", split="cutters 70/30", repeat=r, test_cutters=" ".join(map(str, test_tools)), whole=w, last20=l))
    pd.concat(pcs).to_csv(OUT / "split_comparison_lgbm_per_cutter.csv", index=False)
    loo = pd.concat([fit(df[df["tool"] != t], df[df["tool"] == t]) for t in tools])
    w, l = score(loo)
    rows.append(dict(model="lgbm_summaries", split="leave one out", repeat=0, test_cutters="each in turn", whole=w, last20=l))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "split_comparison_lgbm.csv", index=False)
    print(out.groupby("split")[["whole", "last20"]].agg(["mean", "min", "max"]).round(1).to_string())


def _tcn_split(args):
    import torch
    torch.set_num_threads(1)
    r, test_tools = args
    th = module("th", "13_train_history.py")
    from toollife.models.hazard import curves
    df, cols = th.load("physics")
    te = df["tool"].isin(test_tools)
    rows, lg, _ = th.fit_predict(df[~te], df[te], cols, 3)
    p = rows[["tool", "age", "rul", "life"]].assign(pred=curves(lg)["rul_q50"])
    w, l = score(p)
    per = per_cutter(p).reset_index().assign(repeat=r)
    return dict(model="tcn_physics", split="cutters 70/30", repeat=r, test_cutters=" ".join(map(str, test_tools)), whole=w, last20=l), per


def run_tcn():
    th = module("th", "13_train_history.py")
    tools = sorted(th.load("physics")[0]["tool"].unique())
    with ProcessPoolExecutor(5) as ex:
        res = list(ex.map(_tcn_split, list(enumerate(cutter_splits(tools)))))
    rows = [r for r, _ in res]
    pd.concat([pc for _, pc in res]).to_csv(OUT / "split_comparison_tcn_per_cutter.csv", index=False)
    # leave one out: the project's saved 5-seed predictions, scored the same way
    p = pd.read_parquet(ROOT / "results" / "predictions" / "history_physics.parquet").rename(columns={"run_idx": "age", "rul_q50": "pred"})
    w, l = score(p[p["rul"] >= 1])
    rows.append(dict(model="tcn_physics", split="leave one out", repeat=0, test_cutters="each in turn", whole=w, last20=l))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "split_comparison_tcn.csv", index=False)
    print(out.groupby("split")[["whole", "last20"]].agg(["mean", "min", "max"]).round(1).to_string())


def summary():
    parts = [pd.read_csv(OUT / f"split_comparison_{m}.csv") for m in ("lgbm", "tcn")]
    df = pd.concat(parts)
    s = df.groupby(["model", "split"]).agg(splits=("whole", "size"), whole_mean=("whole", "mean"), whole_min=("whole", "min"),
                                           whole_max=("whole", "max"), last20_mean=("last20", "mean"),
                                           last20_min=("last20", "min"), last20_max=("last20", "max")).round(2)
    s.to_csv(OUT / "split_comparison.csv")
    print(s.to_string())
    # A set of random splits does not test every cutter equally often; average per cutter as well.
    for m in ("lgbm", "tcn"):
        pc = pd.read_csv(OUT / f"split_comparison_{m}_per_cutter.csv")
        c = pc.groupby("tool").agg(times=("repeat", "size"), whole=("whole", "mean"), last20=("last20", "mean"))
        print(m, "times tested per cutter:", c["times"].to_dict())
        print(m, "each cutter equally: whole %.2f, last20 %.2f" % (c["whole"].mean(), c["last20"].mean()))


if __name__ == "__main__":
    {"lgbm": run_lgbm, "tcn": run_tcn, "summary": summary}[sys.argv[1]]()
