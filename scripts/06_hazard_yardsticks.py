"""Yardstick failure curves for the decision layer, in the PLAN.md §6 predictions interface.

For every recorded cycle of every usable Rzeszów cutter, each model gives hazard_1 … hazard_K
(K = 60): the chance of failing in each of the next K cycles, given survival until then
(model-design.md §5.1), plus remaining-life quantiles rul_q10/q50/q90 read off the same curve.
"Remaining life" here is the steps-to-failure J (J = 1: the next cycle breaks), which equals the
dataset's `rul` column.

Models
  weibull_settings_age : Weibull AFT (lifelines) fitted to the training cutters' lives with the
                         cutting settings as covariates (tool type, axial and radial depth, holder,
                         the cutter's mean hardness). The life of a cutter with L good cycles is
                         entered as L + 0.5 (it broke somewhere inside cycle L + 1). The curve at
                         age a is the exact conditional hazard given survival of a + 1 cycles.
                         Sensors are not used, so its curves are self-consistent: the curve one
                         cycle later equals this curve shifted by one step.
  lgbm_hazard          : LightGBM discrete-time hazard on the 120 released sensor summaries + age +
                         settings. Trained in "person-period" form (model-design.md §8, B4): each
                         training row at age a is expanded into one row per step k = 1 … 160
                         with label 1 if the cutter failed at exactly step k, kept only while it
                         was still at risk (rul >= k). Its k = 1 slice is the "fails at the next
                         cycle" model. Why not one next-cycle classifier with age shifted forward:
                         that label has only 12 positive rows per training set, too few for
                         LightGBM; the person-period form has one positive row per training row
                         (~880 from the same 12 lives) and gives each step's hazard directly.
                         Hazard is constrained to be non-decreasing in k (wear only accumulates).
                         160 steps (the main model's horizon, model-design.md §7) covers the
                         longest life, so remaining-life quantiles come from the model rather than
                         from a tail guess; only the first K steps are stored. Not calibrated.

Folds (no prediction row ever comes from a model that trained on that cutter)
  loco : 13 outer folds, one held-out cutter each.            → results/predictions/<model>.parquet
  rl4  : the 4 outer folds of rl-design.md §4.10 (workshop).
  Both are nested: inside each outer fold, every training cutter also gets an inner out-of-fold
  prediction from a model trained without it and without the fold's test cutters. Those rows are
  what policies are tuned on.                                → results/predictions/nested/<model>.parquet
  Columns: role ('test' or 'inner'), scheme, fold, trained_without (comma-separated cutters).

Also writes results/predictions/summary.csv: held-out quality of each curve (log-likelihood of
the real failure step, calibration of the next-cycle and 10-cycle risk, median error, interval
coverage), each cutter weighted equally.

Usage: python scripts/06_hazard_yardsticks.py [--jobs -1]
"""

import argparse
import sys
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from lifelines import WeibullAFTFitter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.policy.curves import rul_quantiles, survival
from toollife.policy.lives import RL4_FOLDS, rzeszow_rows
from toollife.rzeszow import ROOT, SETTING_COLS, load_table, sensor_columns, usable

warnings.filterwarnings("ignore")
OUT = ROOT / "results" / "predictions"
K = 60
LONG = 400     # horizon used only for the Weibull's exact remaining-life quantiles
K_FIT = 160    # steps ahead the LightGBM hazard is trained and evaluated on (first K are stored)

df = rzeszow_rows(usable(load_table()))
SENSORS = sensor_columns(df)
TOOLS = sorted(df["tool"].unique())
HCOLS = [f"hazard_{j}" for j in range(1, K + 1)]

# One row per cutter: settings known before cutting starts (hardness averaged over its workpieces).
CUTTERS = df.groupby("tool").agg(
    tool_type=("tool_type", "first"), adoc_mm=("adoc_mm", "first"), rdoc_mm=("rdoc_mm", "first"),
    hardness_hrc=("hardness_hrc", "mean"), holder_mm=("holder_mm", "first"), life=("life", "first"),
)


# ------------------------------------------------------------------------------------------------
# (a) Weibull AFT on settings + age


def weibull(train_tools, pred_tools):
    lives = CUTTERS.loc[train_tools].copy()
    cols = [c for c in SETTING_COLS if lives[c].nunique() > 1]
    lives["T"] = lives["life"] - 1 + 0.5
    lives["E"] = 1
    m = WeibullAFTFitter(penalizer=0.1).fit(lives[cols + ["T", "E"]], "T", "E")
    beta = m.params_.loc["lambda_"]
    rho = np.exp(m.params_.loc[("rho_", "Intercept")])
    out = []
    for tool in pred_tools:
        x = CUTTERS.loc[tool, cols].to_numpy(float)
        lam = np.exp(beta.reindex(cols).to_numpy() @ x + beta["Intercept"])
        rows = df[df["tool"] == tool]
        a = rows["age"].to_numpy()
        # log S(t) = -(t / lam)^rho ; after a + 1 completed cycles, step j breaks inside cycle a + 1 + j.
        t = a[:, None] + 1 + np.arange(LONG + 1)[None, :]
        logs = -((t / lam) ** rho)
        h = 1.0 - np.exp(logs[:, 1:] - logs[:, :-1])
        out.append((rows, h[:, :K], rul_quantiles(h)))
    return out


# ------------------------------------------------------------------------------------------------
# (b) LightGBM person-period hazard on sensors + age + settings

FEATS = SENSORS + SETTING_COLS + ["age", "k", "age_at_step"]
LGB_PARAMS = dict(
    objective="binary", n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=100,
    subsample=0.8, subsample_freq=1, colsample_bytree=0.5, reg_lambda=1.0, verbose=-1,
    random_state=0, n_jobs=1, monotone_constraints=[0] * (len(FEATS) - 2) + [1, 0],
)


def person_period(rows: pd.DataFrame, train: bool) -> pd.DataFrame:
    """Expand each row into steps k = 1..K_FIT. For training keep only steps still at risk (rul >= k)."""
    rows = rows[rows["rul"] >= 1] if train else rows
    rep = rows.loc[rows.index.repeat(K_FIT)].copy()
    rep["k"] = np.tile(np.arange(1, K_FIT + 1), len(rows))
    rep["age_at_step"] = rep["age"] + rep["k"]
    if train:
        rep = rep[rep["rul"] >= rep["k"]]
        rep["y"] = (rep["rul"] == rep["k"]).astype(int)
    return rep


def lgbm(train_tools, pred_tools):
    pp = person_period(df[df["tool"].isin(train_tools)], train=True)
    m = lgb.LGBMClassifier(**LGB_PARAMS).fit(pp[FEATS], pp["y"])
    out = []
    for tool in pred_tools:
        rows = df[df["tool"] == tool]
        h = m.predict_proba(person_period(rows, train=False)[FEATS])[:, 1].reshape(len(rows), K_FIT)
        out.append((rows, h[:, :K], rul_quantiles(h)))
    return out


MODELS = {"weibull_settings_age": weibull, "lgbm_hazard": lgbm}


# ------------------------------------------------------------------------------------------------
# Nested folds


def jobs():
    """(scheme, fold, role, train_tools, pred_tools, excluded_tools) for every fit."""
    out = []
    for scheme, folds in [("loco", {str(t): [t] for t in TOOLS}), ("rl4", RL4_FOLDS)]:
        for fold, test in folds.items():
            train = [t for t in TOOLS if t not in test]
            out.append((scheme, fold, "test", train, list(test), list(test)))
            for c in train:
                out.append((scheme, fold, "inner", [t for t in train if t != c], [c], list(test) + [c]))
    return out


def run(model, scheme, fold, role, train, pred, excluded):
    frames = []
    for rows, h, q in MODELS[model](train, pred):
        f = pd.DataFrame({
            "dataset": "rzeszow", "tool": rows["tool"].astype(str).to_numpy(),
            "run_idx": rows["age"].to_numpy(), "fold": fold, "scheme": scheme, "role": role,
            "trained_without": ",".join(str(t) for t in excluded),
            "cycle": rows["cycle"].to_numpy(), "age": rows["age"].to_numpy(),
            "rul": rows["rul"].to_numpy(), "life": rows["life"].to_numpy(),
            "rul_q10": q[:, 0], "rul_q50": q[:, 1], "rul_q90": q[:, 2],
        })
        frames.append(pd.concat([f, pd.DataFrame(h.astype(np.float32), columns=HCOLS)], axis=1))
    return pd.concat(frames, ignore_index=True)


# ------------------------------------------------------------------------------------------------
# Held-out quality of the curves (decision rows only: rows after which the cutter was still whole)


def quality(pred: pd.DataFrame) -> dict:
    per = []
    for tool, g in pred[pred["rul"] >= 1].groupby("tool"):
        h = g[HCOLS].to_numpy(float)
        s = survival(h)
        J = g["rul"].to_numpy()
        inside = J <= K
        Jc = np.minimum(J, K)
        pj = h[np.arange(len(g)), Jc - 1] * s[np.arange(len(g)), Jc - 1]
        ll = np.where(inside, np.log(np.maximum(pj, 1e-12)), np.log(np.maximum(s[:, K], 1e-12)))
        f10 = 1 - s[:, 10]
        q = g[["rul_q10", "rul_q50", "rul_q90"]].to_numpy()
        near = g["age"].to_numpy() >= 0.8 * g["life"].iloc[0]
        per.append(dict(
            tool=tool, nll=-ll.mean(),
            sum_h1=h[:, 0].sum(),                      # expected next-cycle failures; truth is exactly 1
            f10_pred=f10.mean(), f10_obs=(J <= 10).mean(),
            brier10=((f10 - (J <= 10)) ** 2).mean(),
            mae_q50=np.abs(q[:, 1] - J).mean(), mae_q50_last20=np.abs(q[near, 1] - J[near]).mean(),
            cover_10_90=((J >= q[:, 0]) & (J <= q[:, 2])).mean(),
            h1_at_last=h[-1, 0] if g["rul"].iloc[-1] == 1 else np.nan,
        ))
    p = pd.DataFrame(per)
    return p.drop(columns="tool").mean().to_dict() | {"sum_h1_total": p["sum_h1"].sum(), "n_cutters": len(p)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=-1)
    args = ap.parse_args()
    (OUT / "nested").mkdir(parents=True, exist_ok=True)

    rows = []
    for model in MODELS:
        js = jobs()
        print(f"{model}: {len(js)} fits")
        parts = Parallel(n_jobs=args.jobs)(delayed(run)(model, *j) for j in js)
        nested = pd.concat(parts, ignore_index=True)
        nested.to_parquet(OUT / "nested" / f"{model}.parquet", index=False)

        std = nested[(nested["scheme"] == "loco") & (nested["role"] == "test")].drop(columns=["scheme", "role"])
        assert (std["fold"] == std["tool"]).all() and not std.duplicated(["tool", "run_idx"]).any()
        std.to_parquet(OUT / f"{model}.parquet", index=False)
        rows.append({"model": model} | quality(std))

    summary = pd.DataFrame(rows).set_index("model").round(4)
    summary.to_csv(OUT / "summary.csv")
    print("Held-out curve quality (leave-one-cutter-out, decision rows, each cutter weighted equally):")
    print(summary.T.to_string())
