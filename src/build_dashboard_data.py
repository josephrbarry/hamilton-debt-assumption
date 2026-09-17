"""
Build the tidy CSVs the Power BI report reads, from output/assumption_ledger.csv
(which src/analysis.py writes).

Tables written to powerbi/data/:
  states.csv          one row per state - every measure, 1790 $ and 2025 $ side by side
  ledger_long.csv     one row per state x reconciliation step (estimate, quota, ... net)
  waterfall.csv       the $21.5M -> $18.27M bridge, in steps
  counterfactual.csv  one row per state x population basis: quota vs per-head split
  stats.csv           every test in the write-up: statistic, p-value, plain-English read

Run:  python src/build_dashboard_data.py      (after src/analysis.py)
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "powerbi" / "data"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(ROOT / "output" / "assumption_ledger.csv")
CPI = float(pd.read_csv(ROOT / "data" / "inflation.csv").set_index("measure")
            .loc["cpi", "factor_1790_to_2025"])
TOTAL_POP = df.pop_total_1790.sum()
TOTAL_QUOTA = df.quota_usd.sum()

# ---------------------------------------------------------------- states (wide)
s = pd.DataFrame({
    "state": df.state,
    "region": df.region,
    "position_1793": df.position.str.capitalize(),          # Creditor / Debtor
    "pop_total_1790": df.pop_total_1790,
    "pop_enslaved_1790": df.pop_enslaved_1790,
    "pop_free_1790": df.pop_free_1790,
    "pop_share_pct": df.pop_total_1790 / TOTAL_POP * 100,
    "estimate_1790_usd": df.debt_estimate_1790_usd,
    "estimate_basis": df.basis,
    "quota_usd": df.quota_usd,
    "quota_share_pct": df.quota_usd / TOTAL_QUOTA * 100,
    "quota_vs_estimate_usd": df.quota_vs_estimate_usd,
    "subscribed_1792_usd": df.subscribed_usd,
    "assumed_usd": df.assumed_usd,
    "takeup_pct": df.takeup_rate * 100,
    "quota_unused_usd": df.quota_unused_usd,
    "remaining_state_debt_usd": df.remaining_state_debt_usd,
    "settlement_usd": df.settlement_balance_usd,
    "net_position_usd": df.net_position_usd,
    "quota_per_capita": df.quota_pc,
    "assumed_per_capita": df.assumed_pc,
    "settlement_per_capita": df.settlement_balance_pc,
    "net_position_per_capita": df.net_position_pc,
    "quota_per_free_person": df.quota_pc_free,
    "quota_z_score": df.z_score,
    "quota_gap_vs_population_usd": df.gap_vs_pop_total_1790,
    "settlement_abs_usd": df.settlement_balance_usd.abs(),
})
for c in [c for c in s.columns if c.endswith("_usd") or c.endswith("per_capita")
          or c.endswith("per_free_person")]:
    s[c + "_2025"] = s[c] * CPI
s["quota_rank"] = s.quota_per_capita.rank(ascending=False).astype(int)
s = s.sort_values("quota_per_capita", ascending=False)
s.to_csv(OUT / "states.csv", index=False)

# ---------------------------------------------------------------- ledger (long)
STEPS = [  # order, label, column
    (1, "1. Hamilton estimate, Jan 1790", "debt_estimate_1790_usd"),
    (2, "2. Act quota, Aug 1790", "quota_usd"),
    (3, "3. Subscribed, 1st window, Jan 1792", "subscribed_usd"),
    (4, "4. Finally assumed, to 1793", "assumed_usd"),
    (5, "5. Settlement balance, Jun 1793", "settlement_balance_usd"),
    (6, "6. Net position (4 + 5)", "net_position_usd"),
]
rows = []
for order, label, colname in STEPS:
    for _, r in df.iterrows():
        v = r[colname]
        rows.append({"state": r.state, "region": r.region, "step_order": order, "step": label,
                     "usd_1790": v, "usd_2025": v * CPI if pd.notna(v) else np.nan,
                     "per_capita_1790": v / r.pop_total_1790 if pd.notna(v) else np.nan,
                     "per_capita_2025": v / r.pop_total_1790 * CPI if pd.notna(v) else np.nan})
pd.DataFrame(rows).to_csv(OUT / "ledger_long.csv", index=False)

# ---------------------------------------------------------------- waterfall
known = df[df.estimate_known]
blank = df[~df.estimate_known]
cuts = df[df.quota_vs_estimate_usd < 0].quota_vs_estimate_usd.sum()
adds = df[df.quota_vs_estimate_usd > 0].quota_vs_estimate_usd.sum()
wf = [
    (1, "Hamilton estimate (9 states)", known.debt_estimate_1790_usd.sum()),
    (2, "Quotas for 4 states with no return", blank.quota_usd.sum()),
    (3, "Congress cuts (MA, SC, CT, VA)", cuts),
    (4, "Rounding up (NY, NJ)", adds),
    (5, "Unused quota", -df.quota_unused_usd.sum()),
]
assert abs(sum(v for _, _, v in wf[:4]) - TOTAL_QUOTA) < 1
assert abs(sum(v for _, _, v in wf) - df.assumed_usd.sum()) < 1
pd.DataFrame([{"step_order": o, "step": l, "usd_1790": v, "usd_2025": v * CPI,
               "usd_1790_m": v / 1e6, "usd_2025_m": v * CPI / 1e6} for o, l, v in wf]
             ).to_csv(OUT / "waterfall.csv", index=False)

# ---------------------------------------------------------------- counterfactual
BASES = [("Total population", "pop_total_1790"), ("Free population", "pop_free_1790"),
         ("Three-fifths basis", "pop_three_fifths")]
rows = []
for label, b in BASES:
    for _, r in df.iterrows():
        rows.append({"state": r.state, "region": r.region, "basis": label,
                     "quota_usd": r.quota_usd, "proportional_usd": r[f"cf_{b}"],
                     "gap_usd": r[f"gap_vs_{b}"],
                     "quota_usd_2025": r.quota_usd * CPI, "gap_usd_2025": r[f"gap_vs_{b}"] * CPI,
                     "quota_m": r.quota_usd / 1e6, "proportional_m": r[f"cf_{b}"] / 1e6,
                     "gap_m": r[f"gap_vs_{b}"] / 1e6})
pd.DataFrame(rows).to_csv(OUT / "counterfactual.csv", index=False)

# ---------------------------------------------------------------- stats (recomputed here so the table is self-contained)
ne = df[df.region == "New England"].quota_pc
so = df[df.region == "Southern"].quota_pc
cred = df[df.position == "creditor"].assumed_pc
debt = df[df.position == "debtor"].assumed_pc
mean_diff = lambda a, b: a.mean() - b.mean()
perm_kw = dict(permutation_type="independent", n_resamples=np.inf)
t_reg = stats.ttest_ind(ne, so, equal_var=False)
u_reg = stats.mannwhitneyu(ne, so, alternative="two-sided")
p_reg = stats.permutation_test((ne.values, so.values), mean_diff, alternative="two-sided", **perm_kw)
p_fair = stats.permutation_test((cred.values, debt.values), mean_diff, alternative="greater", **perm_kw)
rho = stats.spearmanr(df.assumed_pc, df.settlement_balance_pc)
pear = stats.pearsonr(df.assumed_pc, df.settlement_balance_pc)
rho_raw = stats.spearmanr(df.assumed_usd, df.settlement_balance_usd)
di = {lbl: df[f"gap_vs_{b}"].abs().sum() / 2 / TOTAL_QUOTA * 100 for lbl, b in BASES}

st = [
    ("A", "Regional tilt", "Welch t-test, NE vs South quota per head", f"t = {t_reg.statistic:.2f}", t_reg.pvalue,
     f"NE ${ne.mean():.2f} vs South ${so.mean():.2f} per head. No detectable regional tilt."),
    ("A", "Regional tilt", "Mann-Whitney U, NE vs South", f"U = {u_reg.statistic:.0f}", u_reg.pvalue,
     "Rank-based version of the same comparison; agrees."),
    ("A", "Regional tilt", "Exact permutation, NE vs South (126 relabelings)", ("diff = (${:.2f})".format(-mean_diff(ne, so)) if mean_diff(ne, so) < 0 else f"diff = ${mean_diff(ne, so):.2f}"), p_reg.pvalue,
     "Every possible relabeling of 9 states as 4 NE / 5 South. South Carolina alone drives the Southern mean."),
    ("B", "Relief vs contribution", "Spearman rho, relief per head vs 1793 settlement per head", f"rho = {rho.statistic:.2f}", rho.pvalue,
     "Moderate positive rank correlation: states the audit found had over-paid got more relief."),
    ("B", "Relief vs contribution", "Pearson r, same variables", f"r = {pear.statistic:.2f}", pear.pvalue,
     "Linear version; agrees in size."),
    ("B", "Relief vs contribution", "Spearman rho on raw dollars (no shared population denominator)", f"rho = {rho_raw.statistic:.2f}", rho_raw.pvalue,
     "Same sign, weaker. Per-capita ratios share a denominator, which can inflate a correlation; this is the check."),
    ("B", "Relief vs contribution", "Exact permutation, creditor vs debtor states, one-sided (1716 relabelings)", f"${cred.mean():.2f} vs ${debt.mean():.2f}", p_fair.pvalue,
     f"Creditor states received {cred.mean() / debt.mean():.1f}x the relief per head of debtor states. Uncorrected for multiple comparisons; suggestive, not confirmatory."),
]
for lbl, _ in BASES:
    st.append(("C", "Proportional to population?", f"Dissimilarity index vs {lbl.lower()}",
               f"{di[lbl]:.1f}%", np.nan,
               f"{di[lbl]:.1f}% of the $21.5M would have to move between states to match this basis. "
               "Descriptive; no chi-square is reported because that test assumes counts and its value depends on the unit."))
pd.DataFrame(st, columns=["group", "question", "test", "statistic", "p_value", "read"]) \
    .assign(test_order=range(1, len(st) + 1)) \
    .to_csv(OUT / "stats.csv", index=False)

# ---------------------------------------------------------------- tie-out (footing schedule)
sub = pd.read_csv(ROOT / "data" / "subscriptions_1792.csv").set_index("state")
printed = sub.subscribed_usd.copy()
printed["North Carolina"] -= 500000            # the figure as printed, before reconciliation
oversub_printed = sub.oversubscribed_usd.copy()
oversub_printed["Massachusetts"] += 30000      # printed $477,013.81; arithmetic gives $447,013.81
enc = pd.DataFrame({
    "state": sub.index,
    "quota_usd": sub.quota_usd.values,
    "subscribed_printed_usd": printed.values,
    "unsubscribed_printed_usd": sub.unsubscribed_usd.values,
    "oversubscribed_printed_usd": oversub_printed.values,
})
enc["unsubscribed_computed_usd"] = (enc.quota_usd - enc.subscribed_printed_usd).clip(lower=0)
enc["oversubscribed_computed_usd"] = (enc.subscribed_printed_usd - enc.quota_usd).clip(lower=0)
# variance = computed less printed, on whichever side of the quota the state sits
enc["variance_usd"] = ((enc.unsubscribed_computed_usd - enc.unsubscribed_printed_usd)
                       + (enc.oversubscribed_computed_usd - enc.oversubscribed_printed_usd))
enc["status"] = np.where(enc.variance_usd.abs() < 1, "Ties",
                np.where(enc.variance_usd.abs() < 1000, "Immaterial", "Does not foot"))
enc["subscribed_reconciled_usd"] = sub.subscribed_usd.values
enc["line_order"] = range(1, len(enc) + 1)
enc.to_csv(OUT / "enclosure_d_tieout.csv", index=False)

tie = [
    ("Funding Act sec. 14, Aug 1790", "Quota column", 21500000, df.quota_usd.sum()),
    ("Schedule E, Jan 1790", "Nine known states ('about twenty-one millions and a half')", 21500000,
     df.debt_estimate_1790_usd.sum()),
    ("Enclosure D, Jan 1792", "Subscribed column, as printed", 18328186.21, printed.sum()),
    ("Enclosure D, Jan 1792", "North Carolina line: quota less unsubscribed vs printed subscribed",
     1166355.57, 2400000 - 733644.43),
    ("Enclosure D, Jan 1792", "Subscribed column, after NC reconciliation", 18328186.21, sub.subscribed_usd.sum()),
    ("Enclosure D, Jan 1792", "Massachusetts line: subscribed less quota vs printed over-subscribed",
     477013.81, 4447013.81 - 4000000),
    ("Enclosure D, Jan 1792", "Over-subscribed column, as printed", 1255851.82, oversub_printed.sum()),
    ("Enclosure D, Jan 1792", "Unsubscribed column", 4427665.61, sub.unsubscribed_usd.sum()),
    ("Enclosure D, Jan 1792", "Printed total explained: quota - unsubscribed + over-subscribed (both as printed)",
     18328186.21, 21500000 - 4427665.61 + oversub_printed.sum()),
    ("Enclosure D, Jan 1792", "Reconciled total: quota - unsubscribed + over-subscribed (MA corrected)",
     sub.subscribed_usd.sum(), 21500000 - 4427665.61 + sub.oversubscribed_usd.sum()),
    ("Bayley (Treasury, 1881)", "Amount assumed column", 18271786.47, df.assumed_usd.sum()),
    ("Commissioners, Jun 1793", "Creditor states (Jefferson's pencilled total)", 3517584,
     df[df.settlement_balance_usd > 0].settlement_balance_usd.sum()),
    ("Commissioners, Jun 1793", "Debtor states", 3517584,
     -df[df.settlement_balance_usd < 0].settlement_balance_usd.sum()),
]
tie_df = pd.DataFrame(tie, columns=["document", "line", "stated_usd", "computed_usd"])
tie_df["variance_usd"] = tie_df.computed_usd - tie_df.stated_usd
tie_df["status"] = np.where(tie_df.variance_usd.abs() < 1, "Ties",
                   np.where(tie_df.variance_usd.abs() < 5000, "Ties (rounded)", "Does not foot"))
tie_df["line_order"] = range(1, len(tie_df) + 1)
tie_df.to_csv(OUT / "tieout.csv", index=False)

# ---------------------------------------------------------------- roll-forward (totals bridge as a schedule)
rf = pd.DataFrame(wf, columns=["line_order", "line", "usd_1790"])
rf["usd_2025"] = rf.usd_1790 * CPI
rf["running_usd_1790"] = rf.usd_1790.cumsum()
rf["running_usd_2025"] = rf.running_usd_1790 * CPI
rf.to_csv(OUT / "rollforward.csv", index=False)

print(f"Wrote 8 tables to {OUT}")
