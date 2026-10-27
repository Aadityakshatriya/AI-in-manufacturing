"""Download the public milling datasets into data/raw/<name>/.

Usage: python scripts/00_download.py luh mstw vmc650 hesso nasa
Re-running skips files that are already complete (size check). Sources and licences are
documented in research/next-phase/data-survey.md.
"""

import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def fetch(url: str, dest: Path, size: int | None = None) -> str:
    if dest.exists() and (size is None or dest.stat().st_size == size):
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "toollife-research/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    if size is not None and tmp.stat().st_size != size:
        raise IOError(f"{dest.name}: got {tmp.stat().st_size} bytes, expected {size}")
    tmp.rename(dest)
    return "ok"


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "toollife-research/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def luh() -> None:
    """LUH Hannover: 9 tools on 3 machines, 6,418 HDF5 files (CC BY 4.0, Mendeley zpxs87bjt8)."""
    files = get_json("https://data.mendeley.com/public-api/datasets/zpxs87bjt8")["files"]
    out = RAW / "luh"
    jobs = [(f["content_details"]["download_url"], out / f["filename"], f["size"]) for f in files]
    with ThreadPoolExecutor(12) as pool:
        for i, res in enumerate(pool.map(lambda j: fetch(*j), jobs), 1):
            if i % 500 == 0 or i == len(jobs):
                print(f"luh {i}/{len(jobs)}", flush=True)


def mstw() -> None:
    """MSTW EndMill 2026: 25 tools run to VB 300 µm (CC BY 4.0, Figshare 31801795)."""
    out = RAW / "mstw"
    fetch("https://ndownloader.figshare.com/files/62917744", out / "Tool_Wear_Value_Table.xlsx")
    fetch("https://ndownloader.figshare.com/files/64734885", out / "Sensor_Data_DAQ_updated.zip", 13_095_061_412)
    print("mstw done", flush=True)


def zenodo(record: str, name: str, only: tuple[str, ...] = ()) -> None:
    files = get_json(f"https://zenodo.org/api/records/{record}")["files"]
    for f in files:
        if only and f["key"] not in only:
            continue
        print(name, f["key"], fetch(f["links"]["self"], RAW / name / f["key"], f["size"]), flush=True)


def nasa() -> None:
    """NASA Ames milling (Agogino & Goebel), from the PCoE data repository."""
    scratch = Path("/private/tmp/claude-501/-Users-aaditya-Sarvam-Kivi/e115590c-d8e3-435c-9a5c-6918359f0460/scratchpad/dl/nasa/inner")
    out = RAW / "nasa"
    out.mkdir(parents=True, exist_ok=True)
    for name in ("mill.mat", "Readme.pdf"):
        if (scratch / name).exists() and not (out / name).exists():
            (out / name).write_bytes((scratch / name).read_bytes())
    print("nasa", sorted(p.name for p in out.iterdir()), flush=True)


TASKS = {
    "luh": luh,
    "mstw": mstw,
    "vmc650": lambda: zenodo("21608174", "vmc650"),
    "hesso": lambda: zenodo("6505073", "hesso", ("toolwear_2020_axes.zip", "toolwear_2020_acc.zip")),
    "nasa": nasa,
}

if __name__ == "__main__":
    for name in sys.argv[1:] or TASKS:
        TASKS[name]()
