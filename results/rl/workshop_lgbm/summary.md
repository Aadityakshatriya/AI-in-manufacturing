# RL run `workshop_lgbm`

Setup **workshop**, world **replay**, predictions **lgbm_hazard**, folds ['F1', 'F2', 'F3', 'F4'] (rl4), seeds [0], 2,000,000 steps per agent, 8 envs, gamma 0.995, 20 evaluation episodes of 2000 ticks per fold, pool and n (same seeds for every policy). Wall time 23.9 min.

Profit is in rupees per 1,000 ticks (one tick = one 1.3-minute cycle), contribution minus cutters and breakage costs. `vs DP` is the % difference from the exact single-cutter DP rule at normal speed (fold-averaged profits, same episodes). `test` = held-out cutters (the result), `train` = training cutters (memorisation check). Rules ending in `_auto` slow down when Taylor's law with the episode's n says it pays.

## pool = test, Taylor n = 0.25

| policy | profit / 1,000 ticks | vs DP | breakages / 1,000 parts | changes per episode | slow share |
|---|---:|---:|---:|---:|---:|
| oracle_auto | 221,728 | +127.4% | 0.46 | 31.4 | 100% |
| hazard_auto | 177,746 | +82.3% | 2.68 | 40.4 | 100% |
| oracle_normal | 174,530 | +79.0% | 3.30 | 63.4 | 0% |
| dp_auto | 173,333 | +77.8% | 3.84 | 35.5 | 100% |
| fixed_auto | 156,658 | +60.7% | 4.23 | 42.5 | 100% |
| dqn | 106,689 | +9.4% | 4.20 | 54.7 | 63% |
| ppo | 103,482 | +6.1% | 3.30 | 81.0 | 64% |
| dp_normal | 97,513 | +0.0% | 9.05 | 62.5 | 0% |
| hazard_normal | 91,822 | -5.8% | 8.39 | 68.8 | 0% |
| fixed_normal | 77,746 | -20.3% | 12.35 | 52.0 | 0% |

## pool = test, Taylor n = 0.4

| policy | profit / 1,000 ticks | vs DP | breakages / 1,000 parts | changes per episode | slow share |
|---|---:|---:|---:|---:|---:|
| oracle_auto | 174,530 | +79.0% | 3.30 | 63.4 | 0% |
| oracle_normal | 174,530 | +79.0% | 3.30 | 63.4 | 0% |
| dp_auto | 97,513 | +0.0% | 9.05 | 62.5 | 0% |
| dp_normal | 97,513 | +0.0% | 9.05 | 62.5 | 0% |
| hazard_normal | 91,822 | -5.8% | 8.39 | 68.8 | 0% |
| hazard_auto | 90,268 | -7.4% | 8.81 | 66.5 | 0% |
| ppo | 88,737 | -9.0% | 4.42 | 80.9 | 62% |
| dqn | 86,849 | -10.9% | 4.81 | 63.8 | 63% |
| fixed_normal | 77,746 | -20.3% | 12.35 | 52.0 | 0% |
| fixed_auto | 75,148 | -22.9% | 12.59 | 52.5 | 0% |

## pool = test, Taylor n = 1

| policy | profit / 1,000 ticks | vs DP | breakages / 1,000 parts | changes per episode | slow share |
|---|---:|---:|---:|---:|---:|
| oracle_auto | 174,530 | +79.0% | 3.30 | 63.4 | 0% |
| oracle_normal | 174,530 | +79.0% | 3.30 | 63.4 | 0% |
| dp_auto | 97,513 | +0.0% | 9.05 | 62.5 | 0% |
| dp_normal | 97,513 | +0.0% | 9.05 | 62.5 | 0% |
| hazard_normal | 91,822 | -5.8% | 8.39 | 68.8 | 0% |
| hazard_auto | 90,268 | -7.4% | 8.81 | 66.5 | 0% |
| fixed_normal | 77,746 | -20.3% | 12.35 | 52.0 | 0% |
| fixed_auto | 75,148 | -22.9% | 12.59 | 52.5 | 0% |
| ppo | 70,013 | -28.2% | 5.92 | 80.9 | 60% |
| dqn | 57,699 | -40.8% | 6.79 | 68.6 | 64% |

## pool = train, Taylor n = 0.25

| policy | profit / 1,000 ticks | vs DP | breakages / 1,000 parts | changes per episode | slow share |
|---|---:|---:|---:|---:|---:|
| oracle_auto | 219,929 | +173.1% | 0.63 | 31.1 | 100% |
| hazard_auto | 167,271 | +107.7% | 3.81 | 38.6 | 100% |
| dp_auto | 164,661 | +104.5% | 4.41 | 36.0 | 100% |
| oracle_normal | 158,694 | +97.1% | 4.34 | 61.9 | 0% |
| dqn | 157,784 | +95.9% | 4.95 | 46.9 | 55% |
| fixed_auto | 154,759 | +92.2% | 4.12 | 43.7 | 100% |
| ppo | 121,442 | +50.8% | 2.35 | 80.6 | 61% |
| hazard_normal | 91,941 | +14.2% | 7.46 | 75.0 | 0% |
| fixed_normal | 86,721 | +7.7% | 10.97 | 55.0 | 0% |
| dp_normal | 80,527 | +0.0% | 10.10 | 63.6 | 0% |

## pool = train, Taylor n = 0.4

| policy | profit / 1,000 ticks | vs DP | breakages / 1,000 parts | changes per episode | slow share |
|---|---:|---:|---:|---:|---:|
| oracle_auto | 158,694 | +97.1% | 4.34 | 61.9 | 0% |
| oracle_normal | 158,694 | +97.1% | 4.34 | 61.9 | 0% |
| dqn | 154,216 | +91.5% | 3.35 | 62.6 | 47% |
| ppo | 102,785 | +27.6% | 3.63 | 80.6 | 59% |
| hazard_normal | 91,941 | +14.2% | 7.46 | 75.0 | 0% |
| hazard_auto | 88,911 | +10.4% | 9.00 | 66.5 | 0% |
| fixed_normal | 86,721 | +7.7% | 10.97 | 55.0 | 0% |
| fixed_auto | 80,592 | +0.1% | 11.70 | 53.8 | 0% |
| dp_auto | 80,527 | +0.0% | 10.10 | 63.6 | 0% |
| dp_normal | 80,527 | +0.0% | 10.10 | 63.6 | 0% |

## pool = train, Taylor n = 1

| policy | profit / 1,000 ticks | vs DP | breakages / 1,000 parts | changes per episode | slow share |
|---|---:|---:|---:|---:|---:|
| oracle_auto | 158,694 | +97.1% | 4.34 | 61.9 | 0% |
| oracle_normal | 158,694 | +97.1% | 4.34 | 61.9 | 0% |
| dqn | 121,500 | +50.9% | 3.36 | 79.5 | 39% |
| hazard_normal | 91,941 | +14.2% | 7.46 | 75.0 | 0% |
| hazard_auto | 88,911 | +10.4% | 9.00 | 66.5 | 0% |
| fixed_normal | 86,721 | +7.7% | 10.97 | 55.0 | 0% |
| fixed_auto | 80,592 | +0.1% | 11.70 | 53.8 | 0% |
| dp_auto | 80,527 | +0.0% | 10.10 | 63.6 | 0% |
| dp_normal | 80,527 | +0.0% | 10.10 | 63.6 | 0% |
| ppo | 72,313 | -10.2% | 5.97 | 80.2 | 55% |
