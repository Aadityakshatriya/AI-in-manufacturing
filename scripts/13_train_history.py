"""Train and test the history model on Rzeszów with nested leave-one-cutter-out.

For each of the 13 cutters (outer fold): hide it; on the other 12, run inner leave-one-cutter-out to get
out-of-fold predictions (used to set the conformal margins that widen the low/high estimates);
then train a 5-seed ensemble on all 12 and predict the hidden one. Folds run in parallel processes.

Usage: python scripts/13_train_history.py --features {settings_age,physics,ae,physics_ae} [--seeds 5]
The 'ae' feature sets use the CNN autoencoder of the hidden cutter's fold group (scripts/11_train_autoencoder.py).
Writes results/predictions/history_<name>.parquet (PLAN.md §6 format) and results/models/history_<name>.csv.
"""

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.models.hazard import curves, tool_conformal_margin
from toollife.models.history import make_sequences, predict, train
from toollife.rzeszow import ROOT

torch.set_num_threads(4)
SETTINGS = ["adoc_mm", "rdoc_mm", "holder_mm", "hardness_hrc", "tool_type"]

# Physics features, all relative to the cutter's own first cycles (log ratios), plus two absolute ones.
PHYS_REL = [
    "spindle_net_a", "table_cut_a", "x_cut_a", "y_cut_a", "spindle_charge_per_mm3", "table_over_spindle",
    "X_Driving_axle_pZ__rms", "X_Driving_axle_pZ__tooth", "X_Driving_axle_pZ__order1", "X_Driving_axle_pZ__hiband_rms",
    "X_Driving_axle_mX__rms", "X_Driving_axle_mX__tooth", "X_Driving_axle_mX__order1",
    "Y_Driving_axle_pY__rms", "Y_Driving_axle_pY__tooth", "Y_Driving_axle_pY__hiband_rms",
    "Spindle_mX__rms", "Spindle_mX__hiband_rms",
]
PHYS_ABS = ["X_Driving_axle_pZ__asym", "X_Driving_axle_pZ__sync_frac", "X_Driving_axle_pZ__kurt", "Spindle_mX__kurt"]


GROUP_OF = {t: g for g, ts in {1: [2, 7, 101], 2: [3, 8, 102], 3: [4, 9, 103], 4: [5, 10], 5: [6, 105]}.items() for t in ts}


def load(features: str) -> tuple[pd.DataFrame, list[str]]:
    df = pd.read_parquet(ROOT / "data" / "processed" / "rzeszow_physics.parquet")
    df = df[df["tool"] != 11].copy()
    df["log_age"] = np.log1p(df["age"])
    df["first_ring"] = df["file"].str.endswith("_C1").astype(float)
    cols = SETTINGS + ["log_age"]
    if features in ("physics", "physics_ae"):
        for c in PHYS_REL:
            df[f"lr_{c}"] = np.log(df[f"{c}__rel"].clip(1e-3, 1e3))
        cols += [f"lr_{c}" for c in PHYS_REL] + PHYS_ABS + ["first_ring"]
    if features in ("ae", "physics_ae"):
        cols += ["log_health", "log_health_rel"] + [f"emb_{i}" for i in range(64)]
    df["life_frac"] = (df["age"] + 1) / df["life"]
    return df, cols


def add_autoencoder(df: pd.DataFrame, group: int) -> pd.DataFrame:
    """Fingerprint and health score from autoencoder `group` (which never heard that group's cutters)."""
    ae = pd.read_parquet(ROOT / "data" / "processed" / f"ae_g{group}.parquet")
    ae = ae.rename(columns={f"fp_{i}": f"emb_{i}" for i in range(64)})
    out = df.merge(ae, on="file", how="left").sort_values(["tool", "age"])
    out["log_health"] = np.log(out["health"])
    # Health relative to the cutter's own first clean cycles: "how much less healthy than when new".
    base = out[~out["file"].str.endswith("_C1")].groupby("tool")["log_health"].apply(lambda s: s.head(3).median())
    out["log_health_rel"] = out["log_health"] - out["tool"].map(base)
    return out


def compress_embeddings(train_df, test_df, cols, n_components=8):
    """Replace the 64 fingerprint columns by their top principal components, fitted on training cutters only."""
    ecols = [c for c in cols if c.startswith("emb_")]
    if not ecols:
        return train_df, test_df, cols
    from sklearn.decomposition import PCA

    pca = PCA(n_components, random_state=0).fit(train_df[ecols].fillna(0).to_numpy())
    pcols = [f"pc_{i}" for i in range(n_components)]
    out = []
    for d in (train_df, test_df):
        d = d.copy()
        d[pcols] = pca.transform(d[ecols].fillna(0).to_numpy())
        out.append(d)
    return out[0], out[1], [c for c in cols if not c.startswith("emb_")] + pcols


def fit_predict(train_df, test_df, cols, seeds):
    """Ensemble trained on all of train_df for a fixed number of passes, predictions on test_df.

    No early stopping: with only 12 training cutters, holding 2 back to decide when to stop was
    noisier than simply training for a fixed 400 passes (checked on 27 Oct).
    """
    train_df, test_df, cols = compress_embeddings(train_df, test_df, cols)
    seq_tr, mean, std = make_sequences(train_df, cols)
    seq_te, _, _ = make_sequences(test_df, cols, mean=mean, std=std)
    models = [train(seq_tr, None, len(cols), seed=s) for s in range(seeds)]
    logits, gauge = predict(models, seq_te)
    rows = test_df[test_df["rul"] >= 1].sort_values(["tool", "age"])
    return rows, logits, gauge


def run_fold(held, features, base_df, cols, seeds):
    """One outer fold: calibrate on the other 12 cutters, then predict the hidden one."""
    torch.set_num_threads(1)
    df = add_autoencoder(base_df, GROUP_OF[held]) if features in ("ae", "physics_ae") else base_df
    dev, test = df[df["tool"] != held], df[df["tool"] == held]
    # Inner loop: out-of-fold predictions on the 12 development cutters, for calibration only.
    oof = [fit_predict(dev[dev["tool"] != inner], dev[dev["tool"] == inner], cols, 1)[:2] for inner in sorted(dev["tool"].unique())]
    oof_rows = pd.concat([r for r, _ in oof])
    oof_c = curves(np.concatenate([l for _, l in oof]))
    rul_oof, tools_oof = oof_rows["rul"].to_numpy(), oof_rows["tool"].to_numpy()
    # Conformal widening, one score per cutter: how far below its low estimate (or above its high
    # estimate) the truth ever fell. The margin is the worst such miss seen on the other cutters.
    lo_margin = tool_conformal_margin(oof_c["rul_q10"], rul_oof, tools_oof)
    hi_margin = tool_conformal_margin(-oof_c["rul_q90"], -rul_oof, tools_oof)

    rows, lg, gauge = fit_predict(dev, test, cols, seeds)
    c = curves(lg)
    pred = rows[["tool", "age", "rul", "life", "file"]].copy()
    pred["fold"] = held
    for k in ("rul_q10", "rul_q50", "rul_q90", "rmst", "p_fail_1", "p_fail_3", "p_fail_5"):
        pred[k] = c[k]
    pred["rul_lower"] = np.maximum(c["rul_q10"] - max(lo_margin, 0), 0)
    pred["rul_upper"] = c["rul_q90"] + max(hi_margin, 0)
    pred["gauge"] = gauge
    haz = pd.DataFrame(c["hazard"][:, :60], columns=[f"hazard_{k}" for k in range(1, 61)], index=pred.index)
    print(f"cutter {held:>3}: margins -{lo_margin:.0f}/+{hi_margin:.0f} MAE(q50)={np.abs(c['rul_q50'] - rows['rul']).mean():.1f}", flush=True)
    return pd.concat([pred, haz], axis=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default="physics", choices=["settings_age", "physics", "ae", "physics_ae"])
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--name")
    args = ap.parse_args()
    name = args.name or args.features
    base_df, cols = load(args.features)
    with ProcessPoolExecutor(8) as pool:
        futs = [pool.submit(run_fold, held, args.features, base_df, cols, args.seeds) for held in sorted(base_df["tool"].unique())]
        out_rows = [f.result() for f in futs]

    pred = pd.concat(out_rows).reset_index(drop=True)
    pred.insert(0, "dataset", "rzeszow")
    pred = pred.rename(columns={"age": "run_idx"})
    (ROOT / "results" / "predictions").mkdir(parents=True, exist_ok=True)
    pred.to_parquet(ROOT / "results" / "predictions" / f"history_{name}.parquet")

    # Per-cutter metrics, each cutter weighted equally.
    m = []
    for t, g in pred.groupby("tool"):
        near = (g["run_idx"] + 1) / g["life"] >= 0.8
        err = g["rul_q50"] - g["rul"]
        m.append(dict(
            tool=t, mae=np.abs(err).mean(), mae_last20=np.abs(err[near]).mean(),
            over_last20=err[near].clip(lower=0).mean(),
            cover_raw=((g["rul"] >= g["rul_q10"]) & (g["rul"] <= g["rul_q90"])).mean(),
            cover_widened=((g["rul"] >= g["rul_lower"]) & (g["rul"] <= g["rul_upper"])).mean(),
            width=(g["rul_upper"] - g["rul_lower"]).mean(),
            brier5=((g["p_fail_5"] - (g["rul"] <= 5)) ** 2).mean(),
        ))
    m = pd.DataFrame(m)
    (ROOT / "results" / "models").mkdir(parents=True, exist_ok=True)
    m.to_csv(ROOT / "results" / "models" / f"history_{name}.csv", index=False)
    print(m.round(2).to_string(index=False))
    print("MEAN", m.drop(columns="tool").mean().round(3).to_dict())


if __name__ == "__main__":
    main()
