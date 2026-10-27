"""Cut fixed 4,096-sample vibration windows out of every Rzeszów cycle, for the deep encoder.

Takes up to 48 windows per cycle, spread evenly over the cutting part, all 8 accelerometers.
Writes data/processed/windows_rzeszow.npy (float16, [n, 8, 4096], m/s²) and windows_rzeszow_index.parquet.
"""

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.features import load_cycle
from toollife.models.autoencoder import WIN
from toollife.rzeszow import ROOT, load_table

PER_CYCLE = 48
OUT = ROOT / "data" / "processed"


def windows_of(file: str) -> np.ndarray:
    d = load_cycle(file)
    idx = np.flatnonzero(d["cutting_vib"])
    if len(idx) < WIN:
        return np.zeros((0, 8, WIN), np.float16)
    # Contiguous cutting stretch only: start positions where the whole window is cutting.
    ok = np.flatnonzero(np.convolve(d["cutting_vib"].astype(int), np.ones(WIN, int), "valid") == WIN)
    starts = ok[np.linspace(0, len(ok) - 1, min(PER_CYCLE, len(ok))).astype(int)]
    sig = np.stack(list(d["vib"].values()), 0)  # [8, n]
    return np.stack([sig[:, s : s + WIN] for s in starts]).astype(np.float16)


def main() -> None:
    df = load_table()
    files = df["file"].tolist()
    chunks, index = [], []
    with ProcessPoolExecutor(8) as pool:
        for (file, tool, age), w in zip(df[["file", "tool", "age"]].itertuples(index=False, name=None), pool.map(windows_of, files, chunksize=4)):
            chunks.append(w)
            index += [(file, tool, age, i) for i in range(len(w))]
    arr = np.concatenate(chunks)
    np.save(OUT / "windows_rzeszow.npy", arr)
    pd.DataFrame(index, columns=["file", "tool", "age", "w"]).to_parquet(OUT / "windows_rzeszow_index.parquet")
    print(arr.shape, f"{arr.nbytes / 1e9:.1f} GB")


if __name__ == "__main__":
    main()
