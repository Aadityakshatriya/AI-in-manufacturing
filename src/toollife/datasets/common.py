"""Shared pieces for the public-dataset loaders.

Common run table (PLAN.md §6): one row per recorded run of one cutter, with
  dataset, tool, run_idx, run_native, end_type, cum_time_s, cum_volume_mm3, life_frac,
  rul_native, rul_unit, eol_reached, machine, material, rpm, feed_mm_min, ap_mm, ae_mm,
  tool_diam_mm, teeth, vb_um, vb_measured, cut_time_s, signal_ok
followed by the physics features:
  spindle_load_abs  spindle load during cutting minus idle, in the dataset's own unit (spindle_unit)
  spindle_idle      the idle level that was subtracted (same unit)
  spindle_load_rel  spindle_load_abs ÷ the same tool's causal early-life baseline
  vib_<ch>_rms      vibration RMS during cutting; vib_<ch>_o1 / _tp / _hi are band RMS at spindle
                    order 1, at the tooth-pass order and its harmonics, and in the high band
  force_res_abs     mean in-plane force √(Fx²+Fy²) during cutting (force_z_abs for the axial one)
  <signal>_mean/_std/_kurt  plain statistics of every raw signal during cutting
  <feature>_rel     every feature listed in a loader's REL_COLS, ÷ the tool's early-life median

Shared features for cross-dataset models (same meaning in every dataset, NaN where the sensor is absent):
  spindle_load_rel  spindle load ÷ the tool's early-life value
  vib_rms_rel       mean over the vibration channels of vib_<ch>_rms_rel
  force_rel         force_res_abs_rel (in-plane force ÷ early-life value)
"Early life" = a causal baseline: at each run, the median of the tool's first (up to) 3 runs seen so
far. It never looks ahead and never depends on how long the tool will live (an earlier version used
the first 10% of the tool's runs, which quietly leaked the tool's life length into the features).

life_frac runs on the cumulative-cutting-time clock: cum_time_s of the run ÷ cum_time_s of the
end-of-life run, so the end-of-life run is exactly 1. Runs recorded after end of life are dropped.
"""

import math
import os
import struct
import zipfile
import zlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal, stats
from scipy.ndimage import uniform_filter1d

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

BASE_COLS = [
    "dataset", "tool", "run_idx", "run_native", "end_type", "cum_time_s", "cum_volume_mm3",
    "life_frac", "rul_native", "rul_unit", "eol_reached", "machine", "material", "rpm",
    "feed_mm_min", "ap_mm", "ae_mm", "tool_diam_mm", "teeth", "vb_um", "vb_measured",
    "cut_time_s", "signal_ok", "spindle_source", "spindle_unit", "spindle_idle",
    "spindle_load_abs", "spindle_load_rel", "vib_rms_rel", "force_rel",
]

SHARED = ["spindle_load_rel", "vib_rms_rel", "force_rel"]



# ---------- parallel map ----------

def parallel_map(fn, jobs: list, workers: int = 8) -> list:
    """fn over jobs in a process pool (in order). workers <= 1 runs in this process."""
    if workers <= 1 or len(jobs) <= 1:
        return [fn(j) for j in jobs]
    with ProcessPoolExecutor(workers) as pool:
        return list(pool.map(fn, jobs, chunksize=max(1, len(jobs) // (workers * 8))))


# ---------- signal helpers ----------

def smooth(x: np.ndarray, n: int) -> np.ndarray:
    """Moving average over n samples (same length)."""
    x = np.asarray(x, dtype=float)
    return uniform_filter1d(x, n, mode="nearest") if n > 1 else x


def cutting_mask(load: np.ndarray, fs: float, smooth_s: float = 0.1, frac: float = 0.5):
    """Samples where the (smoothed) load is in the cutting plateau.

    idle = 5th percentile, plateau = 95th percentile of the smoothed load; cutting is where the load
    has risen more than `frac` of the way from idle to plateau. This keeps steady engagement and drops
    idle, approach, and most of the entry/exit ramps. Returns (mask, idle, plateau).
    """
    s = smooth(load, max(1, int(round(smooth_s * fs))))
    idle, top = np.percentile(s, [5, 95])
    return s > idle + frac * (top - idle), float(idle), float(top)


def window_rms(x: np.ndarray, n: int) -> np.ndarray:
    """RMS of each non-overlapping n-sample window after removing that window's mean (AC RMS)."""
    k = len(x) // n
    w = np.asarray(x[: k * n], dtype=float).reshape(k, n)
    return np.sqrt(((w - w.mean(axis=1, keepdims=True)) ** 2).mean(axis=1))


def basic_stats(prefix: str, x: np.ndarray) -> dict:
    """mean / std / excess kurtosis of a signal (already restricted to cutting)."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 4:
        return {f"{prefix}_mean": np.nan, f"{prefix}_std": np.nan, f"{prefix}_kurt": np.nan}
    return {f"{prefix}_mean": float(x.mean()), f"{prefix}_std": float(x.std()),
            f"{prefix}_kurt": float(stats.kurtosis(x))}


def runs_of(mask: np.ndarray) -> list[tuple[int, int]]:
    """(start, stop) of each contiguous True stretch."""
    m = np.concatenate([[False], np.asarray(mask, bool), [False]])
    d = np.flatnonzero(np.diff(m.astype(np.int8)))
    return list(zip(d[::2], d[1::2]))


def masked_psd(x: np.ndarray, mask: np.ndarray, fs: float, nperseg: int):
    """Welch PSD averaged over the contiguous cutting stretches (each detrended on its own).

    Stretches shorter than nperseg are skipped, so idle samples never enter a spectrum.
    Returns (f, P) or (None, None) when there is not enough cutting.
    """
    acc, total = None, 0
    for a, b in runs_of(mask):
        if b - a < nperseg:
            continue
        f, p = signal.welch(np.asarray(x[a:b], dtype=float), fs=fs, nperseg=nperseg, detrend="constant")
        acc = p * (b - a) if acc is None else acc + p * (b - a)
        total += b - a
    if acc is None:
        return None, None
    return f, acc / total


def band_rms(f: np.ndarray, p: np.ndarray, lo: float, hi: float) -> float:
    """RMS amplitude carried by the PSD between lo and hi (Hz)."""
    sel = (f >= lo) & (f <= hi)
    return float(np.sqrt(p[sel].sum() * (f[1] - f[0]))) if sel.any() else np.nan


def refine_spindle_hz(f, p, nominal_hz: float, teeth: int | None, tol: float = 0.04) -> float:
    """Actual spindle frequency from the tallest line within ±tol of the nominal tooth-pass
    (or of order 1 when the tooth-pass is above Nyquist or teeth are unknown)."""
    order = teeth if teeth and teeth * nominal_hz < f[-1] * 0.9 else 1
    target = order * nominal_hz
    sel = (f > target * (1 - tol)) & (f < target * (1 + tol))
    if not sel.any():
        return nominal_hz
    return float(f[sel][np.argmax(p[sel])] / order)


def order_features(prefix: str, x: np.ndarray, mask: np.ndarray, fs: float, spindle_hz: float,
                   teeth: int | None, nperseg: int | None = None, extra_orders: tuple = ()) -> dict:
    """RMS and spindle-order band amplitudes of one dynamic channel during cutting.

    <prefix>_rms  AC RMS over the cutting samples
    <prefix>_o1   band RMS at spindle order 1 (once per revolution: runout, a chipped tooth)
    <prefix>_tp   band RMS summed over the tooth-pass order and its 2nd and 3rd harmonics
                  (only harmonics below 0.45·fs; NaN when teeth unknown or tooth-pass above that)
    <prefix>_hi   band RMS from min((3·teeth + 0.5) orders, fs/4) up to 0.45·fs (broadband rubbing)
    <prefix>_o<k> band RMS at each spindle order k in extra_orders
    Bands are ±max(2 bins, 5% of the spindle frequency) wide; the spindle frequency is refined from
    the spectrum first. Returns also <prefix>_spindle_hz used.
    """
    x = np.asarray(x, dtype=float)
    cut = x[mask]
    out = {f"{prefix}_rms": float(cut.std()) if len(cut) > 3 else np.nan}
    keys = ["o1", "tp", "hi", "spindle_hz"] + [f"o{k}" for k in extra_orders]
    if nperseg is None:
        # aim for ~0.5 Hz bins or better, but never more than a quarter of the cutting stretch
        nperseg = int(2 ** np.ceil(np.log2(fs / 0.5)))
        longest = max((b - a for a, b in runs_of(mask)), default=0)
        while nperseg > 256 and nperseg > longest:
            nperseg //= 2
    f, p = masked_psd(x, mask, fs, nperseg)
    if f is None or not spindle_hz or spindle_hz <= 0:
        out.update({f"{prefix}_{k}": np.nan for k in keys})
        return out
    nyq = 0.45 * fs
    sp = refine_spindle_hz(f, p, spindle_hz, teeth)
    half = max(2 * (f[1] - f[0]), 0.05 * sp)
    out[f"{prefix}_spindle_hz"] = sp
    for k in (1, *extra_orders):
        out[f"{prefix}_o{k}"] = band_rms(f, p, k * sp - half, k * sp + half) if k * sp + half < nyq else np.nan
    tp_hz = [h * teeth * sp for h in (1, 2, 3)] if teeth else []
    tp_hz = [c for c in tp_hz if c + half < nyq]
    out[f"{prefix}_tp"] = (float(np.sqrt(sum(band_rms(f, p, c - half, c + half) ** 2 for c in tp_hz)))
                           if tp_hz else np.nan)
    lo = min((3 * (teeth or 1) + 0.5) * sp, fs / 4)
    out[f"{prefix}_hi"] = band_rms(f, p, lo, nyq)
    return out


# ---------- zip members without unzipping (also works on a partial download) ----------

def zip_index(path: Path) -> dict[str, tuple[int, int, int]]:
    """name -> (data offset, compressed size, method) for every complete file member.

    A finished archive is read through its central directory. A partial one (still downloading,
    no central directory yet) is walked header by header from the start; members written with a
    trailing data descriptor (sizes not in the local header) are delimited by finding the
    descriptor whose recorded compressed size matches the distance travelled.
    """
    try:
        with zipfile.ZipFile(path) as z:
            infos = [i for i in z.infolist() if not i.is_dir()]
        idx = {}
        with open(path, "rb") as f:
            for i in infos:
                f.seek(i.header_offset)
                h = f.read(30)
                nl, el = struct.unpack("<HH", h[26:30])
                idx[i.filename] = (i.header_offset + 30 + nl + el, i.compress_size, i.compress_type)
        return idx
    except zipfile.BadZipFile:
        pass
    size = os.path.getsize(path)
    idx, pos = {}, 0
    with open(path, "rb") as f:
        while pos + 30 < size:
            f.seek(pos)
            h = f.read(30)
            if h[:4] != b"PK\x03\x04":
                break
            flag, method = struct.unpack("<HH", h[6:10])
            csz = struct.unpack("<I", h[18:22])[0]
            nl, el = struct.unpack("<HH", h[26:30])
            name = f.read(nl).decode("utf-8", errors="replace")
            data_at = pos + 30 + nl + el
            if flag & 0x08:  # sizes follow the data in a descriptor
                found, chunk = None, 1 << 25
                while found is None:
                    f.seek(data_at)
                    buf = f.read(min(chunk, size - data_at))
                    q = buf.find(b"PK\x07\x08")
                    while q >= 0 and q + 16 <= len(buf):
                        if struct.unpack("<Q", buf[q + 8:q + 16])[0] == q:
                            found = (q, 24)  # zip64 descriptor
                            break
                        if struct.unpack("<I", buf[q + 8:q + 12])[0] == q:
                            found = (q, 16)
                            break
                        q = buf.find(b"PK\x07\x08", q + 1)
                    if found is None:
                        if data_at + len(buf) >= size:
                            return idx  # this member is still downloading
                        chunk *= 2
                csz, nxt = found[0], data_at + found[0] + found[1]
            else:
                nxt = data_at + csz
                if nxt > size:
                    break
            if not name.endswith("/"):
                idx[name] = (data_at, csz, method)
            pos = nxt
    return idx


def zip_read(path: Path, entry: tuple[int, int, int]) -> bytes:
    """Bytes of one member, given its zip_index entry."""
    at, csz, method = entry
    with open(path, "rb") as f:
        f.seek(at)
        blob = f.read(csz)
    return zlib.decompress(blob, -15) if method == 8 else blob


# ---------- life columns and per-tool normalisation ----------

def first_crossing(values: pd.Series, threshold: float) -> int | None:
    """Position of the first value >= threshold, or None."""
    hit = np.flatnonzero(np.asarray(values, dtype=float) >= threshold)
    return int(hit[0]) if len(hit) else None


def finish(df: pd.DataFrame, eol_pos: dict, rul_unit: str, rel_cols: list[str]) -> pd.DataFrame:
    """life_columns + finalize, for loaders whose rows are already all the runs they have."""
    return finalize(life_columns(df, eol_pos, rul_unit), rel_cols)


def life_columns(df: pd.DataFrame, eol_pos: dict, rul_unit: str) -> pd.DataFrame:
    """Add run_idx, life_frac and rul_native; drop runs after end of life.

    df must already be sorted by tool and time and carry cum_time_s. eol_pos maps tool -> position
    (within that tool's rows) of its end-of-life run, and `eol_reached` must be set by the loader.
    """
    parts, dropped = [], 0
    for tool, g in df.groupby("tool", sort=False):
        g = g.reset_index(drop=True)
        e = eol_pos[tool]
        dropped += len(g) - e - 1
        g = g.iloc[: e + 1].copy()
        g["run_idx"] = np.arange(len(g))
        g["rul_native"] = e - g["run_idx"]
        g["life_frac"] = g["cum_time_s"] / g["cum_time_s"].iloc[-1]
        parts.append(g)
    out = pd.concat(parts, ignore_index=True)
    out["rul_unit"] = rul_unit
    out.attrs["dropped_after_eol"] = dropped
    return out


def finalize(df: pd.DataFrame, rel_cols: list[str]) -> pd.DataFrame:
    """Add the _rel features and put the common columns first."""
    dropped = df.attrs.get("dropped_after_eol", 0)
    out = add_relative(df, rel_cols)
    vib_rel = [c for c in out.columns if c.startswith("vib_") and c.endswith("_rms_rel")]
    out["vib_rms_rel"] = out[vib_rel].mean(axis=1) if vib_rel else np.nan
    out["force_rel"] = out["force_res_abs_rel"] if "force_res_abs_rel" in out.columns else np.nan
    for c in SHARED:
        if c not in out.columns:
            out[c] = np.nan
    front = [c for c in BASE_COLS if c in out.columns]
    out = out[front + [c for c in out.columns if c not in front]]
    out.attrs["dropped_after_eol"] = dropped
    return out


BASELINE_RUNS = 3  # "when new" = the tool's first 3 runs with a value


def causal_baseline(values: np.ndarray, usable: np.ndarray | None = None, k: int = BASELINE_RUNS) -> np.ndarray:
    """Baseline for every run, using only runs up to and including it (never later ones).

    At run t the baseline is the median of the first min(k, seen so far) usable runs with a value.
    It never depends on how long the tool will live, so the "relative to new" features carry no
    information about the future. Before any usable run has been seen, all runs so far are used.
    """
    values = np.asarray(values, dtype=float)
    usable = np.ones(len(values), bool) if usable is None else np.asarray(usable, bool)
    out = np.full(len(values), np.nan)
    picked, seen = [], []
    for t, v in enumerate(values):
        if np.isfinite(v):
            seen.append(v)
            if usable[t] and len(picked) < k:
                picked.append(v)
        pool = picked if picked else seen
        out[t] = np.median(pool) if pool else np.nan
    return out


def add_relative(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """<col>_rel = col ÷ the same tool's causal early-life baseline (see causal_baseline).

    spindle_load_abs becomes spindle_load_rel. Rows must be in time order within each tool.
    """
    df = df.copy()
    new = {}
    for col in cols:
        if col not in df.columns:
            continue
        name = "spindle_load_rel" if col == "spindle_load_abs" else f"{col}_rel"
        rel = pd.Series(np.nan, index=df.index)
        for _, g in df.groupby("tool", sort=False):
            base = causal_baseline(g[col].to_numpy())
            with np.errstate(divide="ignore", invalid="ignore"):
                r = g[col].to_numpy() / base
            r[~np.isfinite(r) | (base == 0)] = np.nan
            rel.loc[g.index] = r
        new[name] = rel
    for name, rel in new.items():
        df[name] = rel
    return df
