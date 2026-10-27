"""Loaders that put the public milling datasets on one common basis (PLAN.md §1 and §6).

Each module (nasa, luh, mstw, vmc650, hesso) has `load(workers=8) -> DataFrame` returning one row
per recorded run with the common columns below plus that dataset's physics features. Shared
helpers (cutting mask, spectra in spindle orders, life columns, per-tool normalisation) live in
`common.py`. Rzeszów stays in `toollife.rzeszow`.
"""

NAMES = ["nasa", "luh", "mstw", "vmc650", "hesso"]
