"""Read single cycle CSVs out of raw_data.zip without unzipping the archive.

Works on a complete archive (via zipfile) and on a partially downloaded one
(by walking the local file headers from the start).
"""

import io
import os
import struct
import zipfile
import zlib
from functools import lru_cache

import numpy as np
import pandas as pd

from toollife.rzeszow import RAW

ZIP = RAW / "raw_data.zip"

# Unit conversions from the dataset paper (Piecuch & Żabiński 2025).
AMPS_PER_COUNT = 0.00002
G = 9.81
ACC_SENSITIVITY_V_PER_G = 0.1  # all accelerometers are close to 100 mV/g
MS2_PER_COUNT = 5 / (2**15 * ACC_SENSITIVITY_V_PER_G) * G

SPINDLE_HZ = 3200 / 60
TEETH = 4
TOOTH_HZ = SPINDLE_HZ * TEETH


@lru_cache(maxsize=1)
def _local_index() -> dict[str, tuple[int, int, int]]:
    """name -> (data offset, compressed size, method) for every complete member."""
    size = os.path.getsize(ZIP)
    idx, pos = {}, 0
    with open(ZIP, "rb") as f:
        while pos + 30 < size:
            f.seek(pos)
            h = f.read(30)
            if h[:4] != b"PK\x03\x04":
                break
            method = struct.unpack("<H", h[8:10])[0]
            csz = struct.unpack("<I", h[18:22])[0]
            nl, el = struct.unpack("<HH", h[26:30])
            name = f.read(nl).decode()
            data_at = pos + 30 + nl + el
            if data_at + csz > size:
                break
            idx[os.path.basename(name).removesuffix(".csv")] = (data_at, csz, method)
            pos = data_at + csz
    return idx


def read_cycle(file: str) -> pd.DataFrame:
    """Raw rows of one cycle file, e.g. read_cycle('P012_F01_C3')."""
    try:
        with zipfile.ZipFile(ZIP) as z, z.open(f"raw_data/{file}.csv") as fh:
            return pd.read_csv(io.BytesIO(fh.read()), engine="pyarrow")
    except zipfile.BadZipFile:
        at, csz, method = _local_index()[file]
        with open(ZIP, "rb") as f:
            f.seek(at)
            blob = f.read(csz)
        data = zlib.decompress(blob, -15) if method == 8 else blob
        return pd.read_csv(io.BytesIO(data), engine="pyarrow")


def tidy(df: pd.DataFrame) -> dict:
    """Physical units plus a 'cutting' mask on both timelines.

    The CSV packs two series side by side: vibration on every row (25 kHz) and current only on
    the first rows (500 Hz, its own 'Timestamps - Current'). Both timestamps are in ms on one clock.
    """
    t_vib = df["Timestamps - Acc"].to_numpy() / 1000.0
    cur = df[df["Timestamps - Current"].notna()]
    t_cur = cur["Timestamps - Current"].to_numpy() / 1000.0
    phase = lambda name: cur[[f"Current - {name} L{i}" for i in (1, 2, 3)]].mean(axis=1).to_numpy()
    spindle = phase("Spindle") * AMPS_PER_COUNT
    x_axis = phase("Driving axle X") * AMPS_PER_COUNT
    y_axis = phase("Driving axle Y") * AMPS_PER_COUNT
    on = spindle > 2.0
    idle = np.percentile(spindle[on], 20) if on.any() else np.nan
    # Ignore the spin-up surge (first 4 s after the spindle starts) and the spin-down surge
    # (from the last moment at idle before the spindle stops); both look like load but are not.
    window = np.zeros_like(on)
    if on.any():
        t_on = t_cur[np.flatnonzero(on)[0]]
        off = np.flatnonzero(on)[-1]
        at_idle = np.flatnonzero(np.abs(spindle[: off + 1] - idle) < 0.1)
        t_stop = t_cur[at_idle[-1]] if len(at_idle) else t_cur[off]
        window = (t_cur > t_on + 4.0) & (t_cur < t_stop)
    cutting_cur = window & (spindle > idle + 0.3)
    # Carry the cutting mask onto the vibration clock (nearest earlier current sample).
    j = np.clip(np.searchsorted(t_cur, t_vib, side="right") - 1, 0, len(t_cur) - 1)
    cutting_vib = cutting_cur[j]
    vib = {c.replace("Accelerometer - ", ""): df[c].to_numpy() * MS2_PER_COUNT
           for c in df.columns if c.startswith("Accelerometer")}
    return dict(t_vib=t_vib, t_cur=t_cur, spindle=spindle, x_axis=x_axis, y_axis=y_axis,
                idle=idle, cutting_cur=cutting_cur, cutting_vib=cutting_vib, vib=vib)
