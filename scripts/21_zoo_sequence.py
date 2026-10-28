"""Sequence zoo on Rzeszów: which part of the TCN earns its score — the history, the hazard head, or the sensors?

Every model gets exactly the TCN's recipe from scripts/13_train_history.py: the physics inputs of
load("physics"), outer leave-one-cutter-out over the 13 cutters, 5 seeds averaged in probability space,
400 full-batch passes, AdamW (lr 3e-3, weight decay 1e-2), gradient clip 1, dropout 0.2. Only the network
shape (src/toollife/models/sequence_zoo.py) or, for the ablations, the input columns change; the one
exception is linear_hazard, fitted to convergence (sequence_zoo.RECIPE says why). Unlike
script 13 there is no inner calibration loop: the point prediction is the median of the failure curve
(rul_q50), and the raw q10/q90 are saved as they come.

Models (--arch, comma-separated, or "all"):
  tcn                   stock TCN from history.py, the reference; also writes the single-seed spread
  linear_hazard, mlp_now, gru, lstm, transformer, tcn_direct    see sequence_zoo.py
  tcn_summaries         stock TCN on the 120 released per-cycle summaries + settings + age (LightGBM's inputs)
  tcn_currents_only     stock TCN on settings + age + motor-current features + first_ring
  tcn_vibration_only    stock TCN on settings + age + accelerometer features + first_ring
  tcn_no_age            stock TCN on settings + physics, without log_age
  tcn_age_only          stock TCN on log_age alone

Writes results/predictions/zoo_<arch>.parquet (tool, age, rul, life, pred, q10, q90) and one row per model
in results/models/zoo_registry_sequence.csv, scored with per_cutter() from scripts/18_fair_comparison.py.
Every full run also writes its rows of results/models/zoo_seed_spread.csv: each seed alone, the noise
yardstick for every gap between models. --folds 2,7 runs only those hidden cutters and prints scores without writing
anything (smoke tests). train_seconds is the single-thread time to train all 13 × 5 models, measured on
a shared, busy machine, so only its order of magnitude means anything.

Usage: python scripts/21_zoo_sequence.py --arch all [--folds 2,7] [--seeds 5] [--workers 4]
"""

import argparse
import importlib.util
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from toollife.models import history, sequence_zoo as zoo
from toollife.models.hazard import curves
from toollife.rzeszow import load_table, sensor_columns


def _script(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


th = _script("th", "13_train_history.py")  # load() and the feature lists
fair = _script("fair", "18_fair_comparison.py")  # per_cutter(), the shared scoring

CURRENTS = ["spindle_net_a", "table_cut_a", "x_cut_a", "y_cut_a", "spindle_charge_per_mm3", "table_over_spindle"]
VIBRATION = [c for c in th.PHYS_REL if c not in CURRENTS]

# name: (label, family, inputs, uses_history, what_it_assumes)
REGISTRY = {
    "tcn": ("TCN (stock, reference)", "convolution + hazard curve", "physics features + settings + age + first_ring (29)", "yes",
            "the last ~60 cycles, read through fixed sliding filters, show how close the cutter is to breaking"),
    "linear_hazard": ("Logistic hazard (linear)", "statistics: discrete-time logistic hazard", "physics features + settings + age + first_ring (29)", "no",
                      "risk is a fixed weighted sum of today's readings; the past doesn't matter"),
    "mlp_now": ("MLP on today only", "dense network", "physics features + settings + age + first_ring (29)", "no",
                "risk is any smooth function of today's readings; the past adds nothing once today is known"),
    "gru": ("GRU", "recurrent", "physics features + settings + age + first_ring (29)", "yes",
            "a 64-number running summary, updated every cycle, can carry everything about the past that matters"),
    "lstm": ("LSTM", "recurrent", "physics features + settings + age + first_ring (29)", "yes",
             "like the GRU, plus a separate memory cell that can hold early-life facts for a long time"),
    "transformer": ("Causal transformer", "attention", "physics features + settings + age + first_ring (29)", "yes",
                    "any earlier cycle may matter, and the network learns which ones to look back at"),
    "tcn_direct": ("TCN, direct regression", "convolution + regression head", "physics features + settings + age + first_ring (29)", "yes",
                   "same window as the TCN, but the answer is a single number of cycles left, not a risk curve"),
    "tcn_summaries": ("TCN on the 120 summaries", "convolution + hazard curve",
                      "120 released summaries + settings + age (126; LightGBM's inputs)", "yes",
                      "the dataset's own per-cycle summaries carry the wear signal as well as our physics features"),
    "tcn_currents_only": ("TCN, motor currents only", "convolution + hazard curve",
                          "settings + age + 6 current features + first_ring (13)", "yes",
                          "the motors' electricity alone carries the wear signal"),
    "tcn_vibration_only": ("TCN, vibration only", "convolution + hazard curve",
                           "settings + age + 16 accelerometer features + first_ring (23)", "yes",
                           "the accelerometers alone carry the wear signal"),
    "tcn_no_age": ("TCN without age", "convolution + hazard curve", "physics features + settings + first_ring, no log_age (28)", "yes",
                   "wear shows in the signals themselves, so the cycle count is not needed"),
    "tcn_age_only": ("TCN on age only", "convolution + hazard curve", "log_age only (1)", "yes",
                     "all cutters age alike, so the cycle count alone says how much life is left"),
}
STOCK = ("tcn", "tcn_summaries", "tcn_currents_only", "tcn_vibration_only", "tcn_no_age", "tcn_age_only")
ALL = ("tcn",) + zoo.ARCHS + ("tcn_currents_only", "tcn_vibration_only", "tcn_summaries", "tcn_no_age", "tcn_age_only")


def columns(arch: str, physics_cols: list[str], summaries: list[str]) -> list[str]:
    base = th.SETTINGS + ["log_age"]
    if arch == "tcn_summaries":
        return base + summaries
    if arch == "tcn_currents_only":
        return base + [f"lr_{c}" for c in CURRENTS] + ["first_ring"]
    if arch == "tcn_vibration_only":
        return base + [f"lr_{c}" for c in VIBRATION] + th.PHYS_ABS + ["first_ring"]
    if arch == "tcn_no_age":
        # first_ring stays: it marks the first ring of each new workpiece (every ~4 cycles), not life position.
        return [c for c in physics_cols if c != "log_age"]
    if arch == "tcn_age_only":
        return ["log_age"]
    return physics_cols


def run_fold(arch: str, held: int, df: pd.DataFrame, cols: list[str], seeds: int):
    """Train the 5-seed ensemble on the other 12 cutters and predict the hidden one."""
    torch.set_num_threads(1)
    train_df, test_df = df[df["tool"] != held], df[df["tool"] == held]
    seq_tr, mean, std = history.make_sequences(train_df, cols)
    seq_te, _, _ = history.make_sequences(test_df, cols, mean=mean, std=std)
    t0 = time.perf_counter()
    if arch in STOCK:
        models = [history.train(seq_tr, None, len(cols), seed=s) for s in range(seeds)]
    else:
        models = [zoo.train(seq_tr, len(cols), arch, seed=s) for s in range(seeds)]
    seconds = time.perf_counter() - t0
    rows = test_df[test_df["rul"] >= 1].sort_values(["tool", "age"])
    out = rows[["tool", "age", "rul", "life"]].copy()
    if arch == "tcn_direct":
        point = lambda ms: np.clip(zoo.predict_direct(ms, seq_te), 0, None)
        out["q10"] = out["q90"] = np.nan
    else:
        point = lambda ms: curves(history.predict(ms, seq_te)[0])["rul_q50"]
        c = curves(history.predict(models, seq_te)[0])
        out["q10"], out["q90"] = c["rul_q10"], c["rul_q90"]
    out["pred"] = point(models)
    per_seed = {s: point([m]) for s, m in enumerate(models)}  # each seed alone, for the noise yardstick
    return arch, held, out, seconds, zoo.n_params(models[0]), per_seed


def score(p: pd.DataFrame) -> tuple[float, float, pd.DataFrame]:
    pc = fair.per_cutter(p)
    return pc["whole_life"].mean(), pc["last20"].mean(), pc


def upsert(path: Path, new: pd.DataFrame, key: str, order: list[str]) -> None:
    """Replace this run's rows in a shared table, keep everyone else's."""
    old = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=new.columns)
    out = pd.concat([old[~old[key].isin(new[key])], new], ignore_index=True)
    out["_o"] = out[key].map({n: i for i, n in enumerate(order)}).fillna(len(order))
    out.sort_values("_o", kind="stable").drop(columns="_o").to_csv(path, index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", default="all", help="comma-separated names, or 'all'")
    ap.add_argument("--folds", help="comma-separated hidden cutters for a smoke test; nothing is written")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    archs = list(ALL) if args.arch == "all" else args.arch.split(",")
    unknown = [a for a in archs if a not in REGISTRY]
    assert not unknown, f"unknown arch {unknown}; choose from {list(ALL)}"

    df, physics_cols = th.load("physics")
    tab = load_table()
    summaries = sensor_columns(tab)  # the 120 released per-cycle summaries, LightGBM's inputs in script 02
    df = df.merge(tab[["file"] + summaries], on="file", how="left", validate="one_to_one")
    all_folds = sorted(df["tool"].unique())
    folds = [int(f) for f in args.folds.split(",")] if args.folds else all_folds
    tasks = [(a, h) for a in archs for h in folds]  # in the order asked, so the first archs finish first
    full = folds == all_folds
    ref = pd.read_parquet(ROOT / "results" / "predictions" / "history_physics.parquet")
    ref = ref.rename(columns={"run_idx": "age", "rul_q50": "pred"})[["tool", "age", "rul", "life", "pred"]]

    results: dict[str, list] = {a: [] for a in archs}
    with ProcessPoolExecutor(min(args.workers, len(tasks))) as pool:
        futs = [pool.submit(run_fold, a, h, df, columns(a, physics_cols, summaries), args.seeds) for a, h in tasks]
        for f in as_completed(futs):
            try:
                arch, held, out, sec, size, per_seed = f.result()
            except Exception as e:  # one broken fold should not take the other models down with it
                print(f"FAILED fold: {e!r}", flush=True)
                continue
            results[arch].append((out, sec, size, per_seed))
            print(f"{arch:>20} cutter {held:>3}: MAE {np.abs(out['pred'] - out['rul']).mean():5.1f}  ({sec:.0f} s)", flush=True)
            if len(results[arch]) == len(folds):  # write each model as soon as its last fold is in
                finish(arch, results[arch], folds, full, ref, args.seeds)


def finish(arch: str, res: list, folds: list[int], full: bool, ref: pd.DataFrame, seeds: int) -> None:
    """Score one model over its folds; on a full run, write its predictions and registry row."""
    pred = pd.concat([o for o, *_ in res]).sort_values(["tool", "age"]).reset_index(drop=True)
    whole, last20, pc = score(pred)
    seconds, size = sum(r[1] for r in res), res[0][2]
    print(f"\n{arch}: whole life {whole:.2f}, last 20% {last20:.2f}, {size:,} params, {seconds:.0f} s")
    if arch == "tcn":  # sanity check against script 13's saved predictions for the same cutters
        rw, rl, rpc = score(ref[ref["tool"].isin(folds)])
        both = pd.concat({"this run": pc[["whole_life", "last20"]], "history_physics": rpc[["whole_life", "last20"]]}, axis=1)
        print(both.round(2).to_string())
        print(f"history_physics on these cutters: whole life {rw:.2f}, last 20% {rl:.2f}")
    else:
        print(pc[["whole_life", "last20"]].round(2).T.to_string())
    print(flush=True)
    if not full:
        return
    pred[["tool", "age", "rul", "life", "pred", "q10", "q90"]].to_parquet(ROOT / "results" / "predictions" / f"zoo_{arch}.parquet")
    label, family, inputs, uses_history, assumes = REGISTRY[arch]
    row = dict(name=arch, label=label, family=family, inputs=inputs, uses_history=uses_history,
               what_it_assumes=assumes, mae_whole_life=round(whole, 2), mae_last20=round(last20, 2),
               size=size, train_seconds=round(seconds))
    upsert(ROOT / "results" / "models" / "zoo_registry_sequence.csv", pd.DataFrame([row]), "name", list(ALL))
    # Each seed alone over all 13 cutters: how far one model moves on a new random start, i.e. the noise
    # yardstick for every gap between models.
    rows = []
    for s in range(seeds):
        w, l, _ = score(pd.concat([o.assign(pred=ps[s]) for o, _, _, ps in res]))
        rows.append(dict(name=arch, model=f"seed {s} alone", mae_whole_life=round(w, 2), mae_last20=round(l, 2)))
    sp = pd.DataFrame(rows)
    rows += [dict(name=arch, model="single seeds: min", mae_whole_life=sp.mae_whole_life.min(), mae_last20=sp.mae_last20.min()),
             dict(name=arch, model="single seeds: max", mae_whole_life=sp.mae_whole_life.max(), mae_last20=sp.mae_last20.max()),
             dict(name=arch, model=f"{seeds}-seed ensemble", mae_whole_life=round(whole, 2), mae_last20=round(last20, 2))]
    upsert(ROOT / "results" / "models" / "zoo_seed_spread.csv", pd.DataFrame(rows), "name", list(ALL))
    print(pd.DataFrame(rows).drop(columns="name").to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
