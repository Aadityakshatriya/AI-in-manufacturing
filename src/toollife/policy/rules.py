"""Simple keep-or-change rules, each tuned on training cutters only (rl-design.md §6.1, B0–B4).

Every rule exposes fit(train_lives, econ) and flags(life) -> bool[L] (True = change after that row;
see replay.py). Tuning: grid search for the lowest pooled training ratio ΣA / ΣB. With 12 training
lives the ratio is a step function with flat stretches, so among exactly tied candidates we take
the middle one (the centre of the best plateau), not the first.

  never        B0  run every cutter until it fails (lower bound)
  fixed        B1  change after N good cycles, one N for all cutters (uses no predictions)
  fixed_group  B1  one N per setting group (Rzeszów: radial depth 4.5 or 8 mm; known before cutting);
                   falls back to the overall N for a group with no training cutter
  rul_q10      B2  change once the predicted 10th-percentile remaining life is <= m cycles
  hazard       B3  change once the predicted next-cycle failure chance is >= h* (control limit)
  one_step     B4  costs.md §7.3 rule (in dp.py)
  dp               exact optimal stopping under the predicted curve, g by Dinkelbach (in dp.py)
  dp_tuned         the same DP with g grid-searched on training cutters (in dp.py)
  (A one-step rule with a grid-searched g is exactly the hazard threshold, so it is not repeated.)
"""

from __future__ import annotations

import numpy as np

from toollife.policy.costs import Econ
from toollife.policy.dp import DPPolicy, OneStepPolicy


def _pick(cands, ratios):
    ratios = np.asarray(ratios, float)
    tied = np.flatnonzero(np.isclose(ratios, ratios.min(), rtol=1e-12, atol=0.0))
    return cands[tied[len(tied) // 2]]


def _ratios_for_stops(lives, stops: np.ndarray, econ: Econ) -> np.ndarray:
    """Pooled ratio for every candidate, given stops[i, c] = good cycles before changing life i under
    candidate c (a value > L means it ran to failure)."""
    A = np.zeros(stops.shape[1])
    B = np.zeros(stops.shape[1])
    for life, s in zip(lives, stops):
        a_end, b_end = econ.end(life.end_type)
        fails = s > life.L
        A += np.where(fails, life.L * econ.a_survive + a_end, s * econ.a_survive + econ.a_change)
        B += np.where(fails, life.L * econ.b_survive + b_end, s * econ.b_survive + econ.b_change)
    return A / B


class NeverChange:
    name = "never"
    params: dict = {}

    def fit(self, lives, econ):
        return self

    def flags(self, life):
        return np.zeros(life.L, bool)


class FixedInterval:
    def __init__(self, by_group: bool = False):
        self.by_group = by_group
        self.name = "fixed_group" if by_group else "fixed"

    def _best(self, lives, econ):
        cands = np.arange(1, max(l.L for l in lives) + 2)  # the last candidate means "never"
        stops = np.tile(cands, (len(lives), 1))
        return int(_pick(cands, _ratios_for_stops(lives, stops, econ)))

    def fit(self, lives, econ):
        self.N = self._best(lives, econ)
        self.N_group = {}
        if self.by_group:
            for grp in sorted({l.group for l in lives}):
                self.N_group[grp] = self._best([l for l in lives if l.group == grp], econ)
        return self

    def flags(self, life):
        N = self.N_group.get(life.group, self.N)
        f = np.zeros(life.L, bool)
        if N <= life.L:
            f[N - 1] = True
        return f

    @property
    def params(self):
        return {"N": self.N} | {f"N_{g}": n for g, n in self.N_group.items()}


class RulQuantile:
    """Change once the q-th quantile of the predicted remaining life is <= m (q = 0.1 by default:
    "even the cautious end of the forecast says it will fail within m cycles")."""

    def __init__(self, col: int = 0, name: str = "rul_q10"):
        self.col, self.name = col, name

    def fit(self, lives, econ):
        cands = np.arange(0, lives[0].K + 1)  # m = 0 never fires: remaining life is at least 1
        stops = []
        for l in lives:
            runmin = np.minimum.accumulate(l.rul_q[:, self.col])
            stops.append(np.searchsorted(-runmin, -cands, side="left") + 1)  # first row with runmin <= m
        self.m = int(_pick(cands, _ratios_for_stops(lives, np.array(stops), econ)))
        return self

    def flags(self, life):
        return life.rul_q[:, self.col] <= self.m

    @property
    def params(self):
        return {"m": self.m}


class HazardThreshold:
    """Control-limit policy: change once hazard_1 >= h* (Makis & Jardine 1992)."""

    name = "hazard"
    CANDS = np.concatenate([np.logspace(-5, 0, 101), [1.01]])  # 1.01 never fires

    def fit(self, lives, econ):
        stops = []
        for l in lives:
            runmax = np.maximum.accumulate(l.hazard[:, 0])
            stops.append(np.searchsorted(runmax, self.CANDS, side="left") + 1)  # first row with runmax >= h*
        self.h = float(_pick(self.CANDS, _ratios_for_stops(lives, np.array(stops), econ)))
        return self

    def flags(self, life):
        return life.hazard[:, 0] >= self.h

    @property
    def params(self):
        return {"h_star": self.h}


def make_policies():
    """Fresh, unfitted instances of every policy compared in the single-cutter study."""
    return [NeverChange(), FixedInterval(), FixedInterval(by_group=True), RulQuantile(), HazardThreshold(),
            OneStepPolicy(), DPPolicy(), DPPolicy(tune="grid")]
