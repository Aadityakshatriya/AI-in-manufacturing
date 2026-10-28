"""Does pretraining the TCN on other machines' cutter lives help it on ours?

The design was fixed before any result was seen (one variant, reported whatever it shows):

Inputs. The main TCN's physics input set (scripts/13_train_history.py, "physics") plus the three signals
every dataset shares, computed exactly as in scripts/15_cross_dataset.py: x_spindle (log of spindle load
relative to the same cutter when new, clipped 0.2–5), x_vib (log of mean table-vibration level relative
to new, clipped 0.2–20, 0 when the dataset has no vibration) and has_vib. The Rzeszów-only columns are
standardised on the training cutters as usual; the three shared columns are left as they are (they are
already log ratios), so they mean the same thing in every dataset.

Pretraining. On the 73 lives of the other four datasets only (NASA 15, LUH 9, MSTW 25, VMC 650 24), never
on a Rzeszów cutter. Their Rzeszów-only columns are 0 (the training average after standardisation). Only
the "life used" gauge head is trained (Huber loss on the fraction of life, delta 0.1), each dataset
weighted equally and each cutter equally inside it, 600 passes. The risk-curve head is not trained,
because a "cycle" is a different amount of cutting in each dataset. One pretrained model per seed, so
the same 5 models serve all 13 tests and no test cutter can leak in.

Fine-tuning. For each hidden Rzeszów cutter, start from each seed's pretrained weights and train with the
standard loss (risk curve + 0.5 × gauge) on the other 12, with the same recipe as the main TCN (400 passes,
AdamW, lr 3e-3, weight decay 1e-2, no early stopping). 5-seed ensemble.

Control. The same inputs trained from scratch, so the effect of pretraining is not confused with the
three added columns.

Caveats: in the other datasets a life ends at a wear limit (NASA, LUH, MSTW) or the operator's call
(VMC 650), not at breakage, so "fraction of life used" means only roughly the same thing.

Writes results/predictions/zoo_tcn_pretrained.parquet and zoo_tcn_shared_inputs.parquet (picked up by
scripts/18_fair_comparison.py through results/models/zoo_registry_transfer.csv) and
results/models/transfer_pretrain.csv (both variants, paired bootstrap over the 13 cutters).
"""

import importlib.util
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from toollife.models.hazard import curves
from toollife.models.history import HistoryModel, loss_fn, make_sequences, predict

SEEDS = 5
PRETRAIN_PASSES = 600
SHARED = ["x_spindle", "x_vib", "has_vib"]
TABLE_ACC = ["X_Driving_axle_pZ", "X_Driving_axle_mX", "Y_Driving_axle_pZ", "Y_Driving_axle_pY", "Y_Driving_axle_mX"]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load_rzeszow():
    """The main TCN's physics table, plus the three shared columns computed as in scripts/15."""
    th = module("th", "13_train_history.py")
    df, cols = th.load("physics")
    df["x_spindle"] = np.log(df["spindle_net_a__rel"].clip(0.2, 5))
    vib = df[[f"{a}__rms__rel" for a in TABLE_ACC]].mean(axis=1)
    df["x_vib"] = np.log(vib.clip(0.2, 20)).fillna(0.0)
    df["has_vib"] = vib.notna().astype(float)
    return df, cols


def load_others():
    """The 73 other lives, with the shared columns and LUH thinning of scripts/15."""
    cd = module("cd", "15_cross_dataset.py")
    df = cd.load_all()
    return df[df["dataset"] != "rzeszow"].reset_index(drop=True)


def standardiser(train_df, cols):
    """Mean and spread of the Rzeszów-only columns on the training cutters (same rule as make_sequences:
    a column that never varies is scaled to zero); the shared columns pass through unchanged."""
    rz = [c for c in cols if c not in SHARED]
    x = train_df[train_df["rul"] >= 1][rz].to_numpy(np.float32)
    mean, std = np.nanmean(x, 0), np.nanstd(x, 0)
    std = np.where(std > 1e-6, std, np.inf)
    mean_all = np.array([mean[rz.index(c)] if c in rz else 0.0 for c in cols], np.float32)
    std_all = np.array([std[rz.index(c)] if c in rz else 1.0 for c in cols], np.float32)
    return mean_all, std_all


def pretrain(args):
    """Gauge head only, on the other datasets' lives; returns the model's weights."""
    seed, others, cols = args
    torch.set_num_threads(2)
    torch.manual_seed(seed)
    tools = list(others["tool"].unique())
    T = others.groupby("tool").size().max()
    x = np.zeros((len(tools), T, len(cols)), np.float32)
    y = np.zeros((len(tools), T), np.float32)
    m = np.zeros((len(tools), T), np.float32)
    idx = [cols.index(c) for c in SHARED]
    for i, t in enumerate(tools):
        g = others[others["tool"] == t].sort_values("order")
        x[i, : len(g)][:, idx] = g[SHARED].to_numpy(np.float32)
        y[i, : len(g)] = g["life_frac"].to_numpy(np.float32)
        m[i, : len(g)] = 1
    ds = others.groupby("tool")["dataset"].first().reindex(tools)
    w = torch.as_tensor((1.0 / ds.map(ds.value_counts())).to_numpy(np.float32))
    x, y, m = torch.as_tensor(x), torch.as_tensor(y), torch.as_tensor(m)
    model = HistoryModel(len(cols))
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-2)
    model.train()
    for _ in range(PRETRAIN_PASSES):
        opt.zero_grad()
        _, gauge = model(x)
        per_tool = (nn.functional.huber_loss(gauge, y, reduction="none", delta=0.1) * m).sum(1) / m.sum(1)
        loss = (per_tool * w).sum() / w.sum()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    print(f"pretrained seed {seed}: final loss {loss.item():.4f}", flush=True)
    return {k: v.detach().clone() for k, v in model.state_dict().items()}


def fine_tune(seq, n_features, seed, init=None, passes=400):
    """The main TCN's recipe (toollife.models.history.train with no validation), optionally starting
    from pretrained weights."""
    torch.manual_seed(seed)
    model = HistoryModel(n_features)
    if init is not None:
        model.load_state_dict(init)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-2)
    for _ in range(passes):
        model.train()
        opt.zero_grad()
        loss = loss_fn(model, seq)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    model.eval()
    return model


def one_fold(args):
    held, df, cols, pre = args
    torch.set_num_threads(2)
    tr, te = df[df["tool"] != held], df[df["tool"] == held]
    mean, std = standardiser(tr, cols)
    seq_tr, _, _ = make_sequences(tr, cols, mean=mean, std=std)
    seq_te, _, _ = make_sequences(te, cols, mean=mean, std=std)
    rows = te[te["rul"] >= 1].sort_values(["tool", "age"])[["tool", "age", "rul", "life"]]
    out = {}
    for name, inits in (("tcn_pretrained", pre), ("tcn_shared_inputs", [None] * SEEDS)):
        models = [fine_tune(seq_tr, len(cols), s, inits[s]) for s in range(SEEDS)]
        logits, gauge = predict(models, seq_te)
        out[name] = rows.assign(pred=curves(logits)["rul_q50"], gauge=gauge)
    print(f"cutter {held:>3} done", flush=True)
    return out


def pretrain_check(pre, df, cols):
    """How well the pretrained gauge alone (never trained on any Rzeszów cutter) tracks life used on ours,
    from the shared signals only: the analogue of "trained on other machines only" in scripts/15."""
    seq, _, _ = make_sequences(df, cols, mean=np.zeros(len(cols), np.float32), std=np.ones(len(cols), np.float32))
    keep = [cols.index(c) for c in SHARED]
    x = torch.zeros_like(seq.x)
    x[..., keep] = seq.x[..., keep]
    gauges = []
    with torch.no_grad():
        for st in pre:
            model = HistoryModel(len(cols))
            model.load_state_dict(st)
            model.eval()
            gauges.append(model(x)[1])
    g = torch.stack(gauges).mean(0)
    mask = seq.mask.bool()
    err = (g - seq.life_frac).abs()
    per_tool = [(err[i][mask[i]]).mean().item() for i in range(len(seq.tools))]
    return float(np.mean(per_tool))


def main():
    fc = module("fc", "18_fair_comparison.py")
    df, cols = load_rzeszow()
    cols = cols + SHARED
    others = load_others()
    print(f"pretraining on {others['tool'].nunique()} lives:", others.groupby("dataset")["tool"].nunique().to_dict(), flush=True)

    with ProcessPoolExecutor(SEEDS) as ex:
        pre = list(ex.map(pretrain, [(s, others, cols) for s in range(SEEDS)]))
    check = pretrain_check(pre, df, cols)
    print(f"pretrained gauge alone on our 13 cutters: life-fraction error {check:.3f} (always guessing 0.5: 0.25)", flush=True)

    tools = sorted(df["tool"].unique())
    with ProcessPoolExecutor(5) as ex:
        folds = list(ex.map(one_fold, [(t, df, cols, pre) for t in tools]))

    pcs = {}
    for name in ("tcn_pretrained", "tcn_shared_inputs"):
        p = pd.concat([f[name] for f in folds])
        p.to_parquet(ROOT / "results" / "predictions" / f"zoo_{name}.parquet")
        pcs[name] = fc.per_cutter(p)
    base = pd.read_parquet(ROOT / "results" / "predictions" / "history_physics.parquet").rename(
        columns={"run_idx": "age", "rul_q50": "pred"})
    pcs["tcn_physics"] = fc.per_cutter(base[["tool", "age", "rul", "life", "pred"]])

    pd.DataFrame([
        dict(name="tcn_pretrained", label="TCN pretrained on 73 other machines' lives, then fine-tuned",
             family="convolution + hazard curve, transfer", inputs="physics features + settings + age + 3 shared signals (32)",
             uses_history="yes", what_it_assumes="how a cutter's load and vibration evolve towards the end of its life carries over between machines"),
        dict(name="tcn_shared_inputs", label="TCN + 3 shared signals, no pretraining (control)",
             family="convolution + hazard curve", inputs="physics features + settings + age + 3 shared signals (32)",
             uses_history="yes", what_it_assumes="same as the main TCN; the control for pretraining"),
    ]).to_csv(ROOT / "results" / "models" / "zoo_registry_transfer.csv", index=False)

    rng = np.random.default_rng(0)
    rows = []
    for a, b in (("tcn_pretrained", "tcn_shared_inputs"), ("tcn_pretrained", "tcn_physics"), ("tcn_shared_inputs", "tcn_physics")):
        for metric in ("whole_life", "last20"):
            d = (pcs[a][metric] - pcs[b][metric]).dropna()
            boots = np.array([d.to_numpy()[rng.integers(0, len(d), len(d))].mean() for _ in range(5000)])
            rows.append(dict(comparison=f"{a} minus {b}", metric=metric, a=pcs[a][metric].mean(), b=pcs[b][metric].mean(),
                             mean_diff=d.mean(), ci_low=np.percentile(boots, 2.5), ci_high=np.percentile(boots, 97.5),
                             a_better_on=int((d < 0).sum()), cutters=len(d)))
    res = pd.DataFrame(rows).round(2)
    res["pretrained_gauge_alone_life_frac_error"] = round(check, 3)
    res.to_csv(ROOT / "results" / "models" / "transfer_pretrain.csv", index=False)
    print(res.to_string(index=False))
    print(pd.concat({k: v[["whole_life", "last20"]] for k, v in pcs.items()}, axis=1).round(1).to_string())


if __name__ == "__main__":
    main()
