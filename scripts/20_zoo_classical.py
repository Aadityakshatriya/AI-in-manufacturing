"""Classical (non-neural) remaining-life models, tested exactly like the TCN.

The TCN predicts a hidden cutter's cycles left to within about 20 cycles over its whole life (about 13
in its last 20%). Before crediting the network, we ask what well-known simpler methods reach on the
same data and the same test. Each method believes something different about how a cutter dies, so
each result is also a small physics finding:

  mean_residual_life  no sensors, no settings: of the training cutters that lived at least this long,
                      how many more cycles did they do on average?
  ridge, elastic_net  one straight-line formula on the TCN's inputs
  hi_threshold        textbook prognostics: extend the recent trend of the table motor current until it
                      reaches the level at which training cutters broke
  knn_similarity      find stretches of training cutters whose recent signals looked like this
                      cutter's, and read off how many cycles those cutters had left
  random_forest       many averaged decision trees on the TCN's inputs
  lgbm_plain          LightGBM on the TCN's inputs (the control for lgbm_history; same settings as
                      scripts/18_fair_comparison.py, one thread)
  lgbm_history        the same plus hand-made history (recent means and slopes, highest table current
                      so far): is the TCN's edge just that it sees history?
  lgbm_summaries      LightGBM on the 120 released per-cycle summaries + settings + log age: the inputs on
                      which LightGBM matched the TCN (20.2 in scripts/18_fair_comparison.py, without
                      settings and age). Feature choice and model choice are confounded, so ...
  lgbm_history_summaries  ... the history test is repeated on these inputs too: the 6 summaries LightGBM
                      found most useful on the 12 training cutters, with their recent means, slopes and
                      highest value so far added
  svr                 support vector regression with an RBF kernel on the TCN's inputs (the comparator
                      used in the dataset paper)
  gaussian_process    a smooth similarity model on a few inputs, with a 10%-90% range
  lgbm_quantile       LightGBM predicting the 10th, 50th and 90th percentile directly

Test (as in scripts/18_fair_comparison.py): hide one cutter, fit everything on the other 12 (scaling,
hyperparameters, thresholds), predict every cycle the hidden cutter survived (cycles left >= 1) using
only its cycles so far. Hyperparameters with a `grid` in MODELS below are chosen by hiding each of the 12
training cutters in turn (inner leave-one-cutter-out, lowest whole-life error); everything else is a fixed,
modest default. Every prediction is clipped at 0.
Rule for every fit, inner and outer: inputs that never vary across the training cutters are dropped
before scaling. Cutter 10 is the only one on the 160 mm holder; when it is hidden, holder length is
constant in training, and scaling would turn its 160 into a value 80 "standard deviations" away.

Usage: python scripts/20_zoo_classical.py [--only ridge,knn_similarity] [--workers 3]
Writes results/predictions/zoo_<name>.parquet (tool, age, rul, life, pred [, q10, q90]) and
results/models/zoo_registry_classical.csv (one row per model; --only updates just those rows).
"""

import argparse
import importlib.util
import os
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

# Shared machine: one thread per worker process.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_var] = "1"

import lightgbm as lgb
import numpy as np
import pandas as pd
import torch
from numpy.lib.stride_tricks import sliding_window_view
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _script(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


th = _script("th", "13_train_history.py")   # load(), SETTINGS
from toollife.rzeszow import load_table, sensor_columns  # noqa: E402  (the 120 released summaries)
fc = _script("fc", "18_fair_comparison.py")  # per_cutter() scoring, LightGBM settings
torch.set_num_threads(1)  # 13_train_history sets 4 when imported

LGBM = dict(fc.PARAMS, n_jobs=1)
CAP = 160  # longest life seen is 150 cycles
HI = "lr_table_cut_a"  # health indicator: table motor current while cutting, log ratio to when new
TOP_SUMMARIES = 6  # how many released summaries get history features in lgbm_history_summaries
MIN_POINTS = 5  # fewest cycles to fit a trend line through
KNN_FEATURES = ["lr_table_cut_a", "lr_spindle_net_a", "lr_X_Driving_axle_pZ__rms"]
# Gaussian process inputs: settings, age, and six physics signals chosen by physics (not by looking at
# the answers): table and spindle current, energy per mm3, table vibration, the once-per-turn beat of a
# chipped tooth, spindle vibration.
GP_PHYSICS = ["lr_table_cut_a", "lr_spindle_net_a", "lr_spindle_charge_per_mm3",
              "lr_X_Driving_axle_pZ__rms", "lr_X_Driving_axle_pZ__order1", "lr_Spindle_mX__rms"]
GP_INPUTS = th.SETTINGS + ["log_age"] + GP_PHYSICS


# ---------------------------------------------------------------- data

def trailing_slope(x: np.ndarray, y: np.ndarray, w: int) -> np.ndarray:
    """Least-squares slope of y per cycle over the last w points (fewer at the start; 0 for one point)."""
    out = np.zeros(len(y))
    for i in range(1, len(y)):
        xs, ys = x[max(0, i - w + 1): i + 1], y[max(0, i - w + 1): i + 1]
        dx = xs - xs.mean()
        out[i] = (dx * (ys - ys.mean())).sum() / (dx ** 2).sum()
    return out


def add_history(df: pd.DataFrame, cols: list[str], max_cols: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Per cutter, from its own cycles so far only: mean and slope (per cycle) over the last 5 and 15 cycles
    of each of `cols`, and the highest value seen so far of each of `max_cols`."""
    parts = []
    for _, g in df.sort_values(["tool", "age"]).groupby("tool", sort=False):
        x = g["age"].to_numpy(float)
        h = {}
        for w in (5, 15):
            for c in cols:
                h[f"{c}_mean{w}"] = g[c].rolling(w, min_periods=1).mean().to_numpy()
                h[f"{c}_slope{w}"] = trailing_slope(x, g[c].to_numpy(), w)
        for c in max_cols:
            h[f"{c}_max_so_far"] = g[c].cummax().to_numpy()
        parts.append(pd.DataFrame(h, index=g.index))
    hist = pd.concat(parts)
    return pd.concat([df, hist], axis=1), list(hist.columns)


def prepare() -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """The TCN's per-cycle table with the 120 released summaries joined on, and the input lists:
    "tcn" (the TCN's 29 inputs), "tcn_history" (plus history features), "summaries" (120 + settings + log age)."""
    df, cols = th.load("physics")
    df = df.sort_values(["tool", "age"]).reset_index(drop=True)
    # One cycle (cutter 103, cycle 37) has no physics values: repeat that cutter's previous cycle (causal).
    df[cols] = df.groupby("tool")[cols].ffill()
    df, hist = add_history(df, [c for c in cols if c.startswith("lr_")], [HI])
    table = load_table()
    summaries = sensor_columns(table)
    df = df.merge(table[["file"] + summaries], on="file", how="left", validate="many_to_one")
    df[summaries] = df.groupby("tool")[summaries].ffill()
    return df, {"tcn": cols, "tcn_history": cols + hist, "summaries": th.SETTINGS + ["log_age"] + summaries,
                "knn": KNN_FEATURES, "gp": GP_INPUTS}


def scored(d: pd.DataFrame) -> pd.DataFrame:
    """Cycles the cutter survived (cycles left >= 1): the rows every model is trained and scored on."""
    return d[d["rul"] >= 1]


def varying(train: pd.DataFrame, inputs: list[str]) -> list[str]:
    """The inputs that take more than one value across the training cutters (see the rule above)."""
    tr = scored(train)
    return [c for c in inputs if tr[c].nunique() > 1]


def frame(rows: pd.DataFrame, pred, q10=None, q90=None) -> pd.DataFrame:
    out = rows[["tool", "age", "rul", "life"]].copy()
    out["pred"] = np.clip(pred, 0, None)
    if q10 is not None:
        out["q10"], out["q90"] = np.clip(q10, 0, None), np.clip(q90, 0, None)
    return out


def train_lives(train: pd.DataFrame) -> np.ndarray:
    return train.groupby("tool")["life"].first().to_numpy(float)


# ---------------------------------------------------------------- models
# Each predict_* takes (train, test, inputs, **hyperparameters) and returns (predictions, size).

def mean_residual(lives: np.ndarray, ages) -> np.ndarray:
    """Average further cycles done by the training cutters that outlived each age.

    After cycle a without breaking, the cutter's life is at least a + 2 (the breaking cycle is
    life - 1). Beyond the longest training life nobody is left to average: say 1 cycle ("overdue").
    """
    out = np.empty(len(ages))
    for i, a in enumerate(ages):
        alive = lives[lives >= a + 2]
        out[i] = (alive - a - 1).mean() if len(alive) else 1.0
    return out


def predict_mrl(train, test, inputs):
    rows = scored(test)
    lives = train_lives(train)
    return frame(rows, mean_residual(lives, rows["age"].to_numpy())), len(lives)


def predict_linear(train, test, inputs, alpha, l1_ratio=None):
    tr, rows = scored(train), scored(test)
    reg = Ridge(alpha=alpha) if l1_ratio is None else ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=50_000)
    m = make_pipeline(StandardScaler(), reg).fit(tr[inputs], tr["rul"])
    return frame(rows, m.predict(rows[inputs])), int((np.abs(m[-1].coef_) > 1e-9).sum())


def failure_level(train) -> float:
    """Median over training cutters of each one's median health indicator in its last 3 cycles before breaking."""
    last = scored(train).sort_values(["tool", "age"]).groupby("tool").tail(3)
    return float(last.groupby("tool")[HI].median().median())


def predict_hi(train, test, inputs, window, form):
    """Extend the hidden cutter's recent health-indicator trend to the training failure level.

    form "linear": the current ratio (to new) grows in a straight line; "exponential": it grows by a
    fixed percentage per cycle, i.e. its log (the health indicator itself) grows in a straight line.
    Falls back to the training mean residual life when the trend is flat or falling, or too short.
    """
    level = failure_level(train)
    lives = train_lives(train)
    g = test.sort_values("age")
    x = g["age"].to_numpy(float)
    y = g[HI].to_numpy() if form == "exponential" else np.exp(g[HI].to_numpy())
    target = level if form == "exponential" else np.exp(level)
    keep = np.flatnonzero(g["rul"].to_numpy() >= 1)
    pred = np.empty(len(keep))
    for n, i in enumerate(keep):
        xs, ys = x[max(0, i - window + 1): i + 1], y[max(0, i - window + 1): i + 1]
        slope = 0.0
        if len(xs) >= MIN_POINTS:
            dx = xs - xs.mean()
            slope = (dx * (ys - ys.mean())).sum() / (dx ** 2).sum()
        if slope <= 0:
            pred[n] = mean_residual(lives, [x[i]])[0]
        else:
            now = ys.mean() + slope * (x[i] - xs.mean())  # the trend line's value at this cycle
            pred[n] = np.clip((target - now) / slope, 0, CAP)
    return frame(g.iloc[keep], pred), round(level, 3)


def predict_knn(train, test, inputs, window, k):
    """Trajectory similarity (Wang et al. 2008): compare the hidden cutter's last `window` cycles with every
    same-length stretch of every training cutter; average the cycles left at the end of the k closest
    stretches, weighted by 1 / (distance + 0.01). Early on, fewer cycles exist: compare what exists."""
    tr = scored(train)
    mean, std = tr[inputs].mean(), tr[inputs].std()
    library = [(((g[inputs] - mean) / std).to_numpy(), g["rul"].to_numpy(float)) for _, g in tr.groupby("tool")]
    z = ((test.sort_values("age")[inputs] - mean) / std).to_numpy()
    rows = scored(test).sort_values("age")
    pred = np.empty(len(rows))
    for i in range(len(rows)):
        w = min(window, i + 1)
        recent = z[i - w + 1: i + 1]
        dists, left = [], []
        for zl, rul in library:
            if len(zl) < w:
                continue
            stretches = sliding_window_view(zl, (w, zl.shape[1]))[:, 0]  # stretch s ends at row s + w - 1
            dists.append(((stretches - recent) ** 2).mean(axis=(1, 2)))
            left.append(rul[w - 1:])
        d, left = np.concatenate(dists), np.concatenate(left)
        near = np.argsort(d, kind="stable")[:k]
        wt = 1.0 / (d[near] + 0.01)
        pred[i] = (wt * left[near]).sum() / wt.sum()
    return frame(rows, pred), len(tr)


def predict_forest(train, test, inputs):
    tr, rows = scored(train), scored(test)
    m = RandomForestRegressor(n_estimators=300, min_samples_leaf=5, max_features=0.33, n_jobs=1,
                              random_state=0).fit(tr[inputs], tr["rul"])
    return frame(rows, m.predict(rows[inputs])), sum(e.get_n_leaves() for e in m.estimators_)


def predict_lgbm(train, test, inputs):
    tr, rows = scored(train), scored(test)
    m = lgb.LGBMRegressor(**LGBM).fit(tr[inputs], tr["rul"])
    return frame(rows, m.predict(rows[inputs])), m.booster_.num_trees()


def predict_lgbm_history_summaries(train, test, inputs):
    """LightGBM on the summaries, plus history of the TOP_SUMMARIES summaries with the most split gain in a
    plain LightGBM fitted on the training cutters (chosen per fold, never looking at the hidden cutter)."""
    tr = scored(train)
    plain = lgb.LGBMRegressor(**LGBM).fit(tr[inputs], tr["rul"])
    gain = pd.Series(plain.booster_.feature_importance("gain"), index=inputs)
    top = list(gain[[c for c in inputs if c.startswith(("Accelerometer", "Current"))]].nlargest(TOP_SUMMARIES).index)
    train, hist = add_history(train, top, top)
    test, _ = add_history(test, top, top)
    pred, _ = predict_lgbm(train, test, inputs + hist)
    return pred, tuple(top)


def predict_lgbm_quantile(train, test, inputs):
    tr, rows = scored(train), scored(test)
    q = {a: lgb.LGBMRegressor(objective="quantile", alpha=a, **LGBM).fit(tr[inputs], tr["rul"]).predict(rows[inputs])
         for a in (0.1, 0.5, 0.9)}
    # Separately trained quantiles can cross; keep the range around the middle estimate.
    return frame(rows, q[0.5], np.minimum(q[0.1], q[0.5]), np.maximum(q[0.9], q[0.5])), 3 * LGBM["n_estimators"]


def predict_gp(train, test, inputs):
    """RBF kernel with one length per input (ARD) plus noise; the 10%-90% range is mean -/+ 1.28 std."""
    tr, rows = scored(train), scored(test)
    scale = StandardScaler().fit(tr[inputs])
    kernel = (ConstantKernel(1.0, (1e-2, 1e2)) * RBF(np.ones(len(inputs)), (1e-2, 1e3))
              + WhiteKernel(0.1, (1e-4, 10.0)))
    gp = GaussianProcessRegressor(kernel, normalize_y=True, random_state=0)
    gp.fit(scale.transform(tr[inputs]), tr["rul"].to_numpy(float))
    mu, sd = gp.predict(scale.transform(rows[inputs]), return_std=True)
    return frame(rows, mu, mu - 1.2816 * sd, mu + 1.2816 * sd), len(tr)


def predict_svr(train, test, inputs, C, gamma):
    """RBF-kernel support vector regression on standardized inputs; errors under 1 cycle are ignored."""
    tr, rows = scored(train), scored(test)
    m = make_pipeline(StandardScaler(), SVR(kernel="rbf", C=C, gamma=gamma, epsilon=1.0)).fit(tr[inputs], tr["rul"])
    return frame(rows, m.predict(rows[inputs])), len(m[-1].support_)


TCN_INPUTS = ("TCN physics inputs (29: 18 causal relative signals = log of each signal over the cutter's own first clean "
              "cycles, 4 absolute vibration-shape stats, first-ring flag, 5 settings, log_age)")
SUMMARY_INPUTS = ("120 released summaries (raw per-cycle min/max/mean/std/skew/kurtosis of 8 accelerometers and "
                  "12 motor currents, not relative to new) + 5 settings + log_age (126)")


def _top_summaries(sizes) -> str:
    counts = Counter(c for top in sizes for c in top)
    return "; ".join(f"{c} ({n}/13)" for c, n in counts.most_common(8))
MODELS = {
    "mean_residual_life": dict(
        predict=predict_mrl, label="Mean residual life (age only)", family="survival / life table",
        inputs="age only (the 12 training lives)", uses_history="no",
        assumes="Every cutter's life is a draw from the same pool, so cycles left depend only on how many cycles it has already survived.",
        size=lambda s: "12 stored training lives"),
    "ridge": dict(
        predict=predict_linear, grid=[dict(alpha=a) for a in (0.1, 1, 10, 100, 1e3, 1e4, 1e5)],
        label="Ridge regression", family="linear", inputs=TCN_INPUTS, uses_history="no",
        assumes="Cycles left is one weighted sum of today's currents, vibrations, settings and log age, the same straight-line rule for every cutter.",
        size=lambda s: "30 numbers (29 weights + intercept)"),
    "elastic_net": dict(
        predict=predict_linear,
        grid=[dict(alpha=a, l1_ratio=r) for a in (0.01, 0.1, 0.3, 1, 3) for r in (0.1, 0.5, 0.9)],
        label="Elastic net", family="linear (sparse)", inputs=TCN_INPUTS, uses_history="no",
        assumes="Cycles left is a weighted sum of today's inputs in which only a few inputs matter.",
        size=lambda s: f"{np.median(s):.0f} of 29 weights non-zero (median over folds) + intercept"),
    "hi_threshold": dict(
        predict=predict_hi, grid=[dict(window=w, form=f) for w in (8, 12, 16, 20, 28) for f in ("linear", "exponential")],
        label="Health indicator + failure threshold", family="degradation extrapolation",
        inputs="table motor current relative to new, last W cycles; training lives for the fallback", uses_history="yes",
        assumes="The cutter dies when the table motor current reaches a fixed level, and its recent trend continues smoothly until it gets there.",
        size=lambda s: f"3 numbers (failure level {np.min(s):.2f}-{np.max(s):.2f} as log ratio, window, trend form)"),
    "knn_similarity": dict(
        predict=predict_knn, features="knn", grid=[dict(window=w, k=k) for w in (5, 10, 20, 30) for k in (5, 10, 20, 40)],
        label="Trajectory similarity (k nearest stretches)", family="instance-based",
        inputs="last W cycles of table current, spindle current, table vibration (relative to new)", uses_history="yes",
        assumes="A cutter whose recent current and vibration path looks like a past cutter's at some moment has about as many cycles left as that cutter had then.",
        size=lambda s: f"stores {np.mean(s):.0f} training cycles (mean over folds); window W and k chosen"),
    "random_forest": dict(
        predict=predict_forest, label="Random forest", family="tree ensemble (bagging)", inputs=TCN_INPUTS,
        uses_history="no",
        assumes="Cycles left is a step function of today's inputs alone; averaging many trees learned on resampled cycles smooths the steps.",
        size=lambda s: f"300 trees, {np.mean(s):.0f} leaves in total (mean over folds)"),
    "lgbm_plain": dict(
        predict=predict_lgbm, label="LightGBM, TCN inputs (control)", family="tree ensemble (boosting)",
        inputs=TCN_INPUTS, uses_history="no",
        assumes="Cycles left is a sum of many small step functions of today's inputs alone.",
        size=lambda s: "400 trees x up to 15 leaves"),
    "lgbm_history": dict(
        predict=predict_lgbm, features="tcn_history", label="LightGBM + hand-made history", family="tree ensemble (boosting)",
        inputs="TCN physics inputs (29) + mean and slope over the last 5 and 15 cycles of the 18 causal relative signals + highest table current so far (102)",
        uses_history="yes",
        assumes="Today's inputs plus simple summaries of the last 5-15 cycles (levels, trends, worst table current so far) say how close the cutter is to breaking.",
        size=lambda s: "400 trees x up to 15 leaves"),
    "lgbm_summaries": dict(
        predict=predict_lgbm, features="summaries", label="LightGBM, 120 summaries (control)",
        family="tree ensemble (boosting)", inputs=SUMMARY_INPUTS, uses_history="no",
        assumes="Cycles left is a sum of many small step functions of today's raw signal statistics, settings and age.",
        size=lambda s: "400 trees x up to 15 leaves"),
    "lgbm_history_summaries": dict(
        predict=predict_lgbm_history_summaries, features="summaries", label="LightGBM + history, 120 summaries",
        family="tree ensemble (boosting)",
        inputs=SUMMARY_INPUTS[:-6] + " + mean and slope over the last 5 and 15 cycles and highest value so far of the "
               f"{TOP_SUMMARIES} summaries with most split gain on the training cutters (156)",
        uses_history="yes",
        assumes="Today's raw signal statistics plus the recent level, trend and worst-so-far of the few most telling ones say how close the cutter is to breaking.",
        size=lambda s: f"400 trees x up to 15 leaves; history on: {_top_summaries(s)}"),
    "svr": dict(
        predict=predict_svr, grid=[dict(C=c, gamma=g) for c in (10, 100, 1000) for g in (0.01, 0.03, 0.1)],
        label="Support vector regression (RBF)", family="kernel", inputs=TCN_INPUTS, uses_history="no",
        assumes="Cycles left is a smooth function of today's inputs, built from the training cycles most similar to today's.",
        size=lambda s: f"{np.mean(s):.0f} support vectors (mean over folds) x 28-29 inputs"),
    "gaussian_process": dict(
        predict=predict_gp, features="gp", label="Gaussian process", family="kernel / Bayesian",
        inputs="5 settings, log age, 6 physics signals relative to new (12)", uses_history="no",
        assumes="Cutters with similar settings, age and current/vibration levels have similar cycles left, and cycles left changes smoothly as those inputs change.",
        size=lambda s: f"{np.mean(s):.0f} stored training cycles + one kernel length per input + 2"),
    "lgbm_quantile": dict(
        predict=predict_lgbm_quantile, label="LightGBM quantiles (10/50/90%)", family="tree ensemble (boosting)",
        inputs=TCN_INPUTS, uses_history="no",
        assumes="Today's inputs fix not just the likely cycles left but its spread, learned directly as the 10th, 50th and 90th percentiles.",
        size=lambda s: "3 x 400 trees x up to 15 leaves"),
}


# ---------------------------------------------------------------- test loop

def choose(train, predict, grid, inputs) -> dict:
    """The setting with the lowest whole-life error when each training cutter is hidden in turn."""
    tools = sorted(train["tool"].unique())
    scores = []
    for params in grid:
        preds = []
        for t in tools:
            inner = train[train["tool"] != t]
            preds.append(predict(inner, train[train["tool"] == t], varying(inner, inputs), **params)[0])
        preds = pd.concat(preds)
        scores.append(fc.per_cutter(preds)["whole_life"].mean())
    return grid[int(np.argmin(scores))]


def outer_fold(name: str, held, df: pd.DataFrame, feature_sets: dict[str, list[str]]):
    """Hide one cutter, fit on the other 12 (choosing hyperparameters on them if the model has a grid), predict it."""
    spec = MODELS[name]
    train, test = df[df["tool"] != held], df[df["tool"] == held]
    inputs = feature_sets[spec.get("features", "tcn")]
    t0 = time.perf_counter()
    params = choose(train, spec["predict"], spec["grid"], inputs) if spec.get("grid") else {}
    pred, size = spec["predict"](train, test, varying(train, inputs), **params)
    return pred, params, size, time.perf_counter() - t0


def describe_choices(choices: list[dict]) -> str:
    if not choices or not choices[0]:
        return "fixed"
    counts = Counter(tuple(sorted(c.items())) for c in choices)
    return "; ".join(f"{', '.join(f'{k}={v:g}' if isinstance(v, float) else f'{k}={v}' for k, v in p)} ({n}/13)"
                     for p, n in counts.most_common())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated model names; default: all of " + ", ".join(MODELS))
    ap.add_argument("--workers", type=int, default=3, help="parallel processes (capped at 3: shared machine)")
    args = ap.parse_args()
    names = args.only.split(",") if args.only else list(MODELS)
    unknown = [n for n in names if n not in MODELS]
    if unknown:
        sys.exit(f"unknown model(s): {unknown}")

    df, feature_sets = prepare()
    tools = sorted(df["tool"].unique())
    (ROOT / "results" / "predictions").mkdir(parents=True, exist_ok=True)
    registry, per_tool = [], {}
    with ProcessPoolExecutor(min(args.workers, 3)) as pool:
        futs = {n: [pool.submit(outer_fold, n, held, df, feature_sets) for held in tools] for n in names}
        for n in names:
            parts = [f.result() for f in futs[n]]
            pred = pd.concat([p for p, _, _, _ in parts]).sort_values(["tool", "age"]).reset_index(drop=True)
            pred.to_parquet(ROOT / "results" / "predictions" / f"zoo_{n}.parquet", index=False)
            pc = fc.per_cutter(pred)
            per_tool[n] = pc["whole_life"]
            spec = MODELS[n]
            row = dict(name=n, label=spec["label"], family=spec["family"], inputs=spec["inputs"],
                       uses_history=spec["uses_history"], what_it_assumes=spec["assumes"],
                       mae_whole_life=round(pc["whole_life"].mean(), 2), mae_last20=round(pc["last20"].mean(), 2),
                       size=spec["size"]([s for _, _, s, _ in parts]),
                       train_seconds=round(sum(t for _, _, _, t in parts), 1),
                       hyperparameters=describe_choices([c for _, c, _, _ in parts]))
            registry.append(row)
            extra = ""
            if "q10" in pred:
                inside = ((pred["rul"] >= pred["q10"]) & (pred["rul"] <= pred["q90"])).groupby(pred["tool"]).mean().mean()
                extra = f"  q10-q90 holds truth {inside:.0%} (aim 80%), width {(pred['q90'] - pred['q10']).mean():.0f}"
            print(f"{n:<19} whole {row['mae_whole_life']:6.2f}  last20 {row['mae_last20']:6.2f}  "
                  f"over_last20 {pc['over_last20'].mean():5.2f}  {row['train_seconds']:7.1f}s  [{row['hyperparameters']}]{extra}", flush=True)

    path = ROOT / "results" / "models" / "zoo_registry_classical.csv"
    reg = pd.DataFrame(registry)
    if path.exists():
        old = pd.read_csv(path)
        reg = pd.concat([old[~old["name"].isin(reg["name"])], reg])
    reg = reg.sort_values("name", key=lambda s: s.map(list(MODELS).index)).reset_index(drop=True)
    reg.to_csv(path, index=False)
    print("\nWhole-life error per hidden cutter (cycles):")
    print(pd.DataFrame(per_tool).round(1).to_string())
    print(f"\nwrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
