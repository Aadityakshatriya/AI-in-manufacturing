"""Shared-feature experiment: does what other machines teach transfer to ours?

Every dataset is reduced to two signals it can provide, each relative to the same cutter when new:
  spindle load (current or torque)  and  vibration level (missing for LUH, flagged as missing).
A small TCN reads a cutter's runs in order and estimates the fraction of its life already used
(0 = new, 1 = end of life). End of life means breakage for Rzeszów, a wear limit for NASA, LUH and
MSTW, and the operator's call for VMC 650, so "fraction of life" is only roughly the same thing
everywhere; results are reported per dataset.

Tests
  On our 13 cutters: (a) train on ours only (hide one cutter at a time), (b) train on the other four
  datasets only, (c) train on both (hide one of our cutters at a time).
  Hide one whole dataset at a time: train on the other four, test on it.
Score: mean absolute error in fraction of life (0.25 = no better than always guessing 0.5),
and how well the estimate rises within each cutter (Spearman).

Writes results/cross_dataset/summary.csv and per-cutter tables.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.models.history import CausalBlock
from toollife.rzeszow import ROOT

torch.set_num_threads(2)
PROC = ROOT / "data" / "processed"
OUT = ROOT / "results" / "cross_dataset"
OUT.mkdir(parents=True, exist_ok=True)
MAX_RUNS = 150  # long LUH tools are thinned so every cutter has a comparable number of steps
TABLE_ACC = ["X_Driving_axle_pZ", "X_Driving_axle_mX", "Y_Driving_axle_pZ", "Y_Driving_axle_pY", "Y_Driving_axle_mX"]


def load_all() -> pd.DataFrame:
    parts = []
    rz = pd.read_parquet(PROC / "rzeszow_physics.parquet")
    rz = rz[(rz["tool"] != 11) & (rz["rul"] >= 1)]
    parts.append(pd.DataFrame({
        "dataset": "rzeszow", "tool": "rzeszow_" + rz["tool"].astype(str), "order": rz["age"],
        "spindle": rz["spindle_net_a__rel"], "vib": rz[[f"{a}__rms__rel" for a in TABLE_ACC]].mean(axis=1),
        "life_frac": (rz["age"] + 1) / rz["life"],
    }))
    for name in ("nasa", "luh", "mstw", "vmc650"):
        d = pd.read_parquet(PROC / f"runs_{name}.parquet")
        if "signal_ok" in d:
            d = d[d["signal_ok"].fillna(True).astype(bool)]
        parts.append(pd.DataFrame({
            "dataset": name, "tool": name + "_" + d["tool"].astype(str), "order": d["run_idx"],
            "spindle": d["spindle_load_rel"], "vib": d.get("vib_rms_rel"), "life_frac": d["life_frac"],
        }))
    df = pd.concat(parts, ignore_index=True).dropna(subset=["spindle", "life_frac"])
    df = df.sort_values(["tool", "order"])
    # Thin very long tools evenly.
    df = df.groupby("tool", group_keys=False).apply(lambda g: g.iloc[np.linspace(0, len(g) - 1, min(len(g), MAX_RUNS)).astype(int)])
    df["x_spindle"] = np.log(df["spindle"].clip(0.2, 5))
    df["has_vib"] = df["vib"].notna().astype(float)
    df["x_vib"] = np.log(df["vib"].clip(0.2, 20)).fillna(0.0)
    return df.reset_index(drop=True)


FEATS = ["x_spindle", "x_vib", "has_vib"]


class Gauge(nn.Module):
    def __init__(self, hidden=32):
        super().__init__()
        self.inp = nn.Linear(len(FEATS), hidden)
        self.tcn = nn.Sequential(*[CausalBlock(hidden, d, dropout=0.1) for d in (1, 2, 4, 8)])
        self.out = nn.Linear(hidden, 1)

    def forward(self, x):
        h = self.tcn(self.inp(x).transpose(1, 2)).transpose(1, 2)
        return torch.sigmoid(self.out(h)).squeeze(-1)


def pack(df):
    tools = list(df["tool"].unique())
    T = df.groupby("tool").size().max()
    x = np.zeros((len(tools), T, len(FEATS)), np.float32)
    y = np.zeros((len(tools), T), np.float32)
    m = np.zeros((len(tools), T), np.float32)
    for i, t in enumerate(tools):
        g = df[df["tool"] == t]
        x[i, : len(g)] = g[FEATS].to_numpy(np.float32)
        y[i, : len(g)] = g["life_frac"].to_numpy(np.float32)
        m[i, : len(g)] = 1
    return tools, torch.as_tensor(x), torch.as_tensor(y), torch.as_tensor(m)


def fit(train_df, seed, epochs=600):
    torch.manual_seed(seed)
    _, x, y, m = pack(train_df)
    # Each dataset counts equally, and inside a dataset each cutter counts equally.
    ds = train_df.groupby("tool")["dataset"].first()
    w = torch.as_tensor((1.0 / ds.map(ds.value_counts())).reindex(train_df["tool"].unique()).to_numpy(np.float32))
    model = Gauge()
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-2)
    for _ in range(epochs):
        opt.zero_grad()
        per_tool = (nn.functional.huber_loss(model(x), y, reduction="none", delta=0.1) * m).sum(1) / m.sum(1)
        ((per_tool * w).sum() / w.sum()).backward()
        opt.step()
    return model.eval()


def predict(models, test_df):
    tools, x, _, m = pack(test_df)
    with torch.no_grad():
        p = torch.stack([mdl(x) for mdl in models]).mean(0)
    out = []
    for i, t in enumerate(tools):
        g = test_df[test_df["tool"] == t].copy()
        g["pred"] = p[i, : len(g)].numpy()
        out.append(g)
    return pd.concat(out)


def score(pred, label):
    rows = []
    for t, g in pred.groupby("tool"):
        rows.append(dict(setting=label, dataset=g["dataset"].iloc[0], tool=t, mae=np.abs(g["pred"] - g["life_frac"]).mean(),
                         rho=spearmanr(g["pred"], g["life_frac"]).statistic if len(g) > 4 else np.nan))
    return pd.DataFrame(rows)


def main():
    df = load_all()
    print(df.groupby("dataset").agg(tools=("tool", "nunique"), runs=("tool", "size"), vib=("has_vib", "mean")).round(2))
    seeds = range(3)
    rz = df[df["dataset"] == "rzeszow"]
    others = df[df["dataset"] != "rzeszow"]
    results = []

    # (b) other datasets only → all of ours
    models = [fit(others, s) for s in seeds]
    results.append(score(predict(models, rz), "ours: trained on other machines only"))
    # (a) and (c): hide one of our cutters at a time
    for label, extra in (("ours: trained on ours only", None), ("ours: trained on ours + other machines", others)):
        preds = []
        for t in rz["tool"].unique():
            train = rz[rz["tool"] != t] if extra is None else pd.concat([rz[rz["tool"] != t], extra])
            preds.append(predict([fit(train, s) for s in seeds], rz[rz["tool"] == t]))
        results.append(score(pd.concat(preds), label))
    # Hide one whole dataset at a time.
    for name in df["dataset"].unique():
        models = [fit(df[df["dataset"] != name], s) for s in seeds]
        results.append(score(predict(models, df[df["dataset"] == name]), f"hide dataset: {name}"))

    res = pd.concat(results)
    res.to_csv(OUT / "per_cutter.csv", index=False)
    summary = res.groupby(["setting", "dataset"]).agg(cutters=("tool", "size"), mae=("mae", "mean"), rho=("rho", "mean")).round(3)
    summary.to_csv(OUT / "summary.csv")
    print(summary.to_string())


if __name__ == "__main__":
    main()
