# RL run `single_replay_lgbm`

Setup **single**, world **replay**, predictions **lgbm_hazard**, folds ['F1', 'F2', 'F3', 'F4'] (rl4), seeds [0], 2,000,000 steps per agent, 8 envs, gamma 0.995, 20 evaluation episodes of 2000 ticks per fold, pool and n (same seeds for every policy).

Profit is in rupees per 1,000 ticks (one tick = one 1.3-minute cycle), contribution minus cutters and breakage costs. `vs DP` is the % difference from the exact single-cutter DP rule at normal speed (fold-averaged profits, same episodes). `test` = held-out cutters (the result), `train` = training cutters (memorisation check). Rules ending in `_auto` slow down when Taylor's law with the episode's n says it pays.

## pool = test, Taylor n = -

| policy | profit / 1,000 ticks | vs DP | breakages / 1,000 parts | changes per episode | slow share |
|---|---:|---:|---:|---:|---:|
| oracle_normal | 73,587 | +87.6% | 0.00 | 23.4 | 0% |
| dp_normal | 39,233 | +0.0% | 6.60 | 25.5 | 0% |
| dqn | 32,083 | -18.2% | 13.67 | 24.1 | 0% |
| fixed_normal | 29,456 | -24.9% | 10.78 | 22.4 | 0% |
| hazard_normal | 28,784 | -26.6% | 4.98 | 34.1 | 0% |
| ppo | 27,428 | -30.1% | 10.32 | 24.3 | 0% |

## pool = train, Taylor n = -

| policy | profit / 1,000 ticks | vs DP | breakages / 1,000 parts | changes per episode | slow share |
|---|---:|---:|---:|---:|---:|
| oracle_normal | 71,721 | +135.4% | 0.00 | 24.4 | 0% |
| dqn | 56,786 | +86.4% | 3.23 | 23.6 | 0% |
| hazard_normal | 40,031 | +31.4% | 3.71 | 31.6 | 0% |
| fixed_normal | 31,098 | +2.1% | 9.89 | 23.1 | 0% |
| dp_normal | 30,462 | +0.0% | 7.88 | 27.2 | 0% |
| ppo | 26,881 | -11.8% | 10.62 | 18.3 | 0% |
