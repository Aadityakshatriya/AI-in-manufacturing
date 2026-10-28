"""End-to-end deep learning on the raw signal, against the same question answered from hand-made features.

The question a reviewer will ask: "why hand-made features; why not train a deep network end-to-end on
the raw signal?" This script trains one (src/toollife/models/raw_cnn.py). It reads 0.16 s of raw
vibration from the five table-side sensors (5 x 4,096 readings, one scale per sensor, as in scripts/11)
and outputs the fraction of the cutter's life already used (0 = new, 1 = about to break). It sees
nothing else: not the settings, not the cycle count, not how this cutter sounded when new. A cycle's
prediction is the mean over its 48 windows.

Fair comparators, same folds and same target: LightGBM and a small MLP given the per-cycle physics
inputs the TCN uses (th.load("physics"): settings, log age, 18 signals relative to the cutter's own
first cycles, 4 absolute ones). Two reference rows show where the information sits: LightGBM on
settings + age only, and LightGBM on the physics inputs without age.

Folds: the five groups of scripts/11 (G1 = 2,7,101  G2 = 3,8,102  G3 = 4,9,103  G4 = 5,10  G5 = 6,105),
so every model here trains on 10-11 cutters, not the 12 of leave-one-cutter-out used elsewhere.
Scores count each cutter equally, on every cycle the cutter survived (cycles left >= 1).
Life fraction f becomes cycles left as rul_hat = (age + 1)(1 - f) / f, clipped to [0, 300].

On macOS, PyTorch and LightGBM each bring their own OpenMP library and crash when both do work in one
process, so the CNN runs in a child process (--part cnn) and LightGBM in this one; neither is imported
at the top of this file.

Usage: python scripts/23_raw_cnn.py [--minutes 15] [--reuse-cnn]
Writes results/predictions/zoo_raw_cnn.parquet (tool, age, rul, life, pred),
results/models/zoo_registry_signal.csv, raw_cnn_comparison.csv and raw_cnn_per_cutter.csv;
the CNN's per-cycle life fractions are kept in data/processed/raw_cnn_cycles.parquet.
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "2")  # shared machine: stay within two cores

import argparse
import importlib.util
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from toollife.rzeszow import load_table

PROC = ROOT / "data" / "processed"
CNN_CYCLES = PROC / "raw_cnn_cycles.parquet"
GROUPS = {1: [2, 7, 101], 2: [3, 8, 102], 3: [4, 9, 103], 4: [5, 10], 5: [6, 105]}  # as in scripts/11 and 13
TABLE_SENSORS = [3, 4, 5, 6, 7]
EVERY = 4        # training keeps every 4th window of each cycle (12 of 48), so it fits in memory
CROP = 3584      # random 0.14 s crop of each training window, so the net cannot memorise positions
BATCH = 64
CLIP_RUL = 300


def _script(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------- the raw-signal CNN (child process: PyTorch only) ----------

def window_table() -> pd.DataFrame:
    index = pd.read_parquet(PROC / "windows_rzeszow_index.parquet").reset_index(drop=True).reset_index(names="row")
    meta = load_table()[["file", "life", "rul"]]
    index = index[index["tool"] != 11].merge(meta, on="file", how="left")
    index["frac"] = (index["age"] + 1) / index["life"]
    return index


def preload(windows, rows: np.ndarray) -> np.ndarray:
    """Read the chosen windows' five table sensors, in chunks so the 2.8 GB file is never loaded whole."""
    out = np.empty((len(rows), len(TABLE_SENSORS), windows.shape[2]), np.float16)
    for a in range(0, len(rows), 1024):
        out[a:a + 1024] = windows[rows[a:a + 1024]][:, TABLE_SENSORS]
    return out


def train_cnn(data, frac, train_idx, steps, seed, dev):
    import torch

    from toollife.models.raw_cnn import RawCNN

    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    sample = data[torch.as_tensor(rng.choice(train_idx, min(2000, len(train_idx)), replace=False), device=dev)].float()
    scale = sample.std(dim=(0, 2))[None, :, None]  # one scale per sensor, no per-window normalisation
    target = torch.as_tensor(frac, dtype=torch.float32, device=dev)
    model = RawCNN().to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=1e-3, total_steps=steps)
    model.train()
    for step in range(steps):
        idx = torch.as_tensor(rng.choice(train_idx, BATCH), device=dev)
        start = int(rng.integers(0, data.shape[2] - CROP + 1))
        x = data[idx, :, start:start + CROP].float() / scale
        # Huber with a small threshold: behaves like absolute error for big misses, which is what we score.
        loss = torch.nn.functional.huber_loss(model(x), target[idx], delta=0.1)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % 500 == 0 or step == steps - 1:
            print(f"    step {step} loss {loss.item():.4f}", flush=True)
    return model.eval(), scale


def predict_cycles(model, scale, windows, wt: pd.DataFrame, dev) -> pd.DataFrame:
    """Every window of every cycle of the test cutters; a cycle's prediction is the mean over its windows."""
    import torch

    out = []
    with torch.no_grad():
        for file, g in wt.groupby("file", sort=False):
            x = torch.as_tensor(windows[np.sort(g["row"].to_numpy())][:, TABLE_SENSORS].astype(np.float32), device=dev) / scale
            out.append((file, model(x).mean().item()))
    return pd.DataFrame(out, columns=["file", "f_hat"])


def run_cnn(minutes: float) -> None:
    import torch

    from toollife.models.autoencoder import n_params

    torch.set_num_threads(2)
    dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    windows = np.load(PROC / "windows_rzeszow.npy", mmap_mode="r")
    wt = window_table()
    keep = wt[wt["w"] % EVERY == 0].sort_values("row")
    t0 = time.time()
    data = torch.from_numpy(preload(windows, keep["row"].to_numpy())).to(dev)
    print(f"preloaded {len(keep)} training windows ({data.element_size() * data.nelement() / 1e6:.0f} MB) in {time.time() - t0:.0f}s", flush=True)
    frac, tools = keep["frac"].to_numpy(), keep["tool"].to_numpy()

    # Fit the step count to the time budget: 70% of each fold's share trains, the rest loads and scores.
    # A short warm-up first: the GPU's first steps include one-off set-up and would inflate the timing.
    probe = np.flatnonzero(~np.isin(tools, GROUPS[1]))
    train_cnn(data, frac, probe, 5, 0, dev)
    if dev.type == "mps":
        torch.mps.synchronize()
    t1 = time.time()
    train_cnn(data, frac, probe, 40, 0, dev)
    if dev.type == "mps":
        torch.mps.synchronize()
    sec_per_step = (time.time() - t1) / 40
    steps = int(0.7 * minutes * 60 / len(GROUPS) / sec_per_step)
    print(f"{sec_per_step * 1000:.0f} ms per step on {dev} -> {steps} steps per fold", flush=True)

    preds, train_seconds = [], 0.0
    for g, held in GROUPS.items():
        t1 = time.time()
        model, scale = train_cnn(data, frac, np.flatnonzero(~np.isin(tools, held)), steps, g, dev)
        train_seconds += time.time() - t1
        preds.append(predict_cycles(model, scale, windows, wt[wt["tool"].isin(held)], dev))
        print(f"  fold {g} (held out {held}): {time.time() - t1:.0f}s incl. scoring", flush=True)
    cycles = wt.drop_duplicates("file")[["file", "tool", "age", "life", "rul", "frac"]]
    out = cycles.merge(pd.concat(preds), on="file")
    out["train_seconds"], out["n_weights"], out["steps_per_fold"] = train_seconds, n_params(model), steps
    out.to_parquet(CNN_CYCLES)
    print(f"wrote {CNN_CYCLES}", flush=True)


# ---------- the feature models and scoring (this process: LightGBM, never PyTorch compute) ----------

def feature_models(fair, th) -> dict[str, tuple[pd.DataFrame, float, str]]:
    """LightGBM and MLP on per-cycle inputs, same five group folds, same target."""
    import lightgbm as lgb
    from sklearn.impute import SimpleImputer
    from sklearn.neural_network import MLPRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    df, cols = th.load("physics")
    _, base = th.load("settings_age")
    no_age = [c for c in cols if c != "log_age"]
    lgbm = lambda: lgb.LGBMRegressor(**fair.PARAMS, n_jobs=2)
    mlp = lambda: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                MLPRegressor(hidden_layer_sizes=(64, 32), alpha=1e-2, max_iter=2000, random_state=0))
    specs = {"lgbm_physics": (lgbm, cols), "mlp_physics": (mlp, cols),
             "ref_lgbm_settings_age": (lgbm, base), "ref_lgbm_physics_no_age": (lgbm, no_age)}
    out = {}
    for name, (make, use) in specs.items():
        parts, secs = [], 0.0
        for g, held in GROUPS.items():
            tr, te = df[~df["tool"].isin(held)], df[df["tool"].isin(held)]
            # Drop inputs that never vary among the training cutters: e.g. without group 4, every training
            # cutter has the same holder, and standardising a constant divides by zero.
            fold_use = [c for c in use if tr[c].nunique(dropna=True) > 1]
            t0 = time.time()
            m = make().fit(tr[fold_use], tr["life_frac"])
            secs += time.time() - t0
            parts.append(te[["file", "tool", "age", "life", "rul"]].assign(frac=te["life_frac"], f_hat=m.predict(te[fold_use])))
        size = "400 trees x 15 leaves" if "lgbm" in name else f"{sum(w.size for w in m[-1].coefs_ + m[-1].intercepts_):,} weights"
        out[name] = (pd.concat(parts), secs, size)
    return out


def score(p: pd.DataFrame, per_cutter) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Per-cutter life-fraction error and rank correlation, plus cycles-left errors via 18's per_cutter()."""
    p = p[p["rul"] >= 1].copy()
    p["f_hat"] = p["f_hat"].clip(1e-3, 1.0)
    p["pred"] = ((p["age"] + 1) * (1 - p["f_hat"]) / p["f_hat"]).clip(0, CLIP_RUL)
    rows = [dict(tool=t, frac_mae=(g["f_hat"] - g["frac"]).abs().mean(), spearman=spearmanr(g["frac"], g["f_hat"])[0])
            for t, g in p.groupby("tool")]
    pc = pd.DataFrame(rows).set_index("tool").join(per_cutter(p[["tool", "age", "rul", "life", "pred"]]))
    summary = dict(frac_mae=pc["frac_mae"].mean(), spearman=pc["spearman"].mean(),
                   cutters_spearman_over_05=int((pc["spearman"] > 0.5).sum()),
                   rul_mae_whole_life=pc["whole_life"].mean(), rul_mae_last20=pc["last20"].mean(),
                   rul_over_last20=pc["over_last20"].mean())
    return pc, summary, p


REGISTRY = {
    "raw_cnn": dict(
        label="1-D CNN on raw table vibration", family="deep learning, end-to-end",
        inputs="raw 5 x 4,096 table-sensor window (0.16 s); nothing else", uses_history="no",
        what_it_assumes="How worn a cutter is can be heard in a single 0.16-second burst of table vibration, the same way on every cutter, without knowing its settings, its age or how it sounded when new."),
    "lgbm_physics": dict(
        label="LightGBM on physics inputs", family="gradient-boosted trees",
        inputs="th.load('physics'): settings, log age, 18 signals relative to new, 4 absolute",
        uses_history="first cycles only (signals are relative to the cutter's own start)",
        what_it_assumes="Wear shows as how much current and vibration have changed since the cutter was new; with the settings and age, learned thresholds map those changes to life used."),
    "mlp_physics": dict(
        label="Small MLP on physics inputs", family="neural network on features",
        inputs="th.load('physics'): settings, log age, 18 signals relative to new, 4 absolute",
        uses_history="first cycles only (signals are relative to the cutter's own start)",
        what_it_assumes="Wear shows as how much current and vibration have changed since the cutter was new, and life used is a smooth function of those changes, the settings and age."),
}
NOTE = "5-group folds (trained on 10-11 cutters per fold), not leave-one-cutter-out; target = fraction of life used"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=15, help="total GPU time for the five CNN folds")
    ap.add_argument("--reuse-cnn", action="store_true", help=f"score the CNN predictions already in {CNN_CYCLES.name}")
    ap.add_argument("--part", choices=["cnn"], help=argparse.SUPPRESS)  # internal: the child process
    args = ap.parse_args()
    if args.part == "cnn":
        run_cnn(args.minutes)
        return
    if not (args.reuse_cnn and CNN_CYCLES.exists()):
        subprocess.run([sys.executable, "-u", __file__, "--part", "cnn", "--minutes", str(args.minutes)], check=True)

    import lightgbm  # noqa: F401  (before 18_fair_comparison pulls in PyTorch; see the module note)

    fair = _script("fair", "18_fair_comparison.py")
    cnn = pd.read_parquet(CNN_CYCLES)
    results = {"raw_cnn": (cnn, float(cnn["train_seconds"].iloc[0]), f"{int(cnn['n_weights'].iloc[0]):,} weights")}
    results |= feature_models(fair, fair.th)

    summaries, per_cutter = [], []
    for name, (pred, secs, size) in results.items():
        pc, s, scored = score(pred, fair.per_cutter)
        if name == "raw_cnn":
            out = ROOT / "results" / "predictions" / "zoo_raw_cnn.parquet"
            scored[["tool", "age", "rul", "life", "pred"]].reset_index(drop=True).to_parquet(out)
            print(f"wrote {out}")
        summaries.append(dict(name=name, **s, size=size, train_seconds=round(secs, 1)))
        per_cutter.append(pc.reset_index().assign(name=name))

    summary = pd.DataFrame(summaries)
    out = ROOT / "results" / "models"
    summary.round(3).to_csv(out / "raw_cnn_comparison.csv", index=False)
    pd.concat(per_cutter).round(3).to_csv(out / "raw_cnn_per_cutter.csv", index=False)
    reg = summary[summary["name"].isin(REGISTRY)].copy()
    for col in ("label", "family", "inputs", "uses_history", "what_it_assumes"):
        reg[col] = reg["name"].map(lambda n: REGISTRY[n][col])
    reg["note"] = NOTE
    first = ["name", "label", "family", "inputs", "uses_history", "what_it_assumes"]
    reg[first + [c for c in reg.columns if c not in first]].round(3).to_csv(out / "zoo_registry_signal.csv", index=False)
    print(summary.round(3).to_string(index=False))
    print(pd.concat(per_cutter).pivot(index="tool", columns="name", values="spearman").round(2).to_string())


if __name__ == "__main__":
    main()
