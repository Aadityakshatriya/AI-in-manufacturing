"""Yardstick models for remaining useful life (RUL), tested by hiding one whole cutter at a time.

Models
  avg_life        : every cutter lives as long as the average training cutter
  settings_age    : Weibull survival model on cutting settings; predicts the median remaining life
                    given that the cutter has already survived `age` cycles
  lgbm_settings   : LightGBM on settings + age (no sensors)
  lgbm_sensors    : LightGBM on the 120 sensor summaries only (no age, no settings)
  lgbm_all        : LightGBM on sensors + settings + age

Writes per-cutter and summary tables to results/baselines/.
"""

import sys
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from lifelines import WeibullAFTFitter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.rzeszow import ROOT, SETTING_COLS, load_table, sensor_columns, usable

warnings.filterwarnings("ignore")
OUT = ROOT / "results" / "baselines"
OUT.mkdir(parents=True, exist_ok=True)

df = usable(load_table())
SENSORS = sensor_columns(df)
LGB_PARAMS = dict(
    n_estimators=400, learning_rate=0.03, num_leaves=15, min_child_samples=20,
    subsample=0.8, subsample_freq=1, colsample_bytree=0.5, verbose=-1, random_state=0,
)


def avg_life(train, test):
    mean_life = train.groupby("tool")["life"].first().mean()
    return np.clip(mean_life - 1 - test["age"].to_numpy(), 0, None)


def settings_age(train, test):
    lives = train.groupby("tool").first().reset_index()
    cols = [c for c in SETTING_COLS if lives[c].nunique() > 1]
    fit_df = lives[cols + ["life"]].assign(event=1)
    model = WeibullAFTFitter(penalizer=0.1).fit(fit_df, duration_col="life", event_col="event")
    # Median of total life given the cutter has survived `age + 1` cycles, minus what it has used.
    survived = test["age"].to_numpy() + 1
    med_total = model.predict_median(test[cols], conditional_after=survived).to_numpy().ravel()
    return np.clip(med_total - 1, 0, None)


def lgbm(features):
    def run(train, test):
        m = lgb.LGBMRegressor(**LGB_PARAMS).fit(train[features], train["rul"])
        return np.clip(m.predict(test[features]), 0, None)

    return run


MODELS = {
    "avg_life": avg_life,
    "settings_age": settings_age,
    "lgbm_settings": lgbm(SETTING_COLS + ["age"]),
    "lgbm_sensors": lgbm(SENSORS),
    "lgbm_all": lgbm(SENSORS + SETTING_COLS + ["age"]),
}

rows, preds = [], []
for held in sorted(df["tool"].unique()):
    train, test = df[df["tool"] != held], df[df["tool"] == held]
    for name, fn in MODELS.items():
        p = fn(train, test)
        err = p - test["rul"].to_numpy()
        near = test["life_frac_used"].to_numpy() >= 0.8
        rows.append(
            dict(
                model=name, tool=held, life=test["life"].iloc[0],
                mae=np.abs(err).mean(), rmse=np.sqrt((err**2).mean()),
                mae_last20pct=np.abs(err[near]).mean(),
                # Over-estimating life near the end is the dangerous mistake.
                overestimate_last20pct=np.clip(err[near], 0, None).mean(),
                mae_frac_of_life=np.abs(err).mean() / test["life"].iloc[0],
            )
        )
        preds.append(test[["tool", "cycle", "age", "rul"]].assign(model=name, pred=p))

per_tool = pd.DataFrame(rows)
per_tool.to_csv(OUT / "per_cutter.csv", index=False)
pd.concat(preds).to_csv(OUT / "predictions.csv", index=False)

summary = (
    per_tool.groupby("model")[["mae", "rmse", "mae_last20pct", "overestimate_last20pct", "mae_frac_of_life"]]
    .mean()
    .loc[list(MODELS)]
    .round(2)
)
summary.to_csv(OUT / "summary.csv")
print("Average over 13 hidden cutters (each cutter weighted equally), errors in cycles:")
print(summary.to_string())
print()
print(per_tool.pivot(index="tool", columns="model", values="mae")[list(MODELS)].round(1).to_string())
