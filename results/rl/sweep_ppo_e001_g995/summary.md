# RL run `sweep_ppo_e001_g995`

Setup **single**, world **model**, predictions **weibull_settings_age**, folds ['F1'] (rl4), seeds [0], 2,000,000 steps per agent, 8 envs, gamma 0.995, 20 evaluation episodes of 2000 ticks per fold, pool and n (same seeds for every policy).

Profit is in rupees per 1,000 ticks (one tick = one 1.3-minute cycle), contribution minus cutters and breakage costs. `vs DP` is the % difference from the exact single-cutter DP rule at normal speed (fold-averaged profits, same episodes). `test` = held-out cutters (the result), `train` = training cutters (memorisation check). Rules ending in `_auto` slow down when Taylor's law with the episode's n says it pays.

## pool = test, Taylor n = -

| policy | profit / 1,000 ticks | vs DP | breakages / 1,000 parts | changes per episode | slow share |
|---|---:|---:|---:|---:|---:|
| oracle_normal | 93,177 | +20.8% | 0.00 | 13.6 | 0% |
| dp_normal | 77,165 | +0.0% | 2.63 | 14.3 | 0% |
| hazard_normal | 76,104 | -1.4% | 2.39 | 15.5 | 0% |
| ppo | 75,609 | -2.0% | 3.12 | 13.8 | 0% |
| fixed_normal | 50,588 | -34.4% | 4.03 | 24.8 | 0% |

## pool = train, Taylor n = -

| policy | profit / 1,000 ticks | vs DP | breakages / 1,000 parts | changes per episode | slow share |
|---|---:|---:|---:|---:|---:|
| oracle_normal | 76,284 | +26.9% | 0.00 | 22.1 | 0% |
| dp_normal | 60,092 | +0.0% | 1.50 | 26.2 | 0% |
| ppo | 59,572 | -0.9% | 2.20 | 24.6 | 0% |
| hazard_normal | 56,997 | -5.2% | 0.56 | 30.4 | 0% |
| fixed_normal | 35,475 | -41.0% | 7.55 | 25.1 | 0% |
