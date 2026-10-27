"""Rule baselines that act inside the workshop environment (rl-design.md §6.2, reduced).

Each rule decides per machine whether it wants a change, then the setter goes to the most urgent
request (a broken machine first, then the highest priority); everyone else keeps cutting. Each rule
also picks one speed for the whole episode: "normal", "slow", or "auto" = slow only if Taylor's law
with this episode's n (visible to every policy) says slow earns more per tick for an average life.

  fixed(N)      change after N parts                               (priority: parts / N)
  hazard(h*)    change once the next part's failure chance >= h*  (priority: that chance)
  dp(g)         exact single-cutter DP on the machine's curve      (priority: how much cheaper changing is)
  oracle        perfect knowledge: change just before the real failure (reference only)

Rules only read what a shop would know (curves, ages, setter, spares), never the failure point,
except the oracle. Thresholds and g are tuned on training cutters only (`tune`).
"""

from __future__ import annotations

import numpy as np

from toollife.policy.costs import Econ
from toollife.policy.curves import stretch
from toollife.policy.dp import dinkelbach, dp_flags, keep_change_values
from toollife.policy.replay import pooled, replay
from toollife.rl.workshop_env import CHANGE, RUN, SLOW, WorkshopEnv


def slow_pays(env: WorkshopEnv, mean_life: float) -> bool:
    """Taylor check: profit per tick of an average cutter at slow vs normal speed (planned changes)."""
    m, s = env.cfg.money, env.cfg.slow_speed
    def rate(parts, ticks_per_part):
        return (parts * m.price - m.tool_price) / (parts * ticks_per_part + m.d_change)
    return rate(mean_life / env.rho, 1 / s) > rate(mean_life, 1.0)


def slow_econ(econ: Econ, s: float) -> Econ:
    """Event model for a slow part: same money, 1/s ticks per part."""
    return Econ(econ.a_survive, econ.b_survive / s, econ.a_break, econ.b_break, econ.a_change, econ.b_change,
                econ.a_wear, econ.b_wear)


class RulePolicy:
    def __init__(self, kind: str, param: float | None = None, speed: str = "normal", mean_life: float = 75.0):
        self.kind, self.param, self.speed, self.mean_life = kind, param, speed, mean_life
        self.name = f"{kind}_{speed}"

    def _slow(self, env):
        return env.cfg.allow_slow and (self.speed == "slow" or (self.speed == "auto" and slow_pays(env, self.mean_life)))

    def want(self, env, m, slow: bool):
        """(wants a change, priority) for a healthy, idle machine."""
        if m.parts == 0:
            return False, 0.0
        if self.kind == "fixed":
            return m.parts >= self.param, m.parts / self.param
        if self.kind == "hazard":
            p = env.risk_next(m, 1, slow)
            return p >= self.param, p
        if self.kind == "dp":
            h, frac = env.curve(m)
            if h is None:
                return False, 0.0
            econ = env.cfg.money.econ()
            if slow:  # a slow part uses rho cycles of life: survival over parts is S(rho · j)
                h, econ = stretch(h, 1 / env.rho), slow_econ(econ, env.cfg.slow_speed)
            keep, change = keep_change_values(h[None], econ, self.param, m.life.end_type)
            return bool(change < keep[0]), float(keep[0] - change)
        if self.kind == "oracle":
            inc = (env.cfg.slow_speed if slow else 1.0) ** (1 / env.n)
            return m.damage + inc > m.fail_at, 1.0
        raise ValueError(self.kind)

    def act(self, env: WorkshopEnv) -> int:
        slow = self._slow(env)
        mk = env.machine_masks()
        acts, requests = [], []
        for i, m in enumerate(env.machines):
            acts.append(SLOW if (slow and mk[i, SLOW]) else RUN)
            if not mk[i, CHANGE]:
                continue
            if m.broken:
                requests.append((np.inf, i))
            else:
                w, pr = self.want(env, m, slow)
                if w:
                    requests.append((pr, i))
        if requests:
            acts[max(requests)[1]] = CHANGE
        return env.encode(acts)


def run_episode(env: WorkshopEnv, act, seed: int, need_obs: bool = True) -> dict:
    """Play one episode with `act(env, obs) -> action` and return the stats (profit in rupees)."""
    env.compute_obs = need_obs
    obs, _ = env.reset(seed=seed)
    done = False
    while not done:
        obs, _, term, trunc, _ = env.step(act(env, obs))
        done = term or trunc
    s = dict(env.stats)
    s["profit_per_1000_ticks"] = 1000 * s["profit"] / env.t
    s["breaks_per_1000_parts"] = 1000 * s["breaks"] / max(1, s["parts"])
    s["slow_share"] = s["slow_ticks"] / max(1, s["cut_ticks"])
    s["taylor_n"] = env.n
    return s


def mean_profit(env, policy, seeds) -> float:
    return float(np.mean([run_episode(env, lambda e, o: policy.act(e), s, need_obs=False)["profit"] for s in seeds]))


# ---------------------------------------------------------------------------------------------
# g for the DP rule


def expected_outcome(life, flags, econ: Econ, cap_rows: int) -> tuple[float, float]:
    """Model world: expected (A, B) of one life when the failure follows the curves' own hazard_1
    and the policy changes at the first row with flags True (rows past the recording use the
    shifted last curve, as the environment does)."""
    A = B = 0.0
    alive = 1.0
    a_end, b_end = econ.end(life.end_type)
    for a in range(cap_rows):
        A += alive * econ.a_survive        # part a+1 was good (the first part never fails)
        B += alive * econ.b_survive
        if flags[a] or a == cap_rows - 1:
            return A + alive * econ.a_change, B + alive * econ.b_change
        h = life.curve_at(a)[0]
        A += alive * h * a_end
        B += alive * h * b_end
        alive *= 1 - h
    return A, B


def dp_g(lives, econ: Econ, world: str) -> float:
    """Long-run −profit per tick of the DP rule by Dinkelbach's iteration (single machine, normal
    speed): on real replays in the 'replay' world, on exact expectations in the 'model' world,
    where the DP with this g is the optimal policy."""
    flags = lambda l, g, H: dp_flags(H, econ, g, end_type=l.end_type)
    if world == "replay":
        g0 = pooled([replay(l, np.zeros(l.L, bool), econ) for l in lives])
        return dinkelbach(lives, lambda l, g: flags(l, g, l.hazard), econ, g0)[0]
    mats = {l.key: np.stack([l.curve_at(a) for a in range(5 * l.L + 200)]) for l in lives}
    g = 0.0
    for _ in range(100):
        AB = [expected_outcome(l, flags(l, g, mats[l.key]), econ, len(mats[l.key])) for l in lives]
        g_new = sum(a for a, _ in AB) / sum(b for _, b in AB)
        if abs(g_new - g) < 1e-9 * max(1.0, abs(g)):
            break
        g = g_new
    return g_new


def tune(make_env, kind: str, grid, speed: str, mean_life: float, seeds) -> RulePolicy:
    """Grid-search one rule's parameter for the highest mean training profit (same seeds for all)."""
    env = make_env()
    best = max(grid, key=lambda p: mean_profit(env, RulePolicy(kind, p, speed, mean_life), seeds))
    return RulePolicy(kind, best, speed, mean_life)
