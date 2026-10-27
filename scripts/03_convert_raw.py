"""Convert the Rzeszów raw archive (968 CSVs, ~112 GB) into compact per-cycle arrays.

Reads one CSV at a time straight out of raw_data.zip, so the archive is never unzipped.
Output: data/rzeszow_cycles/<file>.npz with
  vib      int16  [n, 8]   accelerometers at 25 kHz (raw ADC counts, lossless)
  cur      int32  [m, 12]  currents at 500 Hz (the CSV packs them beside the vibration rows;
                           they fill only the first m rows and carry their own timestamps)
  vib_t0_ms, cur_t_ms      timestamps; vibration is gap-free at 0.04 ms per row
  vib_names, cur_names     channel names

Usage: python scripts/03_convert_raw.py [--workers 8]
"""

import argparse
import io
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "data" / "raw" / "raw_data.zip"
OUT = ROOT / "data" / "rzeszow_cycles"


def convert(member: str) -> tuple[str, int, int]:
    name = Path(member).stem
    dest = OUT / f"{name}.npz"
    if dest.exists():
        return name, -1, -1
    with zipfile.ZipFile(ZIP) as z, z.open(member) as fh:
        df = pd.read_csv(io.BytesIO(fh.read()), engine="pyarrow")
    vib_cols = [c for c in df.columns if c.startswith("Accelerometer")]
    cur_cols = [c for c in df.columns if c.startswith("Current")]
    vib = df[vib_cols].to_numpy()
    if np.abs(vib).max() > 32767 or not np.allclose(vib, np.round(vib)):
        raise ValueError(f"{name}: vibration does not fit int16 losslessly")
    cur_df = df[df["Timestamps - Current"].notna()]
    cur = cur_df[cur_cols].to_numpy()
    tmp = dest.with_suffix(".tmp.npz")
    np.savez_compressed(
        tmp,
        vib=vib.astype(np.int16),
        cur=cur.astype(np.int32),
        vib_t0_ms=df["Timestamps - Acc"].iloc[0],
        cur_t_ms=cur_df["Timestamps - Current"].to_numpy(np.float32),
        vib_names=np.array(vib_cols),
        cur_names=np.array(cur_cols),
    )
    tmp.rename(dest)
    return name, len(vib), len(cur)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP) as z:
        members = [m for m in z.namelist() if m.endswith(".csv")]
    print(f"{len(members)} cycle files")
    done = 0
    with ProcessPoolExecutor(args.workers) as pool:
        futs = [pool.submit(convert, m) for m in members]
        for f in as_completed(futs):
            name, nv, nc = f.result()
            done += 1
            if done % 25 == 0 or done == len(members):
                print(f"{done}/{len(members)}  last={name} vib_rows={nv} cur_rows={nc}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
