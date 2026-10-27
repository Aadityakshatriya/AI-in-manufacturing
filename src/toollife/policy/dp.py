"""Exact optimal stopping for one cutter given its predicted failure curve.

Objective: the long-run AVERAGE cost per good cycle (renewal-reward ratio ΣA / ΣB over many
cutters; not a discounted cost). A ratio is turned into an ordinary stopping problem with
Dinkelbach's method: for a guess g of the long-run ratio, each cutter minimises E[A − g·B]
("every good cycle earns back g"). The policy that is optimal for the true ratio g* has
E[A − g*·B] = 0, and no policy does better (Ross 1983; rl-design.md §3.1).

For a given g and a curve h(1..K) the problem is solved exactly by backward induction over the
steps j = K, …, 1 ahead:

  V(K)  = change cost                                   (horizon: assume a change after K cycles)
  keep_j = h(j+1)·break_cost + (1 − h(j+1))·(survive_cost + V(j+1))
  V(j)  = min(change cost, keep_j)
  decision now: change iff change cost < keep_0

where change cost = a_change − g·b_change, break_cost = a_break − g·b_break and
survive_cost = a_survive − g·b_survive (see costs.Econ).

Assumptions:
  * The curve is taken at face value (the predictor is trusted to be calibrated). Given a fixed
    curve, no new information arrives, so "plan now" and "re-plan every cycle" agree; the policy
    still re-solves after every cycle with the newest curve (receding horizon).
  * Horizon K (60 for the yardsticks): a cutter still running K cycles from now is assumed changed
    then. This can only make "keep" look slightly worse when the cutter is expected to outlive K;
    in that case keep wins by a wide margin anyway.
  * g comes from training cutters only. "dp": Dinkelbach's fixed-point iteration on their real
    replays (g ← realised ratio of the policy with g, until it stops changing), i.e. the DP trusts
    the curves completely. "dp_tuned": g is grid-searched for the lowest training ratio, the same
    tuning effort the threshold rules get. With miscalibrated curves the fixed point can be poor
    (breakages raise g, a high g makes keeping look better, which causes breakages); a tuned g lets
    the DP absorb over- or under-confidence of the predictor in one number.

The one-step rule of costs.md §7.3 is the special case with horizon K = 1 (compare "change now"
with "one more cycle, then change"). It is optimal whenever the hazard only rises (monotone case).
"""

from __future__ import annotations

import numpy as np

from toollife.policy.costs import Econ
from toollife.policy.replay import Outcome, pooled, replay


def keep_change_values(h: np.ndarray, econ: Econ, g: float, end_type: str = "break") -> tuple[np.ndarray, float]:
    """Expected transformed cost E[A − g·B] of keeping now (optimally afterwards) and of changing now,
    for curves h[N, K]. `end_type` picks the cost of reaching the end of life (break or wear limit)."""
    h = np.clip(np.atleast_2d(np.asarray(h, float)), 0.0, 1.0)
    change = econ.a_change - g * econ.b_change
    a_end, b_end = econ.end(end_type)
    brk = a_end - g * b_end
    surv = econ.a_survive - g * econ.b_survive
    V = np.full(h.shape[0], change)
    keep = V
    for j in range(h.shape[1] - 1, -1, -1):
        keep = h[:, j] * brk + (1.0 - h[:, j]) * (surv + V)
        V = np.minimum(change, keep)
    return keep, change


def dp_flags(hazard: np.ndarray, econ: Econ, g: float, horizon: int | None = None,
             end_type: str = "break") -> np.ndarray:
    """Change decisions for every row of a life's curves (horizon=1 gives the one-step rule)."""
    h = hazard if horizon is None else hazard[:, :horizon]
    keep, change = keep_change_values(h, econ, g, end_type)
    return change < keep


def dinkelbach(lives, flags_for_g, econ: Econ, g0: float, iters: int = 60, tol: float = 1e-10) -> tuple[float, float]:
    """Fixed point g = realised ratio of the policy built with g, on training lives.

    The realised ratio of a finite replay is a step function of g, so the iteration can cycle; we
    keep the g whose policy realised the lowest ratio. Returns (g, realised ratio)."""
    g, best = g0, (np.inf, g0)
    for _ in range(iters):
        r = pooled([replay(l, flags_for_g(l, g), econ) for l in lives])
        best = min(best, (r, g))
        if abs(r - g) <= tol * max(1.0, abs(g)):
            break
        g = r
    return best[1], best[0]


class DPPolicy:
    """Exact optimal stopping under the predicted curve, re-solved after every cycle."""

    def __init__(self, horizon: int | None = None, tune: str = "dinkelbach"):
        self.horizon, self.tune = horizon, tune
        self.name = "dp" if tune == "dinkelbach" else "dp_tuned"
        self.g = None

    def fit(self, lives, econ: Econ):
        self.econ = econ
        flags = lambda l, g: dp_flags(l.hazard, econ, g, self.horizon, l.end_type)
        g0 = pooled([replay(l, np.zeros(l.L, bool), econ) for l in lives])  # run-to-failure ratio
        if self.tune == "dinkelbach":
            self.g, self.train_ratio = dinkelbach(lives, flags, econ, g0)
            return self
        # Grid between the best conceivable ratio (every cycle good, no change cost) and far above
        # run-to-failure; lowest training ratio wins, ties take the middle of the plateau.
        floor = econ.a_survive / econ.b_survive
        cands = floor + (g0 - floor) * np.geomspace(1e-3, 100, 81)
        ratios = np.array([pooled([replay(l, flags(l, g), econ) for l in lives]) for g in cands])
        tied = np.flatnonzero(np.isclose(ratios, ratios.min(), rtol=1e-12, atol=0.0))
        self.g, self.train_ratio = float(cands[tied[len(tied) // 2]]), float(ratios.min())
        return self

    def flags(self, life) -> np.ndarray:
        return dp_flags(life.hazard, self.econ, self.g, self.horizon, life.end_type)

    @property
    def params(self) -> dict:
        return {"g": self.g}


class OneStepPolicy(DPPolicy):
    """costs.md §7.3: change once P(fail next cycle) exceeds a / (a + c_m + C_f − C_p), a = g − c_m.
    Identical to the DP with a one-step horizon; g by the same Dinkelbach iteration."""

    def __init__(self):
        super().__init__(horizon=1)
        self.name = "one_step"


def oracle_outcome(life, econ: Econ) -> Outcome:
    """Perfect knowledge: change right after the L-th good cycle (nobody can actually do this)."""
    flags = np.zeros(life.L, bool)
    flags[-1] = True
    return replay(life, flags, econ)
