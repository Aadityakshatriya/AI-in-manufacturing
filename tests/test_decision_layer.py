"""Checks for the decision layer and the workshop environment (rl-design.md §4.14).

Run: .venv/bin/python tests/test_decision_layer.py   (or pytest tests/)
Needs results/predictions from scripts/06_hazard_yardsticks.py.
"""

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.policy.costs import INDIA, grid
from toollife.policy.curves import survival
from toollife.policy.dp import dp_flags, keep_change_values
from toollife.policy.lives import RL4_FOLDS, fold_lives, rzeszow_truth
from toollife.rl.workshop_env import CHANGE, RUN, SLOW, Config, WorkshopEnv, single_machine_config

SOURCE = "lgbm_hazard"
TRAIN, TEST = fold_lives(SOURCE, "F1", "rl4")


def test_no_leakage_any_fold():
    truth = rzeszow_truth()
    for f, tools in RL4_FOLDS.items():
        tr, te = fold_lives(SOURCE, f, "rl4", truth)
        assert {l.tool for l in te} == {str(t) for t in tools} and not {l.tool for l in tr} & {l.tool for l in te}
    for t in truth["tool"]:
        tr, te = fold_lives(SOURCE, t, "loco", truth)
        assert [l.tool for l in te] == [t] and len(tr) == 12


def test_dp_equals_brute_force():
    rng = np.random.default_rng(0)
    econ = INDIA.econ()
    for _ in range(100):
        K = int(rng.integers(1, 30))
        h = rng.uniform(0, 0.3, K) * (rng.random(K) < 0.7)
        g = rng.uniform(20, 200)
        keep, _ = keep_change_values(h[None], econ, g)
        S = survival(h)
        plans = []
        for j in range(1, K + 1):
            v = sum(S[i - 1] * h[i - 1] * econ.a_break + S[i] * (econ.a_survive - g) for i in range(1, j + 1))
            plans.append(v + S[j] * econ.a_change)
        assert abs(min(plans) - keep[0]) < 1e-6 * max(1, abs(min(plans)))


def test_one_step_threshold_matches_costs_formula():
    for c in grid():
        g = 90.0
        thr = c.one_step_threshold(g)
        f = dp_flags(np.array([[thr * 0.999], [thr * 1.001]]), c.econ(), g, horizon=1)
        assert not f[0] and f[1]


def _run_until_break(env, action):
    env.reset(seed=1)
    m = env.machines[0]
    while not m.broken:
        env.step(env.encode([action]))
    return m


def test_replay_fidelity():
    """Normal speed, no changes: every cutter makes exactly L good parts and breaks on part L + 1."""
    for life in TRAIN + TEST:
        env = WorkshopEnv([life], single_machine_config(random_start=False))
        m = _run_until_break(env, RUN)
        assert m.parts == life.L, (life.tool, m.parts, life.L)


def test_taylor_slow_down_and_damage_clock():
    life = TEST[0]
    cfg = replace(single_machine_config(random_start=False), allow_slow=True)
    for n, expect in [(1.0, "same"), (2.0, "fewer"), (0.25, "more")]:
        env = WorkshopEnv([life], replace(cfg, taylor_n=(n, n)))
        m = _run_until_break(env, SLOW)
        assert abs(m.damage - m.fail_at) < 1e-12
        if expect == "same":
            assert m.parts == life.L
        elif expect == "fewer":
            assert m.parts < life.L
        else:
            assert m.parts > life.L
    # Alternating speeds cannot skip the failure point and never cuts past it.
    env = WorkshopEnv([life], replace(cfg, taylor_n=(0.3, 0.3)))
    env.reset(seed=3)
    m, k = env.machines[0], 0
    while not m.broken:
        env.step(env.encode([RUN if k % 2 else SLOW]))
        assert m.damage <= m.fail_at + 1e-12
        k += 1


def test_masks_and_accounting_under_random_play():
    env = WorkshopEnv(TRAIN, Config())
    rng = np.random.default_rng(0)
    money = env.cfg.money
    for ep in range(3):
        env.reset(seed=ep)
        total = 0.0
        done = False
        while not done:
            mask = env.action_masks()
            assert mask.any()
            a = int(rng.choice(np.flatnonzero(mask)))
            acts = env.digits[a]
            assert (acts == CHANGE).sum() <= 1
            if (acts == CHANGE).any():
                assert env.spares > 0 and env.setter == 0
            _, r, _, trunc, _ = env.step(a)
            assert env.spares >= 0
            total += r / env.cfg.reward_scale
            done = trunc
        s = env.stats
        assert abs(total - s["profit"]) < 1e-6
        assert abs(s["revenue"] - s["parts"] * money.price) < 1e-6
        assert abs(s["tools"] + s["changes"] * money.tool_price) < 1e-6
        assert abs(s["breakage"] + s["breaks"] * money.break_cash) < 1e-6


def test_determinism_and_common_random_numbers():
    env = WorkshopEnv(TRAIN, Config(augment=True))
    rng = np.random.default_rng(5)
    acts = []
    env.reset(seed=11)
    out1 = []
    for _ in range(500):
        a = int(rng.choice(np.flatnonzero(env.action_masks())))
        acts.append(a)
        out1.append(env.step(a)[0])
    env.reset(seed=11)
    out2 = [env.step(a)[0] for a in acts]
    assert all(np.array_equal(x, y) for x, y in zip(out1, out2))
    # Same seed → same first cutters and Taylor n, whatever the policy does later.
    e1, e2 = WorkshopEnv(TRAIN, Config()), WorkshopEnv(TRAIN, Config())
    e1.reset(seed=4)
    e2.reset(seed=4)
    assert e1.n == e2.n and [m.life.key for m in e1.machines] == [m.life.key for m in e2.machines]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
