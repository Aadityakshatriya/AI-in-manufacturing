"""Loader for the Rzeszów milling dataset (Piecuch & Żabiński, Scientific Data 2025).

One row = one recorded milling cycle of one physical cutter.
The answer we predict is `rul`: cycles remaining before that cutter failed.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"

# The cutter that broke during its very first cycle. It has no wear history,
# so it is kept out of training and testing and reported separately.
OUTLIER_TOOL = 11

SETTING_COLS = ["tool_type", "adoc_mm", "rdoc_mm", "hardness_hrc", "holder_mm"]


def load_table() -> pd.DataFrame:
    """Metadata plus the 120 released sensor summaries, one row per cycle."""
    meta = pd.read_excel(RAW / "metadata.xlsx")
    meta = meta.rename(
        columns={
            "ExperimentIndex": "file",
            "ToolIndex": "tool",
            "MillingToolType": "tool_type",
            "ADOC [mm]": "adoc_mm",
            "RDOC [mm]": "rdoc_mm",
            "HardnessMean [HRC]": "hardness_hrc",
            "ToolHolderLength [mm]": "holder_mm",
            "CycleToFailure": "rul",
            "CycleToFailureNormalized": "rul_frac",
        }
    )

    # The feature CSV has its real column names in its first data row.
    raw = pd.read_csv(RAW / "features.csv", sep=";", header=None, low_memory=False)
    names = raw.iloc[1].tolist()
    feats = raw.iloc[2:].reset_index(drop=True)
    feats.columns = names
    sensor_cols = names[:120]
    feats[sensor_cols] = feats[sensor_cols].apply(
        lambda c: pd.to_numeric(c.astype(str).str.replace(",", "."), errors="coerce")
    )
    feats = feats[["FileName", "NumberOfCycle", *sensor_cols]].rename(
        columns={"FileName": "file", "NumberOfCycle": "cycle"}
    )
    feats["cycle"] = feats["cycle"].astype(int)

    df = meta.merge(feats, on="file", how="inner", validate="one_to_one")
    if len(df) != len(meta):
        raise ValueError(f"metadata/features mismatch: {len(meta)} vs {len(df)} rows")

    df = df.sort_values(["tool", "cycle"]).reset_index(drop=True)
    # Lifetime of each cutter in recorded cycles, and how far through it each row is.
    df["life"] = df.groupby("tool")["rul"].transform("max") + 1
    df["age"] = df["life"] - 1 - df["rul"]
    df["life_frac_used"] = df["age"] / df["life"]
    return df


def sensor_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(("Accelerometer", "Current"))]


def usable(df: pd.DataFrame) -> pd.DataFrame:
    """The 13 cutters with a normal wear history."""
    return df[df["tool"] != OUTLIER_TOOL].reset_index(drop=True)
