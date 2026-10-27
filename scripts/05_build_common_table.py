"""Put the public milling datasets on the common basis (PLAN.md §1, §6).

Runs every loader in src/toollife/datasets (each parallelises over its files with a process pool),
then writes
  data/processed/runs_<dataset>.parquet   one row per run, common columns + physics features
  results/common/dataset_summary.csv      tools, runs, life range, end type, signals, rates,
                                          within-tool Spearman of the shared features vs life_frac
  results/common/load_vs_life.png         spindle_load_rel vs life_frac, every tool, one panel each
Rzeszów is not rebuilt here (scripts/09_rzeszow_features.py owns runs_rzeszow.parquet); if that file
exists it is added to the summary and the figure for comparison.

Safe to re-run while downloads are still arriving: LUH uses the run files present, MSTW reads the
partial .zip.part and skips the case still downloading. Re-run once the downloads finish.

Usage: python scripts/05_build_common_table.py [--workers 8] [--only nasa luh mstw vmc650]
"""

import argparse
import importlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.datasets import NAMES
from toollife.datasets.common import PROCESSED, ROOT, SHARED

RESULTS = ROOT / "results" / "common"
MIN_POINTS = 5  # a tool needs this many valid values for its Spearman to count


def tool_spearman(df: pd.DataFrame, col: str) -> tuple[float, float, int]:
    """Mean and SD over tools of the within-tool Spearman between col and life_frac."""
    if col not in df.columns:
        return np.nan, np.nan, 0
    rs = []
    for _, g in df.groupby("tool"):
        g = g[["life_frac", col]].dropna()
        if len(g) >= MIN_POINTS and g[col].nunique() > 1:
            rs.append(spearmanr(g["life_frac"], g[col])[0])
    return (float(np.mean(rs)), float(np.std(rs)), len(rs)) if rs else (np.nan, np.nan, 0)


def summarise(name: str, df: pd.DataFrame, info: dict, status: str) -> dict:
    per_tool = df.groupby("tool").agg(runs=("run_idx", "size"), life_s=("cum_time_s", "max"))
    row = {
        "dataset": name,
        "tools": df["tool"].nunique(),
        "runs": len(df),
        "runs_per_tool_min": int(per_tool["runs"].min()),
        "runs_per_tool_max": int(per_tool["runs"].max()),
        "life_min_min": round(per_tool["life_s"].min() / 60, 1),
        "life_min_max": round(per_tool["life_s"].max() / 60, 1),
        "end_type": ",".join(sorted(df["end_type"].unique())),
        "end_of_life": info.get("end_of_life", ""),
        "machines": df["machine"].nunique(),
        "signals": info.get("signals", ""),
        "rates": info.get("rates", ""),
        "spindle_unit": df["spindle_unit"].iloc[0] if "spindle_unit" in df else "",
        "signal_ok_frac": round(float(df["signal_ok"].mean()), 3) if "signal_ok" in df else np.nan,
        "data_status": status,
    }
    for col in SHARED:
        m, s, n = tool_spearman(df, col)
        row[f"rho_{col}"] = round(m, 2) if np.isfinite(m) else np.nan
        row[f"rho_{col}_sd"] = round(s, 2) if np.isfinite(s) else np.nan
        row[f"rho_{col}_tools"] = n
        row[f"{col}_coverage"] = round(float(df[col].notna().mean()), 3)
    vib = [c for c in df.columns if c.startswith("vib_") and c.endswith("_rms_rel") and c != "vib_rms_rel"]
    row["rho_vib_channels"] = "; ".join(f"{c[4:-8]} {tool_spearman(df, c)[0]:+.2f}" for c in vib)
    return row


def figure(tables: dict[str, pd.DataFrame], path: Path) -> None:
    """Small multiples: each tool a thin gray line, the dataset's binned median in blue."""
    names = list(tables)
    cols = min(3, len(names))
    rows = int(np.ceil(len(names) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(4.2 * cols, 3.3 * rows), sharex=True, sharey=True,
                             squeeze=False, facecolor="#fcfcfb")
    bins = np.linspace(0, 1, 11)
    for ax, name in zip(axes.flat, names):
        df = tables[name].dropna(subset=["spindle_load_rel"])
        ax.set_facecolor("#fcfcfb")
        for _, g in df.groupby("tool"):
            ax.plot(g["life_frac"], g["spindle_load_rel"], color="#b8b7b1", lw=0.8, alpha=0.8)
        which = np.digitize(df["life_frac"], bins[1:-1])  # 0..9 = which tenth of life
        mid = df.groupby(which)["spindle_load_rel"].median()
        ax.plot((bins[mid.index] + bins[mid.index + 1]) / 2, mid.to_numpy(), color="#2a78d6", lw=2.2, marker="o", ms=4)
        ax.axhline(1.0, color="#52514e", lw=0.8, ls=":")
        ax.set_title(f"{name}  ({df['tool'].nunique()} tools, {len(df)} runs)", fontsize=10, color="#0b0b0b", loc="left")
        ax.grid(color="#e4e3df", lw=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(colors="#52514e", labelsize=8)
    for i, ax in enumerate(axes.flat):
        if i >= len(names):
            ax.set_visible(False)
            continue
        ax.tick_params(labelbottom=True)
        if i + cols >= len(names):  # nothing below this panel
            ax.set_xlabel("life fraction (cutting time ÷ time at end of life)", fontsize=8, color="#52514e")
        if i % cols == 0:
            ax.set_ylabel("spindle load ÷ early-life value", fontsize=8, color="#52514e")
    axes[0, 0].set_ylim(0, 3)
    fig.suptitle("Spindle load relative to each tool's early life (gray = one tool, blue = median per tenth of life, "
                 "y clipped at 3)", fontsize=11, color="#0b0b0b", x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    tables, summary = {}, []
    for name in args.only or NAMES:
        try:
            mod = importlib.import_module(f"toollife.datasets.{name}")
        except ModuleNotFoundError:
            print(f"{name}: no loader, skipped")
            continue
        try:
            df = mod.load(workers=args.workers)
        except (FileNotFoundError, ValueError) as e:
            print(f"{name}: not loaded ({e})")
            continue
        status = "complete"
        if df.attrs.get("files_missing"):
            status = f"partial: {df.attrs['files_missing']} run files not downloaded yet"
        if df.attrs.get("archive_complete") is False:
            status = f"partial: archive still downloading, skipped {df.attrs.get('skipped_cases')}"
        df.to_parquet(PROCESSED / f"runs_{name}.parquet")
        tables[name] = df
        summary.append(summarise(name, df, getattr(mod, "INFO", {}), status))
        print(f"{name}: {df['tool'].nunique()} tools, {len(df)} runs ({status}); "
              f"dropped after end of life: {df.attrs.get('dropped_after_eol', 0)}", flush=True)

    rz = PROCESSED / "runs_rzeszow.parquet"
    if rz.exists():  # comparison only; built by scripts/09_rzeszow_features.py
        df = pd.read_parquet(rz)
        tables["rzeszow (ours)"] = df
        summary.append(summarise("rzeszow (ours, from runs_rzeszow.parquet)", df,
                                 {"end_of_life": "breakage", "signals": "see scripts/09_rzeszow_features.py"},
                                 "built by 09_rzeszow_features.py"))

    out = pd.DataFrame(summary)
    out.to_csv(RESULTS / "dataset_summary.csv", index=False)
    print(out[["dataset", "tools", "runs", "life_min_min", "life_min_max", "end_type",
               "rho_spindle_load_rel", "rho_vib_rms_rel", "rho_force_rel", "data_status"]].to_string(index=False))
    if tables:
        figure(tables, RESULTS / "load_vs_life.png")


if __name__ == "__main__":
    main()
