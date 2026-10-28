"""One fair comparison of every remaining-life model, plus how sure we can be with 13 cutters.

All models are scored on the same rows (every recorded cycle the cutter survived, i.e. cycles left ≥ 1),
with the same definitions:
  whole life          mean |predicted − true cycles left|
  last 20% of life    the same, on cycles with (cycle number) ÷ (life) ≥ 0.8
  over-estimate       how much it said "more cycles left" than there were, in the last 20%
  by life stage       first, middle and last third of each cutter's life
Each cutter counts equally. Added here: LightGBM given exactly the TCN's physics inputs, so
"TCN vs LightGBM" compares the models, not their inputs. Every model of the model zoo
(scripts/20–23, results/predictions/zoo_*.parquet, named in results/models/zoo_registry_*.csv)
is picked up automatically and scored the same way.
Paired bootstrap over cutters (resample the 13 cutters 5,000 times): if the 95% interval of a
difference includes 0, that difference is within the noise of 13 cutters.

Writes results/models/comparison_per_cutter.csv, comparison_summary.csv and bootstrap.csv.
"""

import importlib.util
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("th", ROOT / "scripts" / "13_train_history.py")
th = importlib.util.module_from_spec(spec)
spec.loader.exec_module(th)

OUT = ROOT / "results" / "models"
PARAMS = dict(n_estimators=400, learning_rate=0.03, num_leaves=15, min_child_samples=20, subsample=0.8,
              subsample_freq=1, colsample_bytree=0.5, verbose=-1, random_state=0)
REF = "TCN: physics features"
# Family of each model, for the zoo table and figure (zoo models by their registry name).
GROUP = {
    "Survival model: settings + age": "No sensors", "TCN: settings + age only": "No sensors",
    "mean_residual_life": "No sensors", "tcn_age_only": "No sensors",
    "LightGBM: same inputs as the TCN": "Classical ML, TCN inputs",
    **{n: "Classical ML, TCN inputs" for n in ("ridge", "elastic_net", "svr", "gaussian_process", "random_forest",
                                               "lgbm_history", "lgbm_quantile", "knn_similarity", "hi_threshold")},
    "LightGBM: 120 summaries only": "120 released summaries",
    **{n: "120 released summaries" for n in ("lgbm_summaries", "lgbm_history_summaries", "tcn_summaries")},
    REF: "Neural networks, TCN inputs",
    **{n: "Neural networks, TCN inputs" for n in ("linear_hazard", "mlp_now", "gru", "lstm", "transformer", "tcn_direct")},
    "TCN: autoencoder health score": "TCN, other inputs", "TCN: physics + autoencoder": "TCN, other inputs",
    **{n: "TCN, other inputs" for n in ("tcn_currents_only", "tcn_vibration_only", "tcn_no_age",
                                         "tcn_pretrained", "tcn_shared_inputs")},
    "raw_cnn": "Raw vibration, end to end",
}
# Clearer names on the slides than the registry's.
RENAME = {"lgbm_summaries": "LightGBM: 120 summaries + settings + age",
          "lgbm_history_summaries": "LightGBM + history: 120 summaries + settings + age",
          "tcn_pretrained": "TCN pretrained on 73 other lives", "tcn_shared_inputs": "TCN + 3 shared signals (control)"}
SKIP = {"lgbm_plain", "tcn"}  # same models as "LightGBM: same inputs as the TCN" and "TCN: physics features"


def lgbm_same_inputs() -> pd.DataFrame:
    df, cols = th.load("physics")
    df = df[df["rul"] >= 1]
    out = []
    for held in sorted(df["tool"].unique()):
        tr, te = df[df["tool"] != held], df[df["tool"] == held]
        m = lgb.LGBMRegressor(**PARAMS).fit(tr[cols], tr["rul"])
        out.append(te[["tool", "age", "rul", "life"]].assign(pred=np.clip(m.predict(te[cols]), 0, None)))
    return pd.concat(out)


def all_predictions() -> dict[str, pd.DataFrame]:
    preds = {}
    for name, label in (("physics", REF), ("ae", "TCN: autoencoder health score"),
                        ("physics_ae", "TCN: physics + autoencoder"), ("settings_age", "TCN: settings + age only")):
        path = ROOT / "results" / "predictions" / f"history_{name}.parquet"
        if path.exists():
            p = pd.read_parquet(path).rename(columns={"run_idx": "age", "rul_q50": "pred"})
            preds[label] = p[["tool", "age", "rul", "life", "pred"]]
    base = pd.read_csv(ROOT / "results" / "baselines" / "predictions.csv")
    life = base.groupby("tool")["rul"].max() + 1
    for model, label in (("lgbm_sensors", "LightGBM: 120 summaries only"), ("settings_age", "Survival model: settings + age")):
        b = base[(base.model == model) & (base.rul >= 1)].copy()
        b["life"] = b["tool"].map(life)
        preds[label] = b[["tool", "age", "rul", "life", "pred"]]
    preds["LightGBM: same inputs as the TCN"] = lgbm_same_inputs()
    labels = {}
    for reg in sorted(OUT.glob("zoo_registry_*.csv")):
        r = pd.read_csv(reg)
        labels.update(dict(zip(r["name"], r["label"])))
    for path in sorted((ROOT / "results" / "predictions").glob("zoo_*.parquet")):
        name = path.stem.removeprefix("zoo_")
        if name in SKIP or name not in labels:
            continue
        p = pd.read_parquet(path)
        label = f"Zoo: {RENAME.get(name, labels[name])}"
        GROUP[label] = GROUP.get(name, "Other")
        preds[label] = p[p["rul"] >= 1][["tool", "age", "rul", "life", "pred"]]
    return preds


def per_cutter(p: pd.DataFrame) -> pd.DataFrame:
    p = p.drop_duplicates(["tool", "age"])
    frac = (p["age"] + 1) / p["life"]
    err = p["pred"] - p["rul"]
    p = p.assign(err=err, abserr=err.abs(), frac=frac)
    rows = []
    for t, g in p.groupby("tool"):
        near = g[g.frac >= 0.8]
        rows.append(dict(tool=t, whole_life=g.abserr.mean(), last20=near.abserr.mean(),
                         over_last20=near.err.clip(lower=0).mean(),
                         first_third=g[g.frac < 1 / 3].abserr.mean(),
                         middle_third=g[(g.frac >= 1 / 3) & (g.frac < 2 / 3)].abserr.mean(),
                         last_third=g[g.frac >= 2 / 3].abserr.mean(),
                         error_share_of_life=g.abserr.mean() / g.life.iloc[0]))
    return pd.DataFrame(rows).set_index("tool")


def main() -> None:
    preds = all_predictions()
    pcs = {k: per_cutter(v) for k, v in preds.items()}
    long = pd.concat({k: v for k, v in pcs.items()}, names=["model"]).reset_index()
    long.to_csv(OUT / "comparison_per_cutter.csv", index=False)
    summary = long.groupby("model").mean(numeric_only=True).drop(columns="tool").round(2).sort_values("whole_life")
    summary.insert(0, "group", [GROUP.get(m, "Other") for m in summary.index])
    summary.to_csv(OUT / "comparison_summary.csv")
    print(summary.to_string())

    rng = np.random.default_rng(0)
    rows = []
    ref = pcs[REF]
    for other, pc in pcs.items():
        if other == REF:
            continue
        for metric in ("whole_life", "last20", "middle_third", "over_last20"):
            d = (ref[metric] - pc[metric]).dropna()
            boots = np.array([d.to_numpy()[rng.integers(0, len(d), len(d))].mean() for _ in range(5000)])
            rows.append(dict(comparison=f"{REF} minus {other}", metric=metric, mean_diff=d.mean(),
                             ci_low=np.percentile(boots, 2.5), ci_high=np.percentile(boots, 97.5),
                             tcn_better_on=int((d < 0).sum()), cutters=len(d)))
    bs = pd.DataFrame(rows).round(2)
    bs.to_csv(OUT / "bootstrap.csv", index=False)
    print(bs.to_string(index=False))


if __name__ == "__main__":
    main()
