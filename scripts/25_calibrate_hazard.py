"""Calibrate the TCN's risk curves, without leakage, and see whether calibrated curves make better decisions.

The TCN's risk curves are too confident: its own 10%–90% range holds the true remaining life only 13% of the
time. The decision rule takes the curves at face value, so overconfidence costs money (scripts/07: a
settings-only survival model, which is calibrated by construction, makes decisions about as good).

Two recalibrations of the hazard log-odds, both chosen before looking at any result:
  temperature   logit' = logit / T                 (one number; T > 1 flattens the curves)
  affine        logit' = a · logit + b             (two numbers: flatten and shift)
For each held-out cutter, the numbers are fitted on the other 12 cutters' inner out-of-fold curves (from
models that saw neither that cutter nor the held-out one; results/predictions/nested/history_physics.parquet),
by the same discrete-time survival likelihood the TCN was trained with, each cutter weighted equally. They
are then applied to the held-out cutter's curves, and to that fold's inner curves (which the decision rule
uses to set its one number).

Writes results/predictions/history_physics_{temp,affine}.parquet (+ nested/ copies) in the standard interface,
results/models/calibration.csv (held-out calibration and accuracy, before and after) and
results/models/calibration_reliability.csv (predicted vs observed chance of breaking within 5 cycles).
Then run scripts/07_single_cutter_decisions.py with the new sources.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from toollife.models.hazard import curves, hazard_nll

PRED = ROOT / "results" / "predictions"
SRC = "history_physics"


def targets(df):
    K = len(hcols(df))
    rul = df["rul"].to_numpy()
    return np.minimum(rul, K), (rul <= K).astype(np.float32)


def hcols(df):
    return sorted([c for c in df.columns if c.startswith("hazard_")], key=lambda c: int(c.split("_")[1]))


def logits_of(df):
    h = np.clip(df[hcols(df)].to_numpy(np.float64), 1e-7, 1 - 1e-7)
    return np.log(h / (1 - h))


def balanced_nll(lg, ek, ob, tools, a, b):
    nll = hazard_nll(a * lg + b, ek, ob)
    per = torch.stack([nll[tools == t].mean() for t in torch.unique(tools)])
    return per.mean()


def fit(df, kind):
    lg = torch.as_tensor(logits_of(df), dtype=torch.float64)
    ek, ob = (torch.as_tensor(x) for x in targets(df))
    tools = torch.as_tensor(df["tool"].astype(int).to_numpy())
    log_a = torch.zeros((), dtype=torch.float64, requires_grad=True)  # a = exp(log_a) > 0
    b = torch.zeros((), dtype=torch.float64, requires_grad=kind == "affine")
    params = [log_a] + ([b] if kind == "affine" else [])
    opt = torch.optim.LBFGS(params, lr=0.5, max_iter=200, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        loss = balanced_nll(lg, ek.long(), ob, tools, torch.exp(log_a), b)
        loss.backward()
        return loss

    opt.step(closure)
    return float(torch.exp(log_a).detach()), float(b.detach())


def apply(df, a, b):
    out = df.copy()
    lg = a * logits_of(df) + b
    c = curves(lg)
    out[hcols(df)] = c["hazard"]
    for q in ("rul_q10", "rul_q50", "rul_q90"):
        out[q] = c[q]
    out["p_fail_5"] = c["p_fail_5"]
    return out


def scores(df):
    """Held-out calibration and accuracy, each cutter weighted equally. The stored curves are the first 60
    cycles of the TCN's 160-cycle curves, so the median errors here (suffix _60) compare the methods with
    each other only; they are not the headline error of scripts/18."""
    lg = logits_of(df)
    ek, ob = targets(df)
    c = curves(lg)
    d = df.assign(nll=hazard_nll(torch.as_tensor(lg), torch.as_tensor(ek).long(), torch.as_tensor(ob)).numpy(),
                  inside=(df["rul"] >= c["rul_q10"]) & (df["rul"] <= c["rul_q90"]),
                  p5=c["p_fail_5"], y5=(df["rul"] <= 5).astype(float), err=np.abs(c["rul_q50"] - df["rul"]),
                  late=(df["run_idx"] + 1) / df["life"] >= 0.8)
    d["brier5"] = (d.p5 - d.y5) ** 2
    per = d.groupby("tool").apply(lambda g: pd.Series(dict(
        nll=g.nll.mean(), cover_10_90=g.inside.mean(), brier5=g.brier5.mean(),
        mae_whole_60=g.err.mean(), mae_last20_60=g.err[g.late].mean())), include_groups=False)
    return per.mean(), d


def main():
    nested = pd.read_parquet(PRED / "nested" / f"{SRC}.parquet")
    test = pd.read_parquet(PRED / f"{SRC}.parquet")
    nested["fold"], test["fold"] = nested["fold"].astype(str), test["fold"].astype(str)
    rows, outs, nouts, rel = [], {"temp": [], "affine": []}, {"temp": [], "affine": []}, []
    for fold in sorted(test["fold"].unique(), key=int):
        inner = nested[(nested["fold"] == fold) & (nested["role"] == "inner")]
        for kind, tag in (("temperature", "temp"), ("affine", "affine")):
            a, b = fit(inner, kind)
            rows.append(dict(fold=fold, method=tag, a=round(a, 3), b=round(b, 3), temperature=round(1 / a, 3)))
            outs[tag].append(apply(test[test["fold"] == fold], a, b))
            nouts[tag].append(apply(nested[nested["fold"] == fold], a, b))
    params = pd.DataFrame(rows)
    print(params.pivot(index="fold", columns="method", values=["a", "b"]).to_string())

    summary = []
    base, d0 = scores(test)
    summary.append(dict(method="none (as trained)", **base.round(3)))
    rel.append(d0.assign(method="none"))
    for tag in ("temp", "affine"):
        cal = pd.concat(outs[tag]).sort_index()
        cal.to_parquet(PRED / f"{SRC}_{tag}.parquet")
        pd.concat(nouts[tag]).to_parquet(PRED / "nested" / f"{SRC}_{tag}.parquet")
        s, d = scores(cal)
        summary.append(dict(method=tag, **s.round(3)))
        rel.append(d.assign(method=tag))
    summary = pd.DataFrame(summary)
    out = ROOT / "results" / "models"
    summary.to_csv(out / "calibration.csv", index=False)
    params.to_csv(out / "calibration_params.csv", index=False)
    print(summary.to_string(index=False))

    # Reliability: bins of the predicted chance of breaking within 5 cycles vs how often it happened.
    r = pd.concat(rel)
    r["bin"] = pd.cut(r.p5, [0, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.7, 1.0], include_lowest=True)
    rb = r.groupby(["method", "bin"], observed=True).agg(predicted=("p5", "mean"), observed=("y5", "mean"), rows=("y5", "size")).reset_index()
    rb["bin"] = rb["bin"].astype(str)
    rb.round(3).to_csv(out / "calibration_reliability.csv", index=False)
    print(rb.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
