"""Cutter lifecycles as the decision layer sees them, built from a predictions table.

A `Life` is one real cutter life plus the failure curves a predictor produced for it, one curve after
every completed good cycle. It is the unit that the single-cutter replay (replay.py) and the RL
workshop (rl/workshop_env.py) both replay. Lives from any dataset can be added to a pool, as long as
the predictions follow the PLAN.md §6 interface.

Timeline of one life (Rzeszów convention, checked against metadata.xlsx):
  row a = 0, 1, ..., L-1 : the cutter has just finished its (a+1)-th cycle, which was good.
                           The predictor has seen signals up to and including that cycle.
                           hazard[a, j-1] = P(fails during cycle a+1+j | survived through cycle a+1+j-1).
  cycle L+1              : the cycle in which the cutter broke (row a = L in the data, rul = 0).
  So a life has L good cycles; "keep" after row L-1 means running the breaking cycle.
The prediction for the breaking cycle itself (row L) is never used: its signals contain the break.

Assumptions (stated once here):
  * Duplicate records of the same cycle (Rzeszów cutter 2, cycle 34 twice) are de-duplicated by
    keeping the first file name.
  * Missing cycles: the decision after a missing cycle uses the last available curve, shifted
    forward by the number of cycles survived since it was made (`curves.shift`). This is the exact
    update "still alive, no new signal" under that curve.
  * If the first decision rows are missing (no earlier curve exists), the first available curve is
    used as is. This does not happen in Rzeszów.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import warnings

import numpy as np
import pandas as pd

from toollife.policy.curves import rul_quantiles, shift, stretch

ROOT = Path(__file__).resolve().parents[3]
PRED_DIR = ROOT / "results" / "predictions"
PROCESSED = ROOT / "data" / "processed"

# rl-design.md §4.10: four outer folds for the workshop, each with a short and a long life.
RL4_FOLDS = {"F1": [10, 4, 103, 9], "F2": [6, 2, 101, 7], "F3": [3, 102, 105], "F4": [5, 8]}


@dataclass
class Life:
    dataset: str
    tool: str                 # unique id within the dataset, as a string
    L: int                    # good cycles before the end of life
    end_type: str             # 'break' | 'wear' | 'operator'
    hazard: np.ndarray        # [L, K] curve after each completed good cycle (gaps filled)
    rul_q: np.ndarray         # [L, 3] steps-to-failure quantiles q10, q50, q90 from the same curves
    cond: np.ndarray = field(default_factory=lambda: np.zeros(3))  # conditions for the RL observation
    group: str = "all"        # setting group (fixed-interval-per-group rule)
    warp: float = 1.0         # time-warp factor if this is an augmented copy (training only)

    @property
    def key(self) -> str:
        return f"{self.dataset}:{self.tool}"

    @property
    def K(self) -> int:
        return self.hazard.shape[1]

    def curve_at(self, a: int) -> np.ndarray:
        """Curve after a+1 completed cycles. Past the last row (only possible in the 'model' world of
        the workshop, where the failure point is sampled), the last curve is shifted forward."""
        last = self.hazard.shape[0] - 1
        if a <= last:
            return self.hazard[max(a, 0)]
        return shift(self.hazard[last], a - last)

    def warped(self, w: float) -> "Life":
        """Time-warp augmentation (rl-design §4.11, training only): life L' = round(w L), the curve at
        step k' is read from step k'/w and stretched so that S'(j) = S(j / w)."""
        L2 = max(1, int(round(w * self.L)))
        src = np.minimum((np.arange(L2) / w).astype(int), self.L - 1)
        hz = np.stack([stretch(self.hazard[i], w) for i in src])
        return Life(self.dataset, self.tool, L2, self.end_type, hz, rul_quantiles(hz),
                    self.cond.copy(), self.group, w)


# ----------------------------------------------------------------------------------------------
# Rzeszów rows and ground truth


def rzeszow_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Usable Rzeszów rows sorted by age, with the cutter-2 duplicate removed (first file kept)."""
    out = df.sort_values(["tool", "age", "file"]).drop_duplicates(["tool", "age"], keep="first")
    return out.reset_index(drop=True)


def rzeszow_truth() -> pd.DataFrame:
    """One row per usable Rzeszów cutter: L, end type, conditions and setting group."""
    from toollife.rzeszow import load_table, usable

    df = rzeszow_rows(usable(load_table()))
    g = df.groupby("tool").agg(life=("life", "first"), adoc=("adoc_mm", "first"),
                               rdoc=("rdoc_mm", "first"), tool_type=("tool_type", "first"))
    return pd.DataFrame({
        "dataset": "rzeszow",
        "tool": g.index.astype(str),
        "L": g["life"].to_numpy() - 1,
        "end_type": "break",
        # Fixed scaling to roughly [0, 1]: depth 5/10 mm, width 4.5/8 mm, cutter type 1/2.
        "cond": [np.array([a / 10, r / 8, t - 1], float) for a, r, t in zip(g.adoc, g.rdoc, g.tool_type)],
        "group": [f"rdoc{r:g}" for r in g.rdoc],
    }).reset_index(drop=True)


def runs_truth(dataset: str) -> pd.DataFrame:
    """Ground truth for another dataset from data/processed/runs_<dataset>.parquet (PLAN.md §6).

    Assumes `rul_native` is counted in runs with the Rzeszów convention (0 on the run in which the
    life ended), so L = run_idx + rul_native on every row. Rows that disagree trigger a warning and
    the value from the first run is used. The life ends at the dataset's own end (`end_type`,
    usually 'wear' at the wear limit).
    """
    runs = pd.read_parquet(PROCESSED / f"runs_{dataset}.parquet")
    rows = []
    for tool, g in runs.groupby("tool"):
        g = g.sort_values("run_idx")
        Ls = (g["run_idx"] + g["rul_native"]).round().astype(int)
        if Ls.nunique() > 1:
            warnings.warn(f"{dataset}:{tool}: run_idx + rul_native is not constant; using the first run")
        rows.append(dict(dataset=dataset, tool=str(tool), L=int(Ls.iloc[0]),
                         end_type=str(g["end_type"].iloc[0]), cond=np.zeros(3), group=dataset))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------
# Predictions → Lives


def hazard_columns(pred: pd.DataFrame) -> list[str]:
    cols = [c for c in pred.columns if c.startswith("hazard_")]
    return sorted(cols, key=lambda c: int(c.split("_")[1]))


def load_predictions(model: str, nested: bool = False) -> pd.DataFrame:
    """results/predictions/<model>.parquet (standard interface: held-out rows only), or the nested
    file results/predictions/nested/<model>.parquet that also holds inner out-of-fold rows."""
    path = PRED_DIR / ("nested" if nested else "") / f"{model}.parquet"
    pred = pd.read_parquet(path)
    pred["tool"] = pred["tool"].astype(str)
    pred["fold"] = pred["fold"].astype(str)
    if "dataset" not in pred:
        pred["dataset"] = "rzeszow"
    return pred


def build_lives(pred: pd.DataFrame, truth: pd.DataFrame) -> dict[str, Life]:
    """Turn prediction rows (one fold/role selection, at most one row per tool and run) into Lives,
    keyed by 'dataset:tool'. Rows at or after the end of life are dropped."""
    hcols = hazard_columns(pred)
    lives = {}
    t = truth.set_index(["dataset", "tool"])
    for (ds, tool), g in pred.groupby(["dataset", "tool"], sort=False):
        info = t.loc[(ds, tool)]
        L = int(info["L"])
        if "fold" in g and g["fold"].nunique() > 1:
            raise ValueError(f"{ds}:{tool}: rows from more than one fold; select one fold first")
        g = g.sort_values(["run_idx", "file"] if "file" in g else ["run_idx"])
        if g["run_idx"].duplicated().any():  # the same cycle recorded twice (Rzeszów cutter 2, cycle 34)
            warnings.warn(f"{ds}:{tool}: duplicate rows for runs {sorted(set(g.loc[g['run_idx'].duplicated(), 'run_idx']))}; keeping the first")
            g = g.drop_duplicates("run_idx", keep="first")
        g = g[g["run_idx"] < L]
        if g.empty or L < 1:
            continue
        H = g[hcols].to_numpy(float)
        idx = g["run_idx"].to_numpy(int)
        hz = np.empty((L, len(hcols)))
        pos = 0
        for a in range(L):
            while pos + 1 < len(idx) and idx[pos + 1] <= a:
                pos += 1
            if idx[pos] <= a:
                hz[a] = shift(H[pos], a - idx[pos])
            else:  # no earlier row exists: use the first available curve (see module docstring)
                hz[a] = H[0]
        lives[f"{ds}:{tool}"] = Life(ds, str(tool), L, str(info["end_type"]), hz, rul_quantiles(hz),
                                     np.asarray(info["cond"], float), str(info["group"]))
    return lives


def fold_lives(model: str, fold: str, scheme: str = "loco", truth: pd.DataFrame | None = None):
    """(train_lives, test_lives) for one outer fold, with no leakage:

    test  : rows predicted by the model trained without the fold's test cutters (role 'test');
    train : the training cutters' inner out-of-fold rows (role 'inner'), each predicted by a model
            that saw neither the test cutters nor that training cutter (rl-design §4.10).

    If the nested file does not exist (e.g. the lead's model only wrote the standard file), training
    cutters fall back to their own leave-one-out rows. Those came from models that saw the test
    cutter: a mild second-order leak that rl-design §4.10 allows as the cheap fallback; we warn.
    """
    truth = rzeszow_truth() if truth is None else truth
    fold = str(fold)
    test_tools = [str(t) for t in (RL4_FOLDS[fold] if scheme == "rl4" else [fold])]
    try:
        nested = load_predictions(model, nested=True)
        sel = nested[(nested["scheme"] == scheme) & (nested["fold"] == fold)]
        test = sel[sel["role"] == "test"]
        train = sel[sel["role"] == "inner"]
    except FileNotFoundError:
        warnings.warn(f"{model}: no nested predictions; training cutters use plain leave-one-out rows")
        std = load_predictions(model)
        test = std[std["tool"].isin(test_tools)]
        train = std[~std["tool"].isin(test_tools) & (std["fold"] == std["tool"])]
    assert set(test["tool"]) <= set(test_tools), "test rows from a non-test cutter"
    assert not set(train["tool"]) & set(test_tools), "a test cutter is in the training pool"
    if "trained_without" in train:
        for tool, tw in zip(train["tool"], train["trained_without"]):
            excl = set(str(tw).split(","))
            assert tool in excl and set(test_tools) <= excl, f"leak: row for {tool} trained with {tw}"
    keep_truth = truth[truth["tool"].isin(set(test["tool"]) | set(train["tool"]))]
    return list(build_lives(train, keep_truth).values()), list(build_lives(test, keep_truth).values())


def dataset_lives(model: str, dataset: str) -> list[Life]:
    """All lives of another dataset (e.g. 'mstw', 'luh') from results/predictions/<model>.parquet,
    with life lengths and end types from data/processed/runs_<dataset>.parquet. Meant as EXTRA
    training lives for the workshop (its Rzeszów test cutters are untouched). Each row must come
    from a model that never trained on that tool; if the model also trained on Rzeszów cutters,
    say so when reporting, since the curves of these extra lives then carry that information."""
    pred = load_predictions(model)
    pred = pred[pred["dataset"] == dataset]
    if pred.empty:
        raise ValueError(f"{model} has no rows for dataset {dataset}")
    pred = pred[pred["fold"] == pred["tool"]] if (pred["fold"] == pred["tool"]).any() else pred
    return list(build_lives(pred, runs_truth(dataset)).values())
