"""Keep-or-change decisions replayed on the 13 real cutters, each judged by models that never saw it.

For each held-out cutter (leave-one-cutter-out) and each prediction source, every policy is tuned
on the other 12 cutters' inner out-of-fold curves (so neither the predictor nor the tuning saw the
held-out cutter), then replays the held-out cutter cycle by cycle. The real failure cycle is known,
so the outcome is exact; only the costs are assumed (rl-design.md §7.3, claim level 1).

Policies (src/toollife/policy): never, fixed, fixed_group, rul_q10, hazard, one_step, dp, dp_tuned,
and the perfect-knowledge oracle (change right after the last good cycle) for measuring regret.
Prediction sources: results/predictions/<model>.parquet (default: the two yardsticks of step 06).
Cost settings: 10 named real-money scenarios + the 14-cell grid of costs.md §1.4.

Scores pool the 13 cutters as total cost ÷ total good cycles (what a shop pays per good cycle over
many cutters). Confidence intervals resample the 13 cutters (paired between policies), because
13 cutters is the real sample size.

Outputs in results/decisions/:
  single_cutter.csv            one row per source × cost setting × policy
  single_cutter_per_cutter.csv one row per source × cost setting × policy × held-out cutter
  single_cutter.md             summary tables
  single_cutter.png            figure

Usage: python scripts/07_single_cutter_decisions.py [--models weibull_settings_age lgbm_hazard]
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from toollife.policy.costs import NAMED, all_settings
from toollife.policy.dp import oracle_outcome
from toollife.policy.lives import PRED_DIR, fold_lives, rzeszow_truth
from toollife.policy.replay import replay, summarise
from toollife.policy.rules import make_policies

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "decisions"
RULES = ["fixed", "fixed_group", "rul_q10", "hazard", "one_step"]
ORDER = ["never", *RULES, "dp", "dp_tuned", "oracle"]
LABEL = {"never": "run to failure", "fixed": "fixed interval", "fixed_group": "fixed interval per width",
         "rul_q10": "cautious remaining life (q10)", "hazard": "risk threshold", "one_step": "one-step cost rule",
         "dp": "exact DP (g from costs)", "dp_tuned": "exact DP (g tuned)", "oracle": "perfect knowledge"}
N_BOOT = 10_000
SOURCE_LABEL = {"weibull_settings_age": "Weibull on settings + age", "lgbm_hazard": "LightGBM hazard on sensors",
                "history_physics": "history model, physics", "history_settings_age": "history model, settings + age"}


def run(models):
    truth = rzeszow_truth()
    settings = all_settings()
    rows = []
    for model in models:
        for fold in truth["tool"]:
            train, test = fold_lives(model, fold, truth=truth)
            assert len(test) == 1 and len(train) == 12
            life = test[0]
            for costs in settings:
                econ = costs.econ()
                outs = []
                for pol in make_policies():
                    pol.fit(train, econ)
                    outs.append((pol.name, replay(life, pol.flags(life), econ), pol.params))
                outs.append(("oracle", oracle_outcome(life, econ), {}))
                for name, o, params in outs:
                    rows.append(dict(source=model, cost=costs.name, currency=costs.currency, r=costs.r,
                                     k=costs.k, policy=name, tool=o.tool, L=o.L, good=o.good, broke=o.broke,
                                     cost_total=o.A, good_total=o.B, wasted=o.wasted, life_used=o.life_used,
                                     params=";".join(f"{k}={v:.6g}" for k, v in params.items())))
        print(f"{model}: done")
    return pd.DataFrame(rows)


def aggregate(per: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    idx = rng.integers(0, 13, size=(N_BOOT, 13))
    out = []
    for (src, cost), g in per.groupby(["source", "cost"], sort=False):
        piv_A = g.pivot(index="tool", columns="policy", values="cost_total")
        piv_B = g.pivot(index="tool", columns="policy", values="good_total")
        boot = {p: piv_A[p].to_numpy()[idx].sum(1) / piv_B[p].to_numpy()[idx].sum(1) for p in piv_A}
        for pol, gp in g.groupby("policy"):
            s = summarise([_O(r) for r in gp.itertuples()])
            fixed, oracle = piv_A["fixed"].sum() / piv_B["fixed"].sum(), piv_A["oracle"].sum() / piv_B["oracle"].sum()
            saving = 100 * (1 - boot[pol] / boot["fixed"])
            out.append(dict(source=src, cost=cost, currency=gp["currency"].iloc[0], r=gp["r"].iloc[0],
                            k=gp["k"].iloc[0], policy=pol) | s | dict(
                saving_vs_fixed_pct=100 * (1 - s["cost_per_good"] / fixed),
                saving_ci_lo=np.percentile(saving, 2.5), saving_ci_hi=np.percentile(saving, 97.5),
                p_better_than_fixed=float((boot[pol] < boot["fixed"]).mean()),
                regret_vs_oracle_pct=100 * (s["cost_per_good"] / oracle - 1)))
    agg = pd.DataFrame(out)
    agg["policy"] = pd.Categorical(agg["policy"], ORDER, ordered=True)
    return agg.sort_values(["source", "cost", "policy"]).reset_index(drop=True)


class _O:
    """Outcome-like view of a per-cutter row, for replay.summarise."""

    def __init__(self, r):
        self.A, self.B, self.broke, self.good, self.L = r.cost_total, r.good_total, r.broke, r.good, r.L
        self.wasted, self.life_used = r.wasted, r.life_used


# ------------------------------------------------------------------------------------------------
# Report



def write_markdown(agg: pd.DataFrame, per: pd.DataFrame, models):
    L = []
    L.append("# Single-cutter keep-or-change decisions on 13 real held-out cutters\n")
    L.append("Generated by `scripts/07_single_cutter_decisions.py`. Each of the 13 usable Rzeszów cutters is held "
             "out in turn. Every policy is tuned on the other 12 cutters (using failure curves from models that "
             "saw neither that training cutter nor the held-out one), then replays the held-out cutter cycle by "
             "cycle. The real failure cycle is known, so outcomes are exact; **only the costs are assumed** "
             "(`research/next-phase/costs.md`). Scores pool the 13 cutters: total cost ÷ total good cycles. "
             "Brackets are 95% intervals from resampling the 13 cutters (paired with the fixed interval).\n")
    L.append("Prediction sources: " + ", ".join(f"`{m}`" for m in models) + ". `weibull_settings_age` and "
             "`lgbm_hazard` are the yardsticks of step 06 (`results/predictions/summary.csv` has their accuracy).\n")
    flat = [m for m in models if not (PRED_DIR / "nested" / f"{m}.parquet").exists()]
    if flat:
        L.append("**Note:** " + ", ".join(f"`{m}`" for m in flat) + " have no nested inner-fold predictions, so for "
                 "those sources the policies were tuned on the training cutters' own leave-one-out curves. Those "
                 "curves came from models that had seen the held-out cutter: a mild second-order leak "
                 "(rl-design.md §4.10 fallback). The held-out cutter's own curve is still clean. The prediction "
                 "files are snapshots taken while that model was still being developed.\n")
    L.append("Policies: " + "; ".join(f"**{p}** = {LABEL[p]}" for p in ORDER) + ".\n")

    ind = agg[agg["cost"] == "india_typical"]
    c = NAMED["india_typical"]
    L.append(f"## India typical costs (planned change ₹{c.C_p:,.0f}, breakage ₹{c.C_f:,.0f}, ratio {c.r:.2f}, "
             f"₹{c.c_m:.1f} per cycle)\n")
    for src in models:
        s = ind[ind["source"] == src]
        L.append(f"**{src}**\n")
        L.append("| policy | ₹ per good cycle | saving vs fixed interval | breakages (of 13) | life used | "
                 "wasted cycles per cutter | above perfect knowledge |")
        L.append("|---|---:|---:|---:|---:|---:|---:|")
        for r in s.itertuples():
            L.append(f"| {r.policy} | {r.cost_per_good:,.1f} | {r.saving_vs_fixed_pct:+.1f}% "
                     f"[{r.saving_ci_lo:+.1f}, {r.saving_ci_hi:+.1f}] | {r.breakages} | {100 * r.life_used:.0f}% | "
                     f"{r.wasted_cycles:.1f} | {r.regret_vs_oracle_pct:+.0f}% |")
        L.append("")

    L.append("## Across cost settings\n")
    L.append("Saving vs the tuned fixed interval (positive = cheaper per good cycle). \"Best rule\" is the best of "
             f"{', '.join(RULES[1:])} **chosen after seeing the held-out results**, so it is optimistic. "
             "Grid cells hold the planned change at ₹3,133; r = breakage ÷ planned change, "
             "k = machining cost per cycle ÷ planned change.\n")
    for src in models:
        s = agg[agg["source"] == src]
        L.append(f"**{src}**\n")
        L.append("| setting | r | k | exact DP | DP breakages | DP, g tuned | breakages | best rule (which) | "
                 "one-step rule | perfect knowledge |")
        L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for cost, g in s.groupby("cost", sort=False):
            g = g.set_index("policy")
            rules = g.loc[RULES[1:]]
            best = rules["saving_vs_fixed_pct"].idxmax()
            L.append(f"| {cost} | {g['r'].iloc[0]:.2f} | {g['k'].iloc[0]:.4f} | "
                     f"{g.loc['dp', 'saving_vs_fixed_pct']:+.1f}% | {g.loc['dp', 'breakages']} | "
                     f"{g.loc['dp_tuned', 'saving_vs_fixed_pct']:+.1f}% | {g.loc['dp_tuned', 'breakages']} | "
                     f"{rules.loc[best, 'saving_vs_fixed_pct']:+.1f}% ({best}) | "
                     f"{g.loc['one_step', 'saving_vs_fixed_pct']:+.1f}% | {g.loc['oracle', 'saving_vs_fixed_pct']:+.1f}% |")
        L.append("")

    L.append("## Win counts over the 24 cost settings\n")
    L.append("| source | policy | cheaper than fixed | ≥3% cheaper than fixed | interval excludes 0 | "
             "cheaper than best rule (ex post) |")
    L.append("|---|---|---:|---:|---:|---:|")
    for src in models:
        s = agg[agg["source"] == src]
        best_rule = s[s["policy"].isin(RULES)].groupby("cost", observed=True)["cost_per_good"].min()
        for pol in ["dp", "dp_tuned", "hazard", "rul_q10"]:
            dp = s[s["policy"] == pol].set_index("cost")
            L.append(f"| {src} | {pol} | {(dp['saving_vs_fixed_pct'] > 0).sum()} | "
                     f"{(dp['saving_vs_fixed_pct'] >= 3).sum()} | {(dp['saving_ci_lo'] > 0).sum()} | "
                     f"{(dp['cost_per_good'] < best_rule.reindex(dp.index) - 1e-9).sum()} |")
    L.append("")

    L.append("## Tuned parameters at India typical costs (median over the 13 folds)\n")
    p = per[(per["cost"] == "india_typical") & (per["params"] != "")]
    L.append("| source | policy | parameters |")
    L.append("|---|---|---|")
    for (src, pol), g in p.groupby(["source", "policy"], sort=False):
        vals = pd.DataFrame([dict(kv.split("=") for kv in s.split(";")) for s in g["params"]]).astype(float)
        L.append(f"| {src} | {pol} | " + ", ".join(f"{k} = {v:.4g}" for k, v in vals.median().items()) + " |")
    L.append("")
    L.append("## Reading these numbers\n")
    L.append("- 13 cutters is the sample size; a policy's breakage count moves by whole cutters. Intervals are wide.\n"
             "- The DP is optimal only if the curve it is given is right. The yardstick curves are not calibrated, so "
             "the DP can lose to a tuned threshold that absorbs the miscalibration in its tuned value.\n"
             "- `dp` trusts the curve completely: g comes from Dinkelbach's iteration on the training replays. "
             "When the curves miss sudden failures, those breakages push g up, and a high g makes keeping look "
             "better, so `dp` can settle on a poor fixed point when breakages are expensive. `dp_tuned` "
             "grid-searches g on the training cutters, the same tuning effort the thresholds get. A one-step "
             "rule with a tuned g is exactly the risk threshold (`hazard`).\n"
             "- The fixed interval uses no predictions; DP and the rules use the curves. The oracle is unreachable.\n"
             "- Wasted cycles count good cycles left on cutters changed early; a breakage wastes none but costs C_f.\n")
    (OUT / "single_cutter.md").write_text("\n".join(L))


def figure(agg: pd.DataFrame, models):
    # Palette: reference categorical slots (dataviz skill, light mode), text in neutral ink.
    # One colour per prediction source in both panels, one shared legend on top.
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    ink, muted, grid_c = "#0b0b0b", "#52514e", "#e4e3df"
    series = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#c2410c", "#8a96a0"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.6 + 0.5 * len(models)), gridspec_kw=dict(width_ratios=[1.1, 1]))

    ax = axes[0]
    ind = agg[agg["cost"] == "india_typical"]
    pols = [p for p in ORDER if p != "oracle"]
    y = np.arange(len(pols))
    hgt = 0.8 / len(models)
    for i, src in enumerate(models):
        s = ind[ind["source"] == src].set_index("policy").loc[pols]
        ys = y + (i - (len(models) - 1) / 2) * hgt
        ax.barh(ys, s["cost_per_good"], height=hgt - 0.03, color=series[i])
        for yy, v, b in zip(ys, s["cost_per_good"], s["breakages"]):
            ax.text(v + 1, yy, f"{v:.0f}  ({b} broke)", va="center", fontsize=7, color=muted)
    orc = ind[ind["policy"] == "oracle"]["cost_per_good"].iloc[0]
    ax.axvline(orc, color=muted, lw=1, ls="--")
    ax.text(orc, len(pols) - 0.45, " perfect knowledge", color=muted, fontsize=8, va="bottom")
    ax.set_yticks(y, [LABEL[p] for p in pols], fontsize=9, color=ink)
    ax.invert_yaxis()
    ax.set_xlabel("₹ per good cycle (13 held-out cutters pooled)", color=ink)
    ax.set_title("India typical costs (breakage = 2.1 × planned change)", fontsize=10, color=ink, loc="left")
    ax.set_xlim(0, ind["cost_per_good"].max() * 1.22)

    ax = axes[1]
    g = agg[agg["cost"].str.startswith("r") & np.isclose(agg["k"], 0.006)]
    orc = g[(g["policy"] == "oracle") & (g["source"] == models[0])].sort_values("r")
    ax.plot(orc["r"], orc["saving_vs_fixed_pct"], color=muted, lw=2, ls="--")
    for i, src in enumerate(models):
        for pol, ls in [("dp_tuned", "-"), ("dp", ":")]:
            d = g[(g["policy"] == pol) & (g["source"] == src)].sort_values("r")
            ax.plot(d["r"], d["saving_vs_fixed_pct"], color=series[i], lw=2, ls=ls, marker="o" if ls == "-" else None, ms=4)
            if pol == "dp_tuned" and len(models) <= 2:
                ax.fill_between(d["r"], d["saving_ci_lo"], d["saving_ci_hi"], color=series[i], alpha=0.12, lw=0)
    ax.axhline(0, color=ink, lw=0.8)
    ax.set_xscale("log")
    ax.set_xticks([1.5, 2, 3, 5, 10, 20, 30], ["1.5", "2", "3", "5", "10", "20", "30"])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_ylim(-50, 100)
    ax.set_xlabel("breakage cost ÷ planned change cost (k = 0.006)", color=ink)
    ax.set_ylabel("% cheaper per good cycle than the tuned fixed interval", color=ink)
    ax.set_title("Saving over the tuned fixed interval across the cost grid (clipped at −50%)",
                 fontsize=10, color=ink, loc="left")
    key = [Line2D([], [], color=muted, lw=2, ls="--", label="perfect knowledge"),
           Line2D([], [], color=muted, lw=2, ls="-", marker="o", ms=4, label=LABEL["dp_tuned"]),
           Line2D([], [], color=muted, lw=2, ls=":", label=LABEL["dp"])]
    if len(models) <= 2:
        key.append(Patch(color=muted, alpha=0.2, label="95% interval over cutters (g tuned)"))
    ax.legend(handles=key, fontsize=8, frameon=False, loc="upper left")
    for a in axes:
        a.grid(axis="x" if a is axes[0] else "y", color=grid_c, lw=0.8)
        a.set_axisbelow(True)
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            a.spines[sp].set_color(muted)
        a.tick_params(colors=muted)
    fig.legend(handles=[Patch(color=series[i], label=SOURCE_LABEL.get(m, m)) for i, m in enumerate(models)],
               loc="upper center", ncol=len(models), frameon=False, fontsize=9, title="failure curves from",
               title_fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(OUT / "single_cutter.png", dpi=150)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["weibull_settings_age", "lgbm_hazard"])
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    per = run(args.models)
    per.to_csv(OUT / "single_cutter_per_cutter.csv", index=False)
    agg = aggregate(per)
    agg.round(5).to_csv(OUT / "single_cutter.csv", index=False)
    write_markdown(agg, per, args.models)
    figure(agg, args.models)
    show = agg[agg["cost"] == "india_typical"][["source", "policy", "cost_per_good", "breakages", "life_used",
                                                 "saving_vs_fixed_pct", "regret_vs_oracle_pct"]]
    print(show.round(2).to_string(index=False))
