"""A small simulated workshop for cutter decisions (reduced version of rl-design.md §4), Gymnasium API.

What it is, in two sentences per part:

* Machines. Each machine cuts one dataset cycle per tick (one "part") with a mounted cutter that
  replays a real recorded cutter life from a pool; the agent sees only that cutter's predicted
  failure curve, age and settings. Every machine always has work at one fixed price per good part.
* Actions. Per machine: RUN, SLOW (20 % slower), or CHANGE the cutter; all machines choose together
  as one joint action (3^M choices) and impossible combinations are masked out. RUN on a machine
  that is being changed or is broken just waits (a broken machine may wait while the setter serves
  another).
* Setter and spares. One setter does every change, one at a time: a planned change takes 8 ticks,
  recovering from a breakage 35 ticks (costs.md: 10 and 45 minutes at 1.3 min per cycle). Spare
  cutters arrive on a fixed schedule (default 2 every 50 ticks, at most 6 in stock); with none in
  stock a machine cannot be changed.
* Replay. A mounted cutter fails at exactly the point the real one did ("replay" world): after L
  good parts at normal speed, during part L + 1. In the "model" world the failure point is instead
  drawn from the predictor's own next-cycle hazards, so a perfectly calibrated predictor is the
  truth; that world is used to check RL against the DP, which is optimal there.
* Slowing down (Taylor's law, physics-brief.md B7). At speed s (feed per tooth held) a part takes
  1/s ticks and uses s^(1/n − 1) cycles of cutter life, so life in parts grows by s^(1 − 1/n);
  the exponent n is drawn per episode (default U[0.2, 0.5]) and shown to the agent. This is an
  assumption: every recorded cutter ran at one speed, and our cutters failed by fracture, which
  Taylor's wear law does not describe; at slow speed the agent still sees the curves recorded at
  normal speed for the same amount of life used.
* Reward. Profit in rupees: + price for each good part, − cutter price for each change started,
  − breakage cost (scrapped part, collateral damage, optional extra to set a breakage ratio) for
  each breakage. Fixed machine costs are the same for every policy and left out; downtime costs
  show up as parts not made. Reward is divided by 1,000 for training.
* Episodes. 2,000 ticks, then cut off (truncated, not terminated), with no time-left feature, so
  there is no end-of-episode trick. Cutters start at random ages.
* Augmentation (training only). With probability 0.5 a mounted life is time-warped by
  w ~ LogUniform(0.8, 1.25) (lives.Life.warped), so the agent cannot memorise ~10 real lives.
* Common random numbers. Each machine has its own random stream for the cutters it mounts, so for a
  given seed every policy sees the same sequence of cutters, failure points and Taylor n.

The pool is any list of policy.lives.Life, so lives from other datasets (built from their own
prediction files and data/processed/runs_<dataset>.parquet) can be added without changing this
file. A life that ends at a wear limit instead of a breakage is charged one scrapped part and a
planned-change recovery instead of the breakage cost and recovery.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace

import gymnasium as gym
import numpy as np

from toollife.policy.costs import Econ
from toollife.policy.curves import surv_at

RUN, SLOW, CHANGE = 0, 1, 2
HZ_STEPS = (1, 2, 5, 10, 20, 40)   # steps ahead whose hazard the agent sees


@dataclass(frozen=True)
class Money:
    """Workshop money and times. Defaults: costs.md India-typical, plus one assumed price."""

    price: float = 120.0          # ₹ contribution per good part [assumption: ~₹70 of cutter and machine cost per part, plus margin]
    tool_price: float = 3000.0    # ₹ per cutter (costs.md C_t)
    cycle_min: float = 1.3        # minutes per tick (costs.md t_c)
    change_min: float = 10.0      # planned change (costs.md t_p) → machine and setter busy
    break_min: float = 45.0       # breakage recovery (costs.md t_b) → machine and setter busy
    part_value: float = 3000.0    # part at risk on breakage (costs.md V)
    p_scrap: float = 0.5          # chance the part is scrapped, else 10 % repair (costs.md p_s)
    collateral: float = 1280.0    # collet / holder / spindle damage per breakage (costs.md E_coll)
    kappa: float | None = None    # if set, extra breakage cost so breakage event = kappa × planned change event

    @property
    def d_change(self) -> int:
        return max(1, round(self.change_min / self.cycle_min))

    @property
    def d_break(self) -> int:
        return max(1, round(self.break_min / self.cycle_min))

    @property
    def base_break_cash(self) -> float:
        return self.p_scrap * self.part_value + (1 - self.p_scrap) * 0.1 * self.part_value + self.collateral

    @property
    def planned_event(self) -> float:
        """Cost of a planned change including the parts not made while the machine is down."""
        return self.tool_price + self.d_change * self.price

    @property
    def break_cash(self) -> float:
        if self.kappa is None:
            return self.base_break_cash
        rest = self.tool_price + (self.d_break + 1) * self.price
        return max(0.0, self.kappa * self.planned_event - rest)

    @property
    def break_ratio(self) -> float:
        """Breakage event ÷ planned change event, both including lost parts (rl-design §4.7 κ)."""
        return (self.tool_price + self.break_cash + (self.d_break + 1) * self.price) / self.planned_event

    def econ(self) -> Econ:
        """Single-machine renewal model for the DP: minimise −profit per tick."""
        return Econ(a_survive=-self.price, b_survive=1.0,
                    a_break=self.break_cash + self.tool_price, b_break=1.0 + self.d_break,
                    a_change=self.tool_price, b_change=float(self.d_change),
                    a_wear=self.part_value + self.tool_price, b_wear=1.0 + self.d_change)


@dataclass(frozen=True)
class Config:
    machines: int = 3
    allow_slow: bool = True
    slow_speed: float = 0.8
    taylor_n: tuple = (0.2, 0.5)        # U[lo, hi] per episode; (x, x) fixes it
    spares: bool = True                 # False: unlimited spares (single-machine check)
    spare_start: int = 3
    spare_every: int = 50
    spare_qty: int = 2
    spare_cap: int = 6
    T: int = 2000
    world: str = "replay"               # 'replay' | 'model'
    augment: bool = False               # training only
    warp: tuple = (0.8, 1.25)
    augment_prob: float = 0.5
    random_start: bool = True
    obs_conditions: bool = True
    reward_scale: float = 1e-3
    money: Money = field(default_factory=Money)


class Machine:
    __slots__ = ("life", "fail_at", "damage", "parts", "progress", "busy", "broken")

    def __init__(self):
        self.life, self.fail_at, self.damage, self.parts = None, 0.0, 0.0, 0
        self.progress, self.busy, self.broken = 0.0, 0, False


class WorkshopEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, pool, config: Config = Config()):
        assert len(pool) > 0
        self.pool, self.cfg = list(pool), config
        M = config.machines
        self.digits = np.array(list(itertools.product(range(3), repeat=M)))[:, ::-1]  # digit i = machine i
        self.action_space = gym.spaces.Discrete(3 ** M)
        self.per_machine = 1 + len(HZ_STEPS) + 2 + 2 + 2 + 3 + 4  # see _obs
        self.observation_space = gym.spaces.Box(-5.0, 5.0, (M * self.per_machine + 4,), np.float32)
        self._h1_cache, self._warp_cache = {}, {}
        self.compute_obs = True  # rule baselines read the state directly and switch this off for speed
        self.reset(seed=0)

    # ------------------------------------------------------------------ episode set-up

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        ss = np.random.SeedSequence(self.np_random.integers(2**63))
        streams = ss.spawn(self.cfg.machines + 1)
        self.rng_ep = np.random.default_rng(streams[0])
        self.rng_mount = [np.random.default_rng(s) for s in streams[1:]]
        lo, hi = self.cfg.taylor_n
        self.n = float(self.rng_ep.uniform(lo, hi))
        self.rho = self.cfg.slow_speed ** (1 / self.n - 1)  # cycles of life used per slow part
        self.t, self.setter, self.spares = 0, 0, self.cfg.spare_start
        self.stats = dict(profit=0.0, revenue=0.0, tools=0.0, breakage=0.0, parts=0, breaks=0, changes=0,
                          slow_ticks=0, cut_ticks=0, wait_ticks=0)
        self.machines = [Machine() for _ in range(self.cfg.machines)]
        for i, m in enumerate(self.machines):
            self._mount(i)
            if self.cfg.random_start and self.rng_ep.random() < 0.8:
                m.damage = float(self.rng_ep.integers(0, max(1, int(m.fail_at))))
                m.parts = int(m.damage)
        return self._obs(), {}

    def _life_for(self, i):
        """Draw the next cutter for machine i from its own stream (5 numbers per mount, always)."""
        u = self.rng_mount[i].random(5)
        life = self.pool[int(u[0] * len(self.pool))]
        if self.cfg.augment and u[2] < self.cfg.augment_prob:
            lo, hi = np.log(self.cfg.warp)
            w = round(float(np.exp(lo + u[3] * (hi - lo))), 2)
            key = (life.key, w)
            if key not in self._warp_cache:
                self._warp_cache[key] = life.warped(w)
            life = self._warp_cache[key]
        if self.cfg.world == "replay":
            L = life.L
        else:  # model world: failure drawn from the curve's own next-cycle hazards (inverse transform)
            surv = self._model_survival(life)
            L = int(np.searchsorted(-surv, -u[4], side="left")) + 1  # first c with S(c) < U
        return life, L + u[1]

    def _model_survival(self, life):
        """S(c) for c = 1, 2, …: chance of having made c + 1 good parts, from hazard_1 of rows 0, 1, …
        Past the recorded rows the last curve is shifted forward; capped at 5 L + 200 rows."""
        key = (life.key, life.warp)
        if key not in self._h1_cache:
            cap = 5 * life.L + 200
            h1 = np.array([life.curve_at(a)[0] for a in range(cap)])
            s = np.cumprod(1 - h1)
            s[-1] = 0.0  # forced end at the cap
            self._h1_cache[key] = s
        return self._h1_cache[key]

    def _mount(self, i):
        m = self.machines[i]
        m.life, m.fail_at = self._life_for(i)
        m.damage, m.parts, m.progress, m.busy, m.broken = 0.0, 0, 0.0, 0, False

    # ------------------------------------------------------------------ masks

    def machine_masks(self) -> np.ndarray:
        """[M, 3] allowed actions per machine, before the one-setter / spares rule."""
        can_change = self.setter == 0 and (not self.cfg.spares or self.spares > 0)
        mk = np.zeros((self.cfg.machines, 3), bool)
        for i, m in enumerate(self.machines):
            if m.busy > 0:
                mk[i, RUN] = True                                    # wait
            elif m.broken:
                mk[i, CHANGE] = can_change
                mk[i, RUN] = True                                    # wait (another machine may need the setter)
            else:
                mk[i, RUN] = True
                mk[i, SLOW] = self.cfg.allow_slow
                mk[i, CHANGE] = can_change and m.parts > 0           # never change an unused cutter
        return mk

    def action_masks(self) -> np.ndarray:
        mk = self.machine_masks()
        ok = np.all(mk[np.arange(self.cfg.machines), self.digits], axis=1)
        n_change = (self.digits == CHANGE).sum(axis=1)
        ok &= n_change <= 1                                          # one setter
        return ok

    def encode(self, acts) -> int:
        return int(sum(int(a) * 3 ** i for i, a in enumerate(acts)))

    # ------------------------------------------------------------------ dynamics

    def step(self, action):
        acts = self.digits[int(action)]
        assert self.action_masks()[int(action)], f"masked action {acts}"
        money, led = self.cfg.money, dict(revenue=0.0, tools=0.0, breakage=0.0)
        for i, a in enumerate(acts):
            m = self.machines[i]
            if a == CHANGE:
                d = (money.d_break if m.life.end_type == "break" else money.d_change) if m.broken else money.d_change
                m.busy, self.setter = d, d
                if self.cfg.spares:
                    self.spares -= 1
                led["tools"] -= money.tool_price
                self.stats["changes"] += 1
        for i, a in enumerate(acts):
            m = self.machines[i]
            if m.busy > 0:
                m.busy -= 1
                if m.busy == 0:
                    self._mount(i)
                continue
            if m.broken:
                self.stats["wait_ticks"] += 1
                continue
            self._cut(m, self.cfg.slow_speed if a == SLOW else 1.0, led)
        self.setter = max(0, self.setter - 1)
        self.t += 1
        if self.cfg.spares and self.t % self.cfg.spare_every == 0:
            self.spares = min(self.cfg.spare_cap, self.spares + self.cfg.spare_qty)
        profit = led["revenue"] + led["tools"] + led["breakage"]
        for k, v in led.items():
            self.stats[k] += v
        self.stats["profit"] += profit
        truncated = self.t >= self.cfg.T
        return self._obs(), profit * self.cfg.reward_scale, False, truncated, {"ledger": led, "stats": self.stats}

    def _cut(self, m, s, led):
        self.stats["cut_ticks"] += 1
        self.stats["slow_ticks"] += s < 1
        inc = s ** (1.0 / self.n)                                    # life used per tick (Taylor)
        if m.damage + inc > m.fail_at:                               # the real failure point is reached
            m.damage, m.progress, m.broken = m.fail_at, 0.0, True
            money = self.cfg.money
            led["breakage"] -= money.break_cash if m.life.end_type == "break" else money.part_value
            self.stats["breaks"] += 1
            return
        m.damage += inc
        m.progress += s
        if m.progress >= 1.0 - 1e-9:
            m.progress = max(0.0, m.progress - 1.0)
            m.parts += 1
            led["revenue"] += self.cfg.money.price
            self.stats["parts"] += 1

    # ------------------------------------------------------------------ what the agent sees

    def curve(self, m):
        """(curve, fraction of a cycle used since that curve) for a machine, or (None, 0) if its
        cutter has not finished a normal-speed cycle's worth of life yet."""
        if m.life is None or m.broken or m.busy > 0 or m.damage < 1.0:
            return None, 0.0
        a = int(np.floor(m.damage + 1e-9)) - 1
        return m.life.curve_at(a), m.damage - (a + 1)

    def risk_next(self, m, parts: float, slow: bool) -> float:
        """P(failing within the next `parts` parts) at normal or slow speed, from the curve."""
        h, frac = self.curve(m)
        if h is None:
            return 0.0
        x = frac + parts * (self.rho if slow else 1.0)
        return float(1 - surv_at(h, x) / max(surv_at(h, frac), 1e-12))

    def _obs(self):
        cfg, money = self.cfg, self.cfg.money
        if not self.compute_obs:
            return np.zeros(self.observation_space.shape, np.float32)
        out = []
        for m in self.machines:
            h, _ = self.curve(m)
            v = [1.0 if h is None else 0.0]
            hz = [-1.0] * len(HZ_STEPS) if h is None else \
                [(np.log10(np.clip(h[k - 1], 1e-5, 1.0)) + 2.5) / 2.5 for k in HZ_STEPS]
            v += hz
            v += [self.risk_next(m, 5, False), self.risk_next(m, 20, False)]
            v += [self.risk_next(m, 1, True), self.risk_next(m, 5, True)] if cfg.allow_slow else [0.0, 0.0]
            v += [np.log1p(m.parts) / np.log(200), np.log1p(m.damage) / np.log(200)]
            v += list(m.life.cond) if (cfg.obs_conditions and m.life is not None) else [0.0, 0.0, 0.0]
            v += [float(m.busy == 0 and not m.broken), float(m.busy > 0), float(m.broken), m.busy / money.d_break]
            out += v
        out += [self.setter / money.d_break,
                (self.spares / cfg.spare_cap) if cfg.spares else 1.0,
                ((cfg.spare_every - self.t % cfg.spare_every) / cfg.spare_every) if cfg.spares else 0.0,
                self.rho if cfg.allow_slow else 1.0]
        return np.asarray(out, np.float32)


def single_machine_config(**kw) -> Config:
    """The single-cutter check: one machine, RUN or CHANGE only, unlimited spares. With one machine
    the setter is always free when needed, so this is exactly the stopping problem the DP solves
    (in units of profit per tick)."""
    return replace(Config(machines=1, allow_slow=False, spares=False), **kw)
