"""
Was Hamilton's 1790 debt assumption allocated fairly across the states?

Reads data/assumption_1790.csv and writes:
  output/assumption_by_state.csv   - the enriched table (per-capita, shares, counterfactuals)
  output/summary.md                - descriptive stats, regional test, allocation gaps
  output/fig_*.png                 - charts

Run:  python src/analysis.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

df = pd.read_csv(ROOT / "data" / "assumption_1790.csv")

# ---------------------------------------------------------------- normalize
df["pop_free_1790"] = df["pop_total_1790"] - df["pop_enslaved_1790"]
# the Constitution's apportionment basis: free persons + 3/5 of enslaved persons
df["pop_three_fifths"] = df["pop_free_1790"] + 0.6 * df["pop_enslaved_1790"]

df["per_capita_total"] = df["assumed_authorized_usd"] / df["pop_total_1790"]
df["per_capita_free"] = df["assumed_authorized_usd"] / df["pop_free_1790"]

total_debt = df["assumed_authorized_usd"].sum()
df["share_of_assumption"] = df["assumed_authorized_usd"] / total_debt

# counterfactual: what each state gets if $21.5M is split in proportion to population
for basis in ["pop_total_1790", "pop_free_1790", "pop_three_fifths"]:
    share = df[basis] / df[basis].sum()
    df[f"cf_{basis}"] = total_debt * share
    df[f"gap_vs_{basis}"] = df["assumed_authorized_usd"] - df[f"cf_{basis}"]

# outlier flags on per-capita (total population)
pc = df["per_capita_total"]
df["z_score"] = (pc - pc.mean()) / pc.std(ddof=1)
q1, q3 = pc.quantile([0.25, 0.75])
iqr = q3 - q1
df["iqr_outlier"] = (pc < q1 - 1.5 * iqr) | (pc > q3 + 1.5 * iqr)

df = df.sort_values("per_capita_total", ascending=False).reset_index(drop=True)
pc = df["per_capita_total"]
df.to_csv(OUT / "assumption_by_state.csv", index=False)

# ---------------------------------------------------------------- descriptives
lines = []
w = lines.append
w("# Hamilton's 1790 Debt Assumption - analysis summary\n")
w(f"Total authorized assumption: ${total_debt:,.0f} across {len(df)} states.\n")

w("## Per-capita assumption (authorized $ / 1790 total population)\n")
desc = pc.describe()
w(f"- Mean: ${desc['mean']:.2f}   Median: ${desc['50%']:.2f}   Std dev: ${desc['std']:.2f}")
w(f"- Min: ${desc['min']:.2f} ({df.loc[pc.idxmin(), 'state']})   "
  f"Max: ${desc['max']:.2f} ({df.loc[pc.idxmax(), 'state']})")
w(f"- Coefficient of variation: {desc['std'] / desc['mean']:.2f} "
  "(std dev as a fraction of the mean - a 'how unequal is this' number)")
w(f"- Skew: {pc.skew():.2f}\n")

w("| State | Region | Assumed $ | Pop (1790) | $ per capita | $ per free person | z-score |")
w("|---|---|---:|---:|---:|---:|---:|")
for _, r in df.iterrows():
    w(f"| {r.state} | {r.region} | {r.assumed_authorized_usd:,.0f} | {r.pop_total_1790:,.0f} "
      f"| {r.per_capita_total:.2f} | {r.per_capita_free:.2f} | {r.z_score:+.2f} |")
w("")
outliers = df[df["iqr_outlier"]]["state"].tolist()
w(f"IQR-rule outliers (1.5xIQR): {outliers if outliers else 'none'}. "
  f"States with |z| > 1.5: {df[df.z_score.abs() > 1.5]['state'].tolist()}\n")

# ---------------------------------------------------------------- regional comparison
w("## Regional comparison: New England vs. Southern\n")
ne = df[df.region == "New England"]["per_capita_total"]
so = df[df.region == "Southern"]["per_capita_total"]
mid = df[df.region == "Middle"]["per_capita_total"]
for name, s in [("New England", ne), ("Middle", mid), ("Southern", so)]:
    w(f"- {name}: n={len(s)}, mean ${s.mean():.2f}, median ${s.median():.2f}")

t, p_t = stats.ttest_ind(ne, so, equal_var=False)
u, p_u = stats.mannwhitneyu(ne, so, alternative="two-sided")

# exact permutation test: every way to label 9 states as 4 NE / 5 Southern
obs = ne.mean() - so.mean()
perm = stats.permutation_test(
    (ne.values, so.values), lambda a, b: a.mean() - b.mean(),
    permutation_type="independent", n_resamples=np.inf, alternative="two-sided")

w("")
w(f"- Observed difference in means (NE - South): ${obs:.2f}")
w(f"- Welch t-test: t = {t:.2f}, p = {p_t:.3f}")
w(f"- Mann-Whitney U: U = {u:.0f}, p = {p_u:.3f}")
w(f"- Exact permutation test (all {int(perm.null_distribution.size)} relabelings): p = {perm.pvalue:.3f}")
w("")
w("**Interpretation caveat.** These 13 states are the entire population of interest, "
  "not a sample from a larger one, so a p-value here answers a narrower question: "
  "'if the regional labels were shuffled at random, how often would a gap this big appear?' "
  "With n=4 vs n=5 the tests have little power, so a non-significant result is weak "
  "evidence of 'no regional tilt', not proof of it. The effect size (the dollar gap) is "
  "the more honest headline.\n")

# ---------------------------------------------------------------- fairness vs. apportionment
w("## Allocation gap: actual quota vs. population-proportional quota\n")
w("If the $21.5M had been split like congressional apportionment, each state's quota "
  "would be its population share x $21.5M. Positive gap = state got more than a per-head "
  "split would give it.\n")
w("| State | Actual $ | If by total pop | Gap | If by free pop | Gap | If by 3/5 rule | Gap |")
w("|---|---:|---:|---:|---:|---:|---:|---:|")
for _, r in df.sort_values("gap_vs_pop_total_1790", ascending=False).iterrows():
    w(f"| {r.state} | {r.assumed_authorized_usd/1e6:.2f}M | {r.cf_pop_total_1790/1e6:.2f}M | "
      f"{r.gap_vs_pop_total_1790/1e6:+.2f}M | {r.cf_pop_free_1790/1e6:.2f}M | "
      f"{r.gap_vs_pop_free_1790/1e6:+.2f}M | {r.cf_pop_three_fifths/1e6:.2f}M | "
      f"{r.gap_vs_pop_three_fifths/1e6:+.2f}M |")
w("")
# chi-square goodness of fit: does the actual split deviate from population-proportional?
for basis, label in [("pop_total_1790", "total population"), ("pop_free_1790", "free population"),
                     ("pop_three_fifths", "three-fifths basis")]:
    expected = df[f"cf_{basis}"] / 1e5   # scale to units of $100k to keep chi2 interpretable
    observed = df["assumed_authorized_usd"] / 1e5
    chi2, p = stats.chisquare(observed, expected)
    mad = (df[f"gap_vs_{basis}"].abs().sum() / 2) / total_debt
    w(f"- vs {label}: chi2 = {chi2:.1f}, p = {p:.2e}; "
      f"{mad:.1%} of the total would have to move between states to match this basis.")
w("")
w("The 'share that would have to move' figure (half the sum of absolute gaps, as a % of "
  "the total) is a dissimilarity index - the same idea used to measure how far a budget "
  "is from a benchmark allocation.\n")

# concentration: how much of the debt sits in the top states
top3 = df.nlargest(3, "assumed_authorized_usd")
w("## Concentration\n")
w(f"- Top 3 states by dollars ({', '.join(top3.state)}) hold "
  f"{top3.assumed_authorized_usd.sum()/total_debt:.1%} of the assumption "
  f"with {top3.pop_total_1790.sum()/df.pop_total_1790.sum():.1%} of the population.")
corr = stats.spearmanr(df["pop_total_1790"], df["assumed_authorized_usd"])
w(f"- Spearman rank correlation, population vs. assumed $: rho = {corr.statistic:.2f} "
  f"(p = {corr.pvalue:.3f}). Bigger states got more, but far from proportionally.\n")

(OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")

# ---------------------------------------------------------------- charts
colors = {"New England": "#1f4e79", "Middle": "#7f7f7f", "Southern": "#b5533c"}
rng = np.random.default_rng(0)

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.barh(df.state[::-1], df.per_capita_total[::-1],
        color=[colors[r] for r in df.region[::-1]])
ax.axvline(pc.mean(), ls="--", color="black", lw=1, label=f"mean ${pc.mean():.2f}")
ax.set_xlabel("Authorized assumption, $ per person (1790 census)")
ax.set_title("Federal assumption of state debt, 1790 - per capita by state")
for k, v in colors.items():
    ax.bar(0, 0, color=v, label=k)
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig_per_capita.png", dpi=150)

fig, ax = plt.subplots(figsize=(7, 6))
ax.scatter(df.cf_pop_total_1790 / 1e6, df.assumed_authorized_usd / 1e6,
           c=[colors[r] for r in df.region], s=70)
lim = max(df.cf_pop_total_1790.max(), df.assumed_authorized_usd.max()) / 1e6 * 1.1
ax.plot([0, lim], [0, lim], ls="--", color="black", lw=1, label="proportional to population")
for _, r in df.iterrows():
    ax.annotate(r.state, (r.cf_pop_total_1790 / 1e6, r.assumed_authorized_usd / 1e6),
                xytext=(4, 4 if r.assumed_authorized_usd > 5e5 else 12 * (r.state in ("Rhode Island", "New Hampshire")) - 6), textcoords="offset points", fontsize=8)
ax.set_xlabel("Quota if split by 1790 population ($M)")
ax.set_ylabel("Actual authorized quota ($M)")
ax.set_title("Who got more than their head-count share?")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig_actual_vs_proportional.png", dpi=150)

fig, ax = plt.subplots(figsize=(6, 5))
data = [ne, mid, so]
ax.boxplot(data, tick_labels=["New England", "Middle", "Southern"], widths=0.5)
for i, s in enumerate(data, start=1):
    ax.scatter(np.full(len(s), i) + rng.uniform(-0.08, 0.08, len(s)), s, color="black", zorder=3)
ax.set_ylabel("$ per capita")
ax.set_title("Per-capita assumption by region")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig_region_box.png", dpi=150)

print(f"Wrote {OUT / 'summary.md'} and 3 figures.")
