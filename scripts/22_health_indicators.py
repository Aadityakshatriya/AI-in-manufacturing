"""Five health indicators side by side: does the 4-million-number autoencoder see wear that simpler ones miss?

The question a reviewer will ask: "why a 4-million-parameter CNN autoencoder, when PCA (a linear
autoencoder) would do?" This script builds four simpler health indicators next to the autoencoder's,
under exactly the autoencoder's rules, and scores all five with the standard prognostics yardsticks.

Rules shared with scripts/11_train_autoencoder.py:
  - the same five fold groups; the model for group g is fitted without group g's cutters, and each
    cutter is scored only by its own group's model;
  - fitted only on "healthy" windows: the first 30% of each allowed cutter's life;
  - the same five table-side vibration sensors, each divided by one scale (its spread in the healthy
    sample); no per-window normalisation, because how loud the cut is matters.

The five indicators (one number per cycle; higher = less like a new cutter):
  pca_time         PCA with 64 components (the autoencoder's 64-number bottleneck) on the raw 5 x 4,096
                   windows; health = mean squared rebuild error. PCA is the best *linear* autoencoder,
                   so this is the autoencoder with its nonlinear layers taken out.
  pca_spectrum     the same on log power spectra (5 sensors x 256 bands of 49 Hz). A spectrum does not
                   care where in the window each tooth hit lands; raw-time PCA does.
  mahalanobis      distance of the cycle's 18 hand-made physics features (motor currents, vibration
                   levels, tooth-hit and once-per-turn strength, each relative to the cutter's own first
                   cycles) from the healthy cloud, with a Ledoit-Wolf covariance.
  cnn_autoencoder  the autoencoder's rebuild error, read from data/processed/ae_g*.parquet.
  table_current    table motor current relative to when new. No model at all.

All five are put on one footing before scoring: log of the value minus its median over the cutter's
first 3 cycles, i.e. "how far has it moved since new". Cycles that start a new ring of the workpiece
(file names ending _C1) are left out, as in scripts/14_health_figure.py.

Yardsticks. All are computed on unsmoothed values or on a trailing (causal) 5-cycle mean, never on
centred smoothing; the figure alone uses a centred 5-cycle mean, for display.
  monotonicity    |rises - falls| / (n - 1), per cutter then averaged (Coble & Hines 2009); 1 = never
                  turns back. Main column on the trailing mean, monotonicity_raw on unsmoothed values.
  trendability    do all cutters follow the same shape? (Coble & Hines 2009; Lei et al. 2018) Each
                  cutter's trailing-mean curve is resampled onto a common grid of life fraction (51
                  points, 0 to 1); trendability is the minimum, and trendability_mean the mean, of the
                  absolute correlations over all 78 pairs of cutters.
  prognosability  across cutters: exp(-spread of the value at failure / mean rise from new to failure),
                  on the trailing mean; 1 = every cutter fails at the same level, so one alarm threshold
                  would fit all.
  spearman        rank correlation of the unsmoothed indicator with fraction of life used, per cutter then
                  averaged; plus how many of the 13 cutters exceed 0.5.

Usage: python scripts/22_health_indicators.py [--recompute]
Writes results/models/health_indicators.csv (+ _per_cutter.csv), results/figures/health_indicators.png,
and caches the two PCA scores per cycle in data/processed/hi_pca.parquet (reused unless --recompute).
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "2")  # shared machine: stay within two cores

import argparse
import importlib.util
import sys
import time
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
from scipy import fft
from scipy.stats import spearmanr
from sklearn.covariance import LedoitWolf
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("th", ROOT / "scripts" / "13_train_history.py")
th = importlib.util.module_from_spec(spec)
spec.loader.exec_module(th)
from toollife.rzeszow import load_table

PROC = ROOT / "data" / "processed"
GROUPS = th.GROUPS
TABLE_SENSORS = [3, 4, 5, 6, 7]
HEALTHY = 0.3
N_COMP = 64        # same bottleneck size as the autoencoder's fingerprint
N_FIT = 3000       # healthy windows per raw-time PCA (each is 20,480 numbers)
BANDS = 256        # frequency bands per sensor
CHUNK = 960        # windows read from disk at a time (20 cycles, about 80 MB)
SMOOTH = 5         # cycles in the moving averages (trailing for metrics, centred for the figure only)
GRID = np.linspace(0, 1, 51)  # common life-fraction grid for trendability
INDICATORS = {
    "pca_time": "PCA on raw signal",
    "pca_spectrum": "PCA on spectrum",
    "mahalanobis": "Mahalanobis, physics features",
    "cnn_autoencoder": "CNN autoencoder (4M)",
    "table_current": "Table motor current",
}


def window_info() -> pd.DataFrame:
    index = pd.read_parquet(PROC / "windows_rzeszow_index.parquet")
    info = index.merge(load_table()[["file", "life"]], on="file", how="left")
    info["frac"] = (info["age"] + 1) / info["life"]
    return info


def healthy_rows(info: pd.DataFrame, g: int) -> np.ndarray:
    """Healthy windows of the cutters model g may learn from (not group g, never cutter 11)."""
    allowed = ~info["tool"].isin(GROUPS[g] + [11])
    return np.flatnonzero((allowed & (info["frac"] <= HEALTHY)).to_numpy())


def fit_time_pca(windows, info, g):
    """PCA on a random sample of healthy raw windows; returns (per-sensor scale, mean, components)."""
    rng = np.random.default_rng(g)
    rows = np.sort(rng.choice(healthy_rows(info, g), N_FIT, replace=False))
    x = windows[rows][:, TABLE_SENSORS].astype(np.float32)
    scale = x.std(axis=(0, 2))
    x = (x / scale[None, :, None]).reshape(len(x), -1)
    pca = PCA(N_COMP, svd_solver="randomized", random_state=g).fit(x)
    print(f"  group {g}: raw-time PCA keeps {pca.explained_variance_ratio_.sum():.0%} of healthy variance", flush=True)
    return scale, pca.mean_.astype(np.float32), pca.components_.astype(np.float32)


def rebuild_error(z: np.ndarray, mean: np.ndarray, comp: np.ndarray) -> np.ndarray:
    """Mean squared error after squeezing through the components and back (a linear autoencoder)."""
    z = z - mean
    r = z - (z @ comp.T) @ comp
    return (r**2).mean(1)


def log_spectrum(x: np.ndarray) -> np.ndarray:
    """[n, 5, 4096] -> [n, 5 * 256] log power, in bands of 8 frequency bins (49 Hz)."""
    p = np.abs(fft.rfft(x, axis=-1, workers=2)) ** 2
    p = p[..., 1:].reshape(len(x), x.shape[1], BANDS, -1).mean(-1)  # drop the constant (0 Hz) term
    return np.log(p + 1e-12).reshape(len(x), -1).astype(np.float32)


def pca_scores() -> pd.DataFrame:
    """Per-cycle raw-time and spectrum PCA rebuild errors, each cutter scored by its own group's model."""
    windows = np.load(PROC / "windows_rzeszow.npy", mmap_mode="r")
    info = window_info()
    t0 = time.time()
    time_models = {g: fit_time_pca(windows, info, g) for g in GROUPS}
    print(f"raw-time PCAs fitted ({time.time() - t0:.0f}s); one pass over all windows ...", flush=True)

    tools = info["tool"].to_numpy()
    spec_all = np.zeros((len(info), len(TABLE_SENSORS) * BANDS), np.float32)
    err_time = np.full(len(info), np.nan)
    for a in range(0, len(info), CHUNK):
        b = min(a + CHUNK, len(info))
        x = np.asarray(windows[a:b, TABLE_SENSORS], dtype=np.float32)
        spec_all[a:b] = log_spectrum(x)
        for g, (scale, mean, comp) in time_models.items():
            m = np.isin(tools[a:b], GROUPS[g])
            if m.any():
                z = (x[m] / scale[None, :, None]).reshape(m.sum(), -1)
                err_time[a + np.flatnonzero(m)] = rebuild_error(z, mean, comp)
    print(f"pass done ({time.time() - t0:.0f}s); spectrum PCAs ...", flush=True)

    # Log spectra need no per-sensor scale: dividing a sensor by a constant only shifts its log
    # spectrum, and PCA subtracts the healthy mean anyway.
    err_spec = np.full(len(info), np.nan)
    for g in GROUPS:
        pca = PCA(N_COMP, random_state=g).fit(spec_all[healthy_rows(info, g)])
        rows = np.flatnonzero(np.isin(tools, GROUPS[g]))
        err_spec[rows] = rebuild_error(spec_all[rows], pca.mean_.astype(np.float32), pca.components_.astype(np.float32))
        print(f"  group {g}: spectrum PCA keeps {pca.explained_variance_ratio_.sum():.0%} of healthy variance", flush=True)

    w = info[["file", "tool"]].assign(pca_time=err_time, pca_spectrum=err_spec)
    return w[w["tool"] != 11].groupby("file", as_index=False)[["pca_time", "pca_spectrum"]].mean()


def mahalanobis(cycles: pd.DataFrame) -> pd.Series:
    """Distance of each cycle's relative physics features from the healthy cycles of the other groups."""
    cols = [f"lr_{c}" for c in th.PHYS_REL]
    out = pd.Series(np.nan, index=cycles.index)
    for g, tools in GROUPS.items():
        fit = cycles[~cycles["tool"].isin(tools) & (cycles["life_frac"] <= HEALTHY)][cols].dropna()
        lw = LedoitWolf().fit(fit.to_numpy())
        test = cycles[cycles["tool"].isin(tools)][cols].dropna()
        out[test.index] = np.sqrt(lw.mahalanobis(test.to_numpy()))
    return out


def autoencoder_health(cycles: pd.DataFrame) -> tuple[pd.Series, str]:
    parts, stamps = [], []
    for g, tools in GROUPS.items():
        path = PROC / f"ae_g{g}.parquet"
        stamps.append(f"g{g} {datetime.fromtimestamp(path.stat().st_mtime):%d %b %H:%M}")
        ae = pd.read_parquet(path)[["file", "health"]]
        parts.append(ae[ae["file"].isin(cycles.loc[cycles["tool"].isin(tools), "file"])])
    health = cycles[["file"]].merge(pd.concat(parts), on="file", how="left")["health"]
    return pd.Series(health.to_numpy(), index=cycles.index), ", ".join(stamps)


def on_one_footing(cycles: pd.DataFrame) -> pd.DataFrame:
    """Each indicator as log(value) minus its median over the cutter's first 3 cycles; ring starts dropped."""
    d = cycles[~cycles["file"].str.endswith("_C1")].sort_values(["tool", "age"]).copy()
    for name in INDICATORS:
        v = d[name] if name == "table_current" else np.log(d[name])  # table current is already a log ratio
        base = v.groupby(d["tool"]).transform(lambda s: s.head(3).median())
        d[name] = v - base
    return d


def trailing(v: np.ndarray) -> np.ndarray:
    """Mean of this cycle and the previous SMOOTH - 1: uses no later cycles."""
    return pd.Series(v).rolling(SMOOTH, min_periods=1).mean().to_numpy()


def centred(v: np.ndarray) -> np.ndarray:
    """For the figure only."""
    return pd.Series(v).rolling(SMOOTH, center=True, min_periods=1).mean().to_numpy()


def monotonicity(v: np.ndarray) -> float:
    step = np.diff(v)
    return abs((step > 0).sum() - (step < 0).sum()) / (len(v) - 1)


def score(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    per_cutter, summary = [], []
    for name, label in INDICATORS.items():
        ends, curves = [], []
        for t, g in d.groupby("tool"):
            g = g.dropna(subset=[name])
            v = g[name].to_numpy()
            s = trailing(v)
            per_cutter.append(dict(
                indicator=name, tool=t, cycles=len(g),
                monotonicity=monotonicity(s), monotonicity_raw=monotonicity(v),
                spearman=spearmanr(g["life_frac"], v)[0], rise_to_failure=s[-1] - s[0],
            ))
            ends.append((s[0], s[-1]))
            curves.append(np.interp(GRID, g["life_frac"].to_numpy(), s))
        ends = np.array(ends)
        pair_r = np.abs(np.corrcoef(np.array(curves)))[np.triu_indices(len(curves), 1)]
        pc = pd.DataFrame([r for r in per_cutter if r["indicator"] == name])
        summary.append(dict(
            indicator=name, label=label,
            monotonicity=pc["monotonicity"].mean(), monotonicity_raw=pc["monotonicity_raw"].mean(),
            trendability=np.nanmin(pair_r), trendability_mean=np.nanmean(pair_r),
            prognosability=np.exp(-ends[:, 1].std() / np.abs(ends[:, 1] - ends[:, 0]).mean()),
            spearman=pc["spearman"].mean(), spearman_median=pc["spearman"].median(),
            cutters_spearman_over_05=int((pc["spearman"] > 0.5).sum()), cutters=len(pc),
        ))
    return pd.DataFrame(summary), pd.DataFrame(per_cutter)


def figure(d: pd.DataFrame, summary: pd.DataFrame, path: Path) -> None:
    """One panel per indicator (centred 5-cycle mean, for display only) and a sixth with the yardsticks."""
    plt.rcParams.update({"font.size": 13, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.4))
    axes = axes.ravel()
    ratio = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}×")
    for ax, (name, label) in zip(axes, INDICATORS.items()):
        row = summary.set_index("indicator").loc[name]
        for t, g in d.groupby("tool"):
            g = g.dropna(subset=[name])
            style = (dict(color="#b4321f", lw=2.4, zorder=3, label="cutter 10 (long holder)") if t == 10
                     else dict(color="#2f4a5c", lw=1.3, alpha=0.55))
            ax.plot(g["life_frac"], np.exp(centred(g[name].to_numpy())), **style)
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(matplotlib.ticker.LogLocator(subs=(1, 2, 5)))
        ax.yaxis.set_major_formatter(ratio)
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.axhline(1, color="grey", lw=0.7)
        ax.set_title(f"{label}\nrises in {row.cutters_spearman_over_05} of {row.cutters} cutters", loc="left", fontsize=13)
        ax.set_xlim(0, 1)
        ax.grid(axis="y", color="#e6e6e6", lw=0.6)
    for ax in axes[3:5]:
        ax.set_xlabel("fraction of life used")
    axes[2].set_xlabel("fraction of life used")
    for ax in (axes[0], axes[3]):
        ax.set_ylabel("× its value when new")
    axes[0].legend(frameon=False, loc="upper left", fontsize=11)

    # Sixth panel: the yardsticks as a small table (1 is best for all).
    t = axes[5]
    t.axis("off")
    cols = [("monotonicity", "monot."), ("trendability", "trend\n(min)"), ("prognosability", "prog."), ("spearman", "Spear-\nman")]
    cells = [[f"{r[c]:.2f}" for c, _ in cols] for _, r in summary.iterrows()]
    short = {"pca_time": "PCA raw", "pca_spectrum": "PCA spectrum", "mahalanobis": "Mahalanobis",
             "cnn_autoencoder": "CNN autoenc.", "table_current": "Table current"}
    tab = t.table(cellText=cells, rowLabels=[short[n] for n in summary["indicator"]], colLabels=[h for _, h in cols],
                  loc="center", cellLoc="center", bbox=[0.27, 0.12, 0.73, 0.78])
    tab.auto_set_font_size(False)
    tab.set_fontsize(12)
    for (r, c), cell in tab.get_celld().items():
        cell.set_edgecolor("#dddddd")
        if r == 0:
            cell.set_height(cell.get_height() * 1.5)
    t.set_title("Yardsticks (1 = best), on unsmoothed\nor trailing-mean values", loc="left", fontsize=13)
    fig.suptitle("Five health indicators on cutters their model never saw", x=0.01, ha="left", fontsize=15)
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, facecolor="white")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recompute", action="store_true", help="redo the PCA pass even if data/processed/hi_pca.parquet exists")
    args = ap.parse_args()

    cache = PROC / "hi_pca.parquet"
    if args.recompute or not cache.exists():
        pca_scores().to_parquet(cache)
    cycles, _ = th.load("physics")
    cycles = cycles.reset_index(drop=True).merge(pd.read_parquet(cache), on="file", how="left")
    cycles["mahalanobis"] = mahalanobis(cycles)
    cycles["cnn_autoencoder"], ae_version = autoencoder_health(cycles)
    cycles["table_current"] = cycles["lr_table_cut_a"]
    print(f"autoencoder scores used: {ae_version}")

    d = on_one_footing(cycles)
    summary, per_cutter = score(d)
    out = ROOT / "results" / "models"
    out.mkdir(parents=True, exist_ok=True)
    summary.assign(autoencoder_version=ae_version).round(3).to_csv(out / "health_indicators.csv", index=False)
    per_cutter.round(3).to_csv(out / "health_indicators_per_cutter.csv", index=False)
    figure(d, summary, ROOT / "results" / "figures" / "health_indicators.png")
    print(summary.round(3).to_string(index=False))
    print(per_cutter.pivot(index="tool", columns="indicator", values="spearman").round(2).to_string())


if __name__ == "__main__":
    main()
