"""Train RL agents for cutter decisions and compare them with tuned rules on held-out cutters.

Setups (src/toollife/rl/workshop_env.py):
  single   : one machine, RUN or CHANGE, unlimited spares: the single-cutter stopping problem. In
             the 'model' world (failures drawn from the predictor's own curve) the exact DP is the
             optimal policy, so a working agent must come within a few % of it (rl-design.md S1).
  workshop : 3 machines, one setter, RUN / SLOW 20 % / CHANGE, 2 spares every 50 ticks, Taylor n
             drawn per episode in training.
Algorithms: ppo = MaskablePPO (sb3-contrib); dqn = masked Double DQN (src/toollife/rl/dqn.py).

Data and leakage: lives come from --source predictions with the nested --scheme folds (default the
4 rl4 folds of rl-design.md §4.10). Agents and rules are trained/tuned on the fold's training
cutters only, using their inner out-of-fold curves, with time-warp augmentation; they are evaluated
on the fold's held-out cutters with real curves and real failure points, and also on the training
cutters so a memorisation gap is visible.

Comparisons: every policy plays the same --eval-episodes seeds (common random numbers: the same
cutters, failure points and Taylor n for everyone). Rules: fixed count, risk threshold, exact
single-cutter DP (g by Dinkelbach), perfect-knowledge reference; in the workshop each rule is run at
normal speed and with the Taylor "slow if it pays" switch (src/toollife/rl/baselines.py).

Outputs in results/rl/<name>/: episodes.csv (one row per policy × fold × seed × pool × n × episode),
summary.csv, summary.md, config.json. Trained agents go to data/rl_models/<name>/ (gitignored).

Defaults that passed the single-machine check: PPO entropy 0.01, gamma 0.995, 2M steps, 8 envs
(gamma 0.999 had not learned by 2M steps; 300k steps were far too few). DQN uses reward centering
and one gradient step per 4 env steps; one gradient step per 16 env steps left it far from the DP.

Examples (10-core Mac; times measured with other jobs running):
  single-machine check vs DP, one fold, ~15-20 min:
      python scripts/08_train_rl.py --setup single --world model --source weibull_settings_age --folds F1 --jobs 2
  single machine on real failures, 4 folds, PPO + DQN, ~30 min (with other jobs running):
      python scripts/08_train_rl.py --setup single --world replay --source lgbm_hazard --dqn-timesteps 1000000 --jobs 8
  workshop, 4 folds, PPO + DQN, one seed (12 tasks on 10 processes), ~30 min on a quiet Mac
  (measured: workshop PPO ~1,900 and DQN ~1,150 training steps/s per process):
      python scripts/08_train_rl.py --setup workshop --world replay --source lgbm_hazard \
          --dqn-timesteps 1000000 --jobs 10
"""

import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.policy.lives import RL4_FOLDS, dataset_lives, fold_lives
from toollife.rl.baselines import RulePolicy, dp_g, run_episode, tune
from toollife.rl.workshop_env import Config, Money, WorkshopEnv, single_machine_config

ROOT = Path(__file__).resolve().parents[1]


def parse():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--setup", choices=["single", "workshop"], default="single")
    ap.add_argument("--algos", nargs="+", default=["ppo", "dqn"], choices=["ppo", "dqn"])
    ap.add_argument("--world", choices=["replay", "model"], default="replay")
    ap.add_argument("--source", default="lgbm_hazard", help="results/predictions/<source>.parquet")
    ap.add_argument("--scheme", choices=["rl4", "loco"], default="rl4")
    ap.add_argument("--folds", nargs="+", default=None, help="default: every fold of the scheme")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0])
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--timesteps", type=int, default=2_000_000)
    ap.add_argument("--jobs", type=int, default=1, help="parallel processes over (fold, algo, seed)")
    ap.add_argument("--gamma", type=float, default=0.995)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--ent-coef", type=float, default=0.01, help="PPO entropy bonus")
    ap.add_argument("--dqn-timesteps", type=int, default=None, help="DQN steps (default: --timesteps)")
    ap.add_argument("--dqn-train-freq", type=int, default=4, help="env steps per DQN gradient step")
    ap.add_argument("--eval-episodes", type=int, default=20)
    ap.add_argument("--tune-episodes", type=int, default=4)
    ap.add_argument("--T", type=int, default=2000, help="ticks per episode")
    ap.add_argument("--train-n", nargs=2, type=float, default=[0.2, 0.5], help="Taylor n range in training")
    ap.add_argument("--eval-n", nargs="+", type=float, default=[0.25, 0.4, 1.0], help="Taylor n values for evaluation")
    ap.add_argument("--no-augment", action="store_true")
    # money (rupees) and workshop settings
    ap.add_argument("--price", type=float, default=Money.price)
    ap.add_argument("--tool-price", type=float, default=Money.tool_price)
    ap.add_argument("--kappa", type=float, default=None, help="breakage event ÷ planned change event")
    ap.add_argument("--spare-qty", type=int, default=Config.spare_qty)
    ap.add_argument("--spare-every", type=int, default=Config.spare_every)
    ap.add_argument("--extra-train", nargs="*", default=[], metavar="MODEL:DATASET",
                    help="add another dataset's lives to the TRAINING pool only (policy.lives.dataset_lives)")
    ap.add_argument("--name", default=None)
    ap.add_argument("--resummarise", action="store_true", help="rebuild summary.csv/md of --name from episodes.csv")
    return ap.parse_args()


def configs(args):
    money = Money(price=args.price, tool_price=args.tool_price, kappa=args.kappa)
    base = dict(world=args.world, T=args.T, money=money)
    if args.setup == "single":
        train = single_machine_config(**base, augment=not args.no_augment)
        evals = {"-": replace(train, augment=False)}
    else:
        train = Config(**base, augment=not args.no_augment, taylor_n=tuple(args.train_n),
                       spare_qty=args.spare_qty, spare_every=args.spare_every)
        evals = {f"{n:g}": replace(train, augment=False, taylor_n=(n, n)) for n in args.eval_n}
    return train, evals


def evaluate(act, pools, evals, args, need_obs=True):
    """Same seeds 1..E for every policy (common random numbers)."""
    rows = []
    for pool_name, lives in pools.items():
        for n_name, cfg in evals.items():
            env = WorkshopEnv(lives, cfg)
            for ep in range(1, args.eval_episodes + 1):
                s = run_episode(env, act, seed=ep, need_obs=need_obs)
                rows.append(dict(pool=pool_name, eval_n=n_name, episode=ep) | s)
    return rows


# ------------------------------------------------------------------------------------------------
# Tasks (run in separate processes)


def lives_for(args, fold):
    """Training and held-out lives of one fold, plus any extra training lives from other datasets."""
    train_lives, test_lives = fold_lives(args.source, fold, args.scheme)
    for spec in args.extra_train:
        model, dataset = spec.split(":")
        train_lives = train_lives + dataset_lives(model, dataset)
    return train_lives, test_lives


def rules_task(args, fold):
    train_lives, test_lives = lives_for(args, fold)
    train_cfg, evals = configs(args)
    tune_cfg = replace(train_cfg, augment=False, T=min(args.T, 1000))
    make = lambda: WorkshopEnv(train_lives, tune_cfg)
    mean_life = float(np.mean([l.L for l in train_lives]))
    seeds = range(10_001, 10_001 + args.tune_episodes)
    g = dp_g(train_lives, train_cfg.money.econ(), args.world)
    speeds = ["normal"] if args.setup == "single" else ["normal", "auto"]
    policies = [RulePolicy("oracle", None, sp, mean_life) for sp in speeds]
    for sp in speeds:
        policies.append(tune(make, "fixed", list(range(10, 151, 10)), sp, mean_life, seeds))
        policies.append(tune(make, "hazard", list(np.logspace(-3, -0.3, 12)), sp, mean_life, seeds))
        policies.append(RulePolicy("dp", g, sp, mean_life))
    pools = {"test": test_lives, "train": train_lives}
    rows = []
    for pol in policies:
        for r in evaluate(lambda e, o, p=pol: p.act(e), pools, evals, args, need_obs=False):
            rows.append(dict(policy=pol.name, kind="rule", param=pol.param, fold=fold, seed=-1) | r)
    return rows


def rl_task(args, fold, algo, seed, model_dir):
    import torch

    torch.set_num_threads(1)
    train_lives, test_lives = lives_for(args, fold)
    train_cfg, evals = configs(args)
    t0 = time.time()
    if algo == "ppo":
        from sb3_contrib import MaskablePPO
        from stable_baselines3.common.env_util import make_vec_env

        venv = make_vec_env(lambda: WorkshopEnv(train_lives, train_cfg), n_envs=args.n_envs, seed=seed)
        model = MaskablePPO(
            "MlpPolicy", venv, n_steps=512, batch_size=1024, n_epochs=10, learning_rate=args.lr,
            gamma=args.gamma, gae_lambda=0.95, clip_range=0.2, ent_coef=args.ent_coef, vf_coef=0.5, max_grad_norm=0.5,
            policy_kwargs=dict(net_arch=dict(pi=[256, 256], vf=[256, 256]), activation_fn=torch.nn.Tanh),
            seed=seed, device="cpu", verbose=0)
        model.learn(total_timesteps=args.timesteps)
        model.save(model_dir / f"ppo_{fold}_s{seed}")
        act = lambda e, o: int(model.predict(o, action_masks=e.action_masks(), deterministic=True)[0])
    else:
        from toollife.rl.dqn import MaskedDQN

        envs = [WorkshopEnv(train_lives, train_cfg) for _ in range(args.n_envs)]
        steps = args.dqn_timesteps or args.timesteps
        model = MaskedDQN(envs, lr=1e-4, gamma=args.gamma, seed=seed, train_freq=args.dqn_train_freq,
                          learning_starts=min(10_000, steps // 10)).learn(steps, log=lambda s: None)
        model.save(model_dir / f"dqn_{fold}_s{seed}.pt")
        act = lambda e, o: model.predict(o, e.action_masks())
    train_s = time.time() - t0
    rows = evaluate(act, {"test": test_lives, "train": train_lives}, evals, args)
    return [dict(policy=algo, kind="rl", param=np.nan, fold=fold, seed=seed, train_seconds=train_s) | r for r in rows]


# ------------------------------------------------------------------------------------------------
# Summary


def summarise(ep: pd.DataFrame, args) -> pd.DataFrame:
    """Mean over folds, seeds and episodes; each fold weighted equally."""
    keys = ["policy", "kind", "pool", "eval_n"]
    per_fold = ep.groupby(keys + ["fold"]).agg(
        profit_per_1000_ticks=("profit_per_1000_ticks", "mean"), breaks_per_1000_parts=("breaks_per_1000_parts", "mean"),
        slow_share=("slow_share", "mean"), changes=("changes", "mean"), parts=("parts", "mean")).reset_index()
    out = per_fold.groupby(keys).mean(numeric_only=True).reset_index()
    # % difference from the DP rule at normal speed: ratio of fold-averaged profits (same folds,
    # pools, n and episodes for both, so the comparison is paired).
    dp = out[out["policy"] == "dp_normal"].set_index(["pool", "eval_n"])["profit_per_1000_ticks"]
    ref = dp.reindex(list(zip(out["pool"], out["eval_n"]))).to_numpy()
    out["vs_dp_normal_pct"] = 100 * (out["profit_per_1000_ticks"].to_numpy() / ref - 1)
    return out.sort_values(["pool", "eval_n", "profit_per_1000_ticks"], ascending=[True, True, False])


def write_md(summary: pd.DataFrame, args, out_dir: Path, seconds: float):
    L = [f"# RL run `{out_dir.name}`\n",
         f"Setup **{args.setup}**, world **{args.world}**, predictions **{args.source}**, folds {args.folds} "
         f"({args.scheme}), seeds {args.seeds}, {args.timesteps:,} steps per agent, {args.n_envs} envs, "
         f"gamma {args.gamma}, {args.eval_episodes} evaluation episodes of {args.T} ticks per fold, pool and n "
         f"(same seeds for every policy)." + (f" Wall time {seconds / 60:.1f} min." if seconds else "") + "\n",
         "Profit is in rupees per 1,000 ticks (one tick = one 1.3-minute cycle), contribution minus cutters "
         "and breakage costs. `vs DP` is the % difference from the exact single-cutter DP rule at normal "
         "speed (fold-averaged profits, same episodes). `test` = held-out cutters (the result), `train` = training cutters (memorisation check). "
         "Rules ending in `_auto` slow down when Taylor's law with the episode's n says it pays.\n"]
    for (pool, n), g in summary.groupby(["pool", "eval_n"], sort=False):
        L.append(f"## pool = {pool}, Taylor n = {n}\n")
        L.append("| policy | profit / 1,000 ticks | vs DP | breakages / 1,000 parts | changes per episode | slow share |")
        L.append("|---|---:|---:|---:|---:|---:|")
        for r in g.itertuples():
            L.append(f"| {r.policy} | {r.profit_per_1000_ticks:,.0f} | {r.vs_dp_normal_pct:+.1f}% | "
                     f"{r.breaks_per_1000_parts:.2f} | {r.changes:.1f} | {100 * r.slow_share:.0f}% |")
        L.append("")
    (out_dir / "summary.md").write_text("\n".join(L))


if __name__ == "__main__":
    args = parse()
    args.folds = args.folds or (list(RL4_FOLDS) if args.scheme == "rl4" else
                                [str(t) for t in (2, 3, 4, 5, 6, 7, 8, 9, 10, 101, 102, 103, 105)])
    name = args.name or f"{args.setup}_{args.world}_{args.source}"
    out_dir = ROOT / "results" / "rl" / name
    if args.resummarise:
        saved = json.loads((out_dir / "config.json").read_text())
        for k in ("setup", "world", "source", "folds", "scheme", "seeds", "timesteps", "n_envs", "gamma",
                  "eval_episodes", "T"):
            setattr(args, k, saved[k])
        ep = pd.read_csv(out_dir / "episodes.csv", dtype={"fold": str, "eval_n": str})
        summary = summarise(ep, args)
        summary.round(4).to_csv(out_dir / "summary.csv", index=False)
        write_md(summary, args, out_dir, None)
        print(summary[["policy", "pool", "eval_n", "profit_per_1000_ticks", "vs_dp_normal_pct"]].round(1).to_string(index=False))
        sys.exit(0)
    model_dir = ROOT / "data" / "rl_models" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "config.json").write_text(json.dumps(vars(args) | {"config": str(configs(args)[0])}, indent=1, default=str))
    t0 = time.time()
    tasks = [delayed(rules_task)(args, f) for f in args.folds]
    tasks += [delayed(rl_task)(args, f, a, s, model_dir) for f in args.folds for a in args.algos for s in args.seeds]
    print(f"{len(tasks)} tasks on {args.jobs} processes")
    results = Parallel(n_jobs=args.jobs, verbose=5)(tasks)
    ep = pd.DataFrame([r for rows in results for r in rows])
    ep.to_csv(out_dir / "episodes.csv", index=False)
    summary = summarise(ep, args)
    summary.round(4).to_csv(out_dir / "summary.csv", index=False)
    write_md(summary, args, out_dir, time.time() - t0)
    cols = ["policy", "pool", "eval_n", "profit_per_1000_ticks", "vs_dp_normal_pct", "breaks_per_1000_parts", "slow_share"]
    print(summary[cols].round(2).to_string(index=False))
    print(f"wrote {out_dir}  ({(time.time() - t0) / 60:.1f} min)")
