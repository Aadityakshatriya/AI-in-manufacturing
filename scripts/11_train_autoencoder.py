"""Train the CNN autoencoder on healthy cutting, one per fold group, then score every cycle.

Leakage rule: the autoencoder used for cutter i must never have heard cutter i. The 13 cutters are
split into five groups (balanced by sideways bite and cutter type); autoencoder g is trained without
group g, and is the one used whenever a cutter of group g is being tested.
  G1 = 2,7,101   G2 = 3,8,102   G3 = 4,9,103   G4 = 5,10   G5 = 6,105
Training uses only "healthy" windows: the first 30% of each allowed cutter's life.

Usage: python scripts/11_train_autoencoder.py --group 1 [--epochs 20]   (or --group all)
Writes results/autoencoders/g<k>.pt and data/processed/ae_g<k>.parquet with, per cycle:
  fp_0 … fp_63  fingerprint (mean over the cycle's windows)
  health        mean rebuild error over the cycle's windows (higher = sounds less like healthy cutting)
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.models.autoencoder import CNNAutoencoder, n_params
from toollife.rzeszow import ROOT, load_table

PROC = ROOT / "data" / "processed"
GROUPS = {1: [2, 7, 101], 2: [3, 8, 102], 3: [4, 9, 103], 4: [5, 10], 5: [6, 105]}
TABLE_SENSORS = [3, 4, 5, 6, 7]  # X and Y driving-axle accelerometers, in the CSV column order
HEALTHY = 0.3


def device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("mps" if torch.backends.mps.is_available() else "cpu")


def batch(windows, rows, scale, dev):
    x = windows[np.sort(rows)][:, TABLE_SENSORS].astype(np.float32)
    return torch.as_tensor(x, device=dev) / scale


def run_group(g: int, epochs: int, windows, index, meta, dev) -> None:
    torch.manual_seed(g)
    rng = np.random.default_rng(g)
    held = set(GROUPS[g]) | {11}
    info = index.merge(meta[["file", "life"]], on="file")
    frac = (info["age"] + 1) / info["life"]
    train_rows = np.flatnonzero((~info["tool"].isin(held) & (frac <= HEALTHY)).to_numpy())

    # One scale per sensor (spread of the healthy training windows); no per-window normalisation,
    # because how loud the cut is matters.
    sample = rng.choice(train_rows, size=min(3000, len(train_rows)), replace=False)
    scale = torch.as_tensor(windows[np.sort(sample)][:, TABLE_SENSORS].astype(np.float32).std(axis=(0, 2)), device=dev)[None, :, None]

    model = CNNAutoencoder().to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    steps = epochs * (len(train_rows) // 64)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=1e-3, total_steps=steps)
    print(f"group {g}: {n_params(model):,} parameters, {len(train_rows)} healthy windows, {steps} steps on {dev}", flush=True)
    t0, log = time.time(), []
    for step in range(steps):
        x = batch(windows, rng.choice(train_rows, 64, replace=False), scale, dev)
        recon, _ = model(x)
        loss = (recon - x).pow(2).mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        sched.step()
        if step % 250 == 0 or step == steps - 1:
            log.append((step, loss.item()))
            print(f"  step {step} loss {loss.item():.4f} ({time.time() - t0:.0f}s)", flush=True)

    out = ROOT / "results" / "autoencoders"
    out.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(), "scale": scale.cpu(), "held": sorted(held)}, out / f"g{g}.pt")
    pd.DataFrame(log, columns=["step", "loss"]).to_csv(out / f"g{g}_loss.csv", index=False)

    # Score every cycle of every cutter.
    model.eval()
    rows_out = []
    with torch.no_grad():
        for file, rows in index.groupby("file", sort=False).groups.items():
            x = batch(windows, np.asarray(rows), scale, dev)
            recon, z = model(x)
            err = (recon - x).pow(2).mean((1, 2))
            rows_out.append([file, *z.mean(0).cpu().numpy(), err.mean().item()])
    cols = ["file"] + [f"fp_{i}" for i in range(z.shape[1])] + ["health"]
    pd.DataFrame(rows_out, columns=cols).to_parquet(PROC / f"ae_g{g}.parquet")
    print(f"group {g} done in {time.time() - t0:.0f}s", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="all")
    ap.add_argument("--epochs", type=int, default=20)
    args = ap.parse_args()
    dev = device()
    windows = np.load(PROC / "windows_rzeszow.npy", mmap_mode="r")
    index = pd.read_parquet(PROC / "windows_rzeszow_index.parquet")
    meta = load_table()
    groups = list(GROUPS) if args.group == "all" else [int(args.group)]
    for g in groups:
        run_group(g, args.epochs, windows, index, meta, dev)


if __name__ == "__main__":
    main()
