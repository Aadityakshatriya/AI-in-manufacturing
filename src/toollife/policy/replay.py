"""Replay real held-out cutters cycle by cycle under a keep-or-change policy.

Every policy here is written as `flags(life) -> bool[L]`: flags[a] is the decision taken after row a
(the cutter has just finished its (a+1)-th good cycle) and True means "change now". Each policy
computes flags[a] from row a only (and the cutter's age and settings), so it only ever sees
predictions up to now. The replay takes the first True:

  first True at row a   → the cutter was changed after a+1 good cycles (never broke)
  no True at all        → the cutter ran into its real failure: L good cycles, then the break

Because the real failure cycle is known, the outcome is exact; only the costs are assumed
(rl-design.md §3.1, claim level 1). Totals over several cutters are pooled as ΣA / ΣB, the
renewal-reward ratio a shop sees over many cutters (rl-design.md §6.1).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from toollife.policy.costs import Econ


@dataclass
class Outcome:
    tool: str
    L: int
    good: int          # good cycles made with this cutter
    broke: bool        # ran into its real end of life
    A: float           # cost (or −profit) of this life
    B: float           # good cycles (or ticks) of this life

    @property
    def wasted(self) -> int:
        """Good cycles left unused when the cutter was changed early (0 if it broke)."""
        return 0 if self.broke else self.L - self.good

    @property
    def life_used(self) -> float:
        return self.good / self.L


def first_change(flags: np.ndarray) -> int | None:
    idx = np.flatnonzero(flags)
    return int(idx[0]) if idx.size else None


def replay(life, flags: np.ndarray, econ: Econ) -> Outcome:
    a = first_change(np.asarray(flags, bool)[: life.L])
    if a is None:
        a_end, b_end = econ.end(life.end_type)
        return Outcome(life.tool, life.L, life.L, True,
                       life.L * econ.a_survive + a_end, life.L * econ.b_survive + b_end)
    n = a + 1
    return Outcome(life.tool, life.L, n, False, n * econ.a_survive + econ.a_change, n * econ.b_survive + econ.b_change)


def stop_outcome(life, stop: int | None, econ: Econ) -> tuple[float, float]:
    """(A, B) when the cutter is changed after `stop` good cycles (None or stop > L: it fails)."""
    if stop is None or stop > life.L:
        a_end, b_end = econ.end(life.end_type)
        return life.L * econ.a_survive + a_end, life.L * econ.b_survive + b_end
    return stop * econ.a_survive + econ.a_change, stop * econ.b_survive + econ.b_change


def pooled(outcomes) -> float:
    """Renewal-reward ratio ΣA / ΣB over cutters (cost per good cycle for costs.md)."""
    A = sum(o.A for o in outcomes)
    B = sum(o.B for o in outcomes)
    return A / B if B > 0 else float("inf")


def policy_ratio(lives, policy, econ: Econ) -> float:
    return pooled([replay(l, policy.flags(l), econ) for l in lives])


def summarise(outcomes) -> dict:
    """Metrics of one policy over a set of replayed cutters."""
    return dict(
        cost_per_good=pooled(outcomes),
        breakages=sum(o.broke for o in outcomes),
        n_cutters=len(outcomes),
        life_used=float(np.mean([o.life_used for o in outcomes])),
        wasted_cycles=float(np.mean([o.wasted for o in outcomes])),
        good_cycles=int(sum(o.good for o in outcomes)),
        mean_cutter_cost_per_good=float(np.mean([o.A / o.B for o in outcomes if o.B > 0])),
    )
