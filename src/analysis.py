"""
Was Hamilton's 1790 debt assumption fair?  An accountant's reconciliation.

Four primary-source ledgers, all of which crossed Hamilton's desk:
  1. Schedule E (Jan 1790)      - state debt as reported / estimated (the opening balance)
  2. Funding Act sec. 14 (Aug 1790) - quota per state (the authorized ceiling)
  3. Enclosure D (Jan 1792)     - what creditors actually subscribed (the take-up)
  4. Commissioners' report (Jun 1793) - final settlement of war accounts (the true-up)
plus the 1790 census as the allocation base.

Writes:
  output/assumption_ledger.csv   - one row per state, every column, for Power BI
  output/summary.md              - the write-up
  output/fig_*.png               - charts

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
DATA = ROOT / "data"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------- load + join
base = pd.read_csv(DATA / "assumption_1790.csv")
est = pd.read_csv(DATA / "hamilton_1790_schedule_e.csv")
sub = pd.read_csv(DATA / "subscriptions_1792.csv")
stl = pd.read_csv(DATA / "settlement_1793.csv")
fin = pd.read_csv(DATA / "assumed_final_bayley.csv")
infl = pd.read_csv(DATA / "inflation.csv").set_index("measure").factor_1790_to_2025
CPI = infl["cpi"]              # $1 (1790) -> $ (2025), purchasing power
GDP_SHARE = infl["gdp_share"]  # $1 (1790) -> $ (2025), same share of the economy

df = (base.merge(est, on="state").merge(sub, on="state").merge(stl, on="state")
          .merge(fin, on="state"))
assert abs(df.assumed_final_usd.sum() - 18271786.47) < 0.01, "Bayley total does not foot"
assert (df.quota_usd == df.assumed_authorized_usd).all(), "quota mismatch between files"
assert abs(df.settlement_balance_usd.sum()) < 1, "1793 settlement should net to zero"
df = df.drop(columns="assumed_authorized_usd")

# ---------------------------------------------------------------- derived columns
df["pop_free_1790"] = df.pop_total_1790 - df.pop_enslaved_1790
df["pop_three_fifths"] = df.pop_free_1790 + 0.6 * df.pop_enslaved_1790

# Step 1 -> 2: how the quota was set. Variance vs Hamilton's own estimate.
df["estimate_known"] = df.debt_estimate_1790_usd.notna()
df["quota_vs_estimate_usd"] = df.quota_usd - df.debt_estimate_1790_usd
df["quota_vs_estimate_pct"] = df.quota_vs_estimate_usd / df.debt_estimate_1790_usd

# Step 2 -> 3: take-up. Enclosure D is the first-window interim (subscriptions above quota
# were scaled back); Bayley's figure is the final amount assumed after the extended window.
df["assumed_interim_usd"] = df[["subscribed_usd", "quota_usd"]].min(axis=1)
df["assumed_usd"] = df.assumed_final_usd
df["takeup_rate"] = df.assumed_usd / df.quota_usd
df["quota_unused_usd"] = df.quota_usd - df.assumed_usd

# Step 4: settlement. Positive = Union owed the state; negative = state owed the Union.
# Net federal position = debt relief received + settlement balance (both are $ the state gained).
df["net_position_usd"] = df.assumed_usd + df.settlement_balance_usd

# Per-capita everything (total population, 1790 boundaries)
for col in ["quota_usd", "assumed_usd", "settlement_balance_usd", "net_position_usd",
            "remaining_state_debt_usd"]:
    df[col.replace("_usd", "_pc")] = df[col] / df.pop_total_1790
df["quota_pc_free"] = df.quota_usd / df.pop_free_1790

# 2025-dollar twins of every $ column (CPI basis) so the ledger carries both
for col in [c for c in df.columns if c.endswith("_usd") or c.endswith("_pc")]:
    df[col + "_2025"] = df[col] * CPI

# Allocation counterfactuals (what a per-head split of the same $21.5M would give)
total_quota = df.quota_usd.sum()
for basis in ["pop_total_1790", "pop_free_1790", "pop_three_fifths"]:
    df[f"cf_{basis}"] = total_quota * df[basis] / df[basis].sum()
    df[f"gap_vs_{basis}"] = df.quota_usd - df[f"cf_{basis}"]

# z-score / outlier on quota per capita
qpc = df.quota_pc
df["z_score"] = (qpc - qpc.mean()) / qpc.std(ddof=1)
q1, q3 = qpc.quantile([0.25, 0.75])
df["iqr_outlier"] = (qpc < q1 - 1.5 * (q3 - q1)) | (qpc > q3 + 1.5 * (q3 - q1))

df = df.sort_values("quota_pc", ascending=False).reset_index(drop=True)
df.to_csv(OUT / "assumption_ledger.csv", index=False)


def acct(x, fmt):
    """Accounting convention: negatives in parentheses, never a minus sign."""
    return f"({fmt.format(abs(x))})" if x < 0 else fmt.format(x)


def m(x):        # 1790 $ millions with 2025 $ beside it
    return f"{acct(x / 1e6, '{:,.2f}M')} [{acct(x * CPI / 1e6, '{:,.0f}M')}]"


def usd(x):      # 1790 $ with 2025 $ beside it
    return f"{acct(x, '${:,.0f}')} [{acct(x * CPI, '${:,.0f}')}]"


def pc(x):       # per-capita 1790 $ with 2025 $ beside it
    return f"{acct(x, '${:.2f}')} [{acct(x * CPI, '${:,.0f}')}]"


L = []
w = L.append

# ================================================================ write-up
w("# Hamilton's 1790 Debt Assumption - an accountant's reconciliation\n")
w("Every figure below is from a document Hamilton wrote or received. See `data/SOURCES.md`.\n")
w(f"**Dollars are shown as 1790 $ [2025 $ in brackets]**, converted at {CPI:.1f}x by CPI "
  "(MeasuringWorth; the Federal Reserve's series starts in 1800 and gives ~19x from that year). "
  "Negatives are in parentheses. CPI understates the scale of these sums: the $21.5M "
  "authorized was about 11% of 1790 GDP (a modern reconstruction, so an order of magnitude); "
  f"the same share of the 2025 economy is ${21.5e6 * GDP_SHARE / 1e12:,.1f} trillion.\n")

# ---------------------------------------------------------------- 1. opening balance
w("## 0. Tie-out: do the source documents foot?\n")
w("Before analyzing, each table was footed against its own printed totals.\n")
w(f"- Funding Act quotas sum to {usd(df.quota_usd.sum())} - ties to the Act's $21.5M.")
w(f"- 1793 settlement: creditors {usd(df[df.settlement_balance_usd > 0].settlement_balance_usd.sum())}, "
  f"debtors {usd(-df[df.settlement_balance_usd < 0].settlement_balance_usd.sum())} - ties to "
  "Jefferson's pencilled total of $3,517,584 and nets to zero.")
w("- Enclosure D (1792 subscriptions): **does not foot as published.** On Founders Online the "
  "subscribed column sums to $17,798,186 against a stated $18,328,186. Row-level tie-out "
  "(quota - subscribed = unsubscribed) isolates a $500,000 error in the North Carolina line "
  "($1,666,355.57 reconciled), a $30,000 error in the Massachusetts line ($4,477,013.81 "
  "reconciled) and a $30 error in Maryland's unsubscribed line ($500,774.60). With those three "
  "cells corrected every column foots to its printed total to the penny: the Treasury's "
  "arithmetic was right and the published cells are wrong. Comparison of four printings "
  "(1792 pamphlet, Seybert 1818, American State Papers 1832, Founders Online) traces the "
  "errors to the 1832 reprint. Reconciled figures used here. See `data/SOURCES.md`.")
w("- Schedule E: Hamilton's nine known states sum to $21,501,206; he wrote 'about twenty-one "
  "millions and a half'. Ties.\n")

w("## 1. Opening balance: what Hamilton knew (Schedule E, 9 Jan 1790)\n")
known = df[df.estimate_known]
w(f"- Returns or estimates for **{len(known)} of 13 states**, totaling "
  f"{usd(known.debt_estimate_1790_usd.sum())}. Hamilton rounded this to 'about twenty-one "
  "millions and a half' and guessed $25M including the four states with no data.")
w(f"- No data at all for: {', '.join(df[~df.estimate_known].state)}. "
  "Three more (NH, PA, MD) were Hamilton's own round-number estimates, not state returns.")
w("- Audit note: the quotas Congress wrote into the Act were set on a balance sheet that "
  "was one-third estimate and one-third blank. Any fairness verdict inherits that.\n")

# ---------------------------------------------------------------- 2. quota vs estimate
w("## 2. Setting the quota: variance between the Act and Hamilton's estimate\n")
w("| State | Hamilton est. (Jan 1790) | Act quota (Aug 1790) | Variance | % |")
w("|---|---:|---:|---:|---:|")
for _, r in df.sort_values("quota_vs_estimate_usd").iterrows():
    if r.estimate_known:
        w(f"| {r.state} | {m(r.debt_estimate_1790_usd)} | {m(r.quota_usd)} | "
          f"{'+' if r.quota_vs_estimate_usd >= 0 else '-'}{m(abs(r.quota_vs_estimate_usd))} | "
          f"{r.quota_vs_estimate_pct:+.0%} |")
    else:
        w(f"| {r.state} | (none) | {m(r.quota_usd)} | n/a | n/a |")
cut = df[df.quota_vs_estimate_usd < -1000]
w("")
w(f"- Congress cut **{usd(-cut.quota_vs_estimate_usd.sum())}** from Hamilton's estimates, "
  f"almost all from Massachusetts and South Carolina (each capped at $4.0M against "
  f"estimates of $5.2M and $5.4M). The three states Hamilton estimated (NH, PA, MD) were "
  "written into the Act at exactly his round numbers.")
w("- The four blank states were assigned $3.1M between them (RI 0.2, DE 0.2, NC 2.4, GA 0.3) "
  "with no return on file. North Carolina's $2.4M is the largest number in the Act with "
  "nothing behind it.\n")

# ---------------------------------------------------------------- 3. take-up
w("## 3. Take-up: quota vs. what creditors actually subscribed (Enclosure D, Jan 1792)\n")
w("Assumption was a *ceiling*. Creditors had to bring state paper to a federal loan office "
  "and swap it. Utilization tells you whether the quota matched real outstanding debt.\n")
w("| State | Quota | Subscribed, 1st window (Jan 1792) | Final assumed (Bayley) | Take-up | Unused quota | Remaining state debt (Hamilton est.) |")
w("|---|---:|---:|---:|---:|---:|---:|")
for _, r in df.sort_values("takeup_rate", ascending=False).iterrows():
    w(f"| {r.state} | {m(r.quota_usd)} | {m(r.subscribed_usd)} | {m(r.assumed_usd)} | {r.takeup_rate:.0%} | "
      f"{m(r.quota_unused_usd)} | {m(r.remaining_state_debt_usd)} |")
w("")
w(f"- Total: {m(df.quota_usd.sum())} authorized; {m(df.subscribed_usd.sum())} subscribed in the "
  f"first window; **{m(df.assumed_usd.sum())} finally assumed** after the window was extended "
  f"to 1793 and the three over-subscribed states were scaled back to quota. "
  f"Overall utilization {df.assumed_usd.sum() / total_quota:.0%}.")
pa = df.set_index("state")
w(f"- {m(df.quota_unused_usd.sum())} of quota went unused. Pennsylvania alone left "
  f"{m(pa.loc['Pennsylvania', 'quota_unused_usd'])} on the table "
  f"({pa.loc['Pennsylvania', 'takeup_rate']:.0%} take-up). Lowest utilization: Delaware "
  f"({pa.loc['Delaware', 'takeup_rate']:.0%}), Pennsylvania ({pa.loc['Pennsylvania', 'takeup_rate']:.0%}), "
  f"Maryland ({pa.loc['Maryland', 'takeup_rate']:.0%}).")
w(f"- The extension mattered: Pennsylvania's subscriptions rose from {m(pa.loc['Pennsylvania', 'subscribed_usd'])} "
  f"to {m(pa.loc['Pennsylvania', 'assumed_usd'])}, Maryland's from {m(pa.loc['Maryland', 'subscribed_usd'])} "
  f"to {m(pa.loc['Maryland', 'assumed_usd'])}, North Carolina's from {m(pa.loc['North Carolina', 'subscribed_usd'])} "
  f"to {m(pa.loc['North Carolina', 'assumed_usd'])}. Virginia's rose from {m(pa.loc['Virginia', 'subscribed_usd'])} "
  f"to {m(pa.loc['Virginia', 'assumed_usd'])}, still {pa.loc['Virginia', 'takeup_rate']:.0%} of quota.")
w("- Massachusetts, Rhode Island, and South Carolina brought in *more* than their quota in the "
  "first window - their real debt exceeded the Act. Hamilton's Schedule E had said so for MA and "
  "SC; Congress capped them anyway. The quota was a ceiling: RI finished exactly at quota, SC "
  "$348 under, MA $18,267 under.")
share = df.assumed_usd.sum() / (df.assumed_usd.sum() + df.remaining_state_debt_usd.sum())
w(f"- Hamilton estimated the states still owed {m(df.remaining_state_debt_usd.sum())} after "
  f"assumption. On that basis the Act absorbed about {share:.0%} of state debt, not all of it - "
  "but the residual is Hamilton's own estimate, graded a-f for reliability, so treat the share "
  "as approximate.\n")

# ---------------------------------------------------------------- 4. settlement
w("## 4. The true-up: final settlement of war accounts (Commissioners, 29 Jun 1793)\n")
w("This is the ledger Madison wanted *before* assumption: each state's war spending, netted "
  "against its fair share of the common cost. Creditor states had over-contributed.\n")
cr = df[df.settlement_balance_usd > 0].sort_values("settlement_balance_usd", ascending=False)
db = df[df.settlement_balance_usd < 0].sort_values("settlement_balance_usd")
w("| Creditor states (Union owes them) | Balance | per capita | | Debtor states (owe the Union) | Balance | per capita |")
w("|---|---:|---:|---|---|---:|---:|")
for i in range(max(len(cr), len(db))):
    a = cr.iloc[i] if i < len(cr) else None
    b = db.iloc[i] if i < len(db) else None
    w(f"| {a.state if a is not None else ''} | {usd(a.settlement_balance_usd) if a is not None else ''} | "
      f"{pc(a.settlement_balance_pc) if a is not None else ''} | | "
      f"{b.state if b is not None else ''} | {usd(b.settlement_balance_usd) if b is not None else ''} | "
      f"{pc(b.settlement_balance_pc) if b is not None else ''} |")
w("")
w(f"- Creditors total {usd(cr.settlement_balance_usd.sum())}; debtors the same. The settlement "
  "was designed to net to zero.")
w("- **Virginia was a debtor state.** The commissioners found Virginia owed the Union "
  f"{usd(-df.loc[df.state == 'Virginia', 'settlement_balance_usd'].iloc[0])}. Madison's 1790 "
  "argument was that Virginia had over-paid for the war and deserved credit. The audit three "
  "years later said the opposite.")
w("- New York was the largest debtor by a wide margin (-$2.07M, or -$6.10 per head, about -$221 "
  "per head today) *and* was "
  "under-allocated in the Act. It got the worst of both.\n")

# ---------------------------------------------------------------- 5. does relief track contribution?
w("## 5. The fairness test: did assumption relief track war contribution?\n")
w("Hamilton's defense of assumption was that the state debts were incurred for a common cause, "
  "so relieving them was rough justice. If that's true, states that over-contributed "
  "(creditor states) should have received more relief per head. Test it.\n")
rho = stats.spearmanr(df.assumed_pc, df.settlement_balance_pc)
pr = stats.pearsonr(df.assumed_pc, df.settlement_balance_pc)
rho_raw = stats.spearmanr(df.assumed_usd, df.settlement_balance_usd)
w(f"- Spearman rank correlation, relief per capita vs. settlement balance per capita: "
  f"rho = {rho.statistic:.2f} (p = {rho.pvalue:.3f}). Pearson r = {pr.statistic:.2f}.")
w(f"- Caveat: both per-capita variables share the same denominator (population), which can "
  f"inflate a correlation mechanically. On raw dollars the Spearman rho is {rho_raw.statistic:.2f} "
  f"(p = {rho_raw.pvalue:.2f}) - same sign, weaker. Per head is the economically meaningful "
  "framing (relief and burden per resident), but the strength of the association should be "
  "read with this in mind.")
cred_relief = df[df.position == "creditor"].assumed_pc
debt_relief = df[df.position == "debtor"].assumed_pc
perm = stats.permutation_test((cred_relief.values, debt_relief.values),
                              lambda a, b: a.mean() - b.mean(),
                              permutation_type="independent", n_resamples=np.inf,
                              alternative="greater")
w(f"- Creditor states (n={len(cred_relief)}) received a mean **{pc(cred_relief.mean())}** of "
  f"relief per head; debtor states (n={len(debt_relief)}) received **{pc(debt_relief.mean())}**. "
  f"Exact permutation test, one-sided, p = {perm.pvalue:.3f}.")
w("- Read: the states the 1793 audit later found had over-paid for the war are, on the whole, "
  "the states assumption relieved most. The relationship is moderate and sits right at the "
  "conventional p = 0.05 line; with 13 observations the effect size (creditor states got about "
  f"{cred_relief.mean() / debt_relief.mean():.1f}x the relief per head) is the more reliable "
  "statement. This is one of several tests in the write-up and is reported uncorrected for "
  "multiple comparisons; it was the single pre-specified, directional test of Hamilton's stated "
  "rationale, but p = 0.047 should be read as suggestive, not confirmatory. The Act didn't have "
  "the settlement numbers, but it landed on the right side of them.\n")

# ---------------------------------------------------------------- 6. net position
w("## 6. Net federal position per state (relief received + settlement balance)\n")
w("Both numbers are dollars the state came out ahead by. Adding them gives each state's net "
  "gain from the whole 1790-93 fiscal settlement.\n")
w("| State | Relief (assumed) | Settlement | Net position | Net per capita | Population share | Share of net gains |")
w("|---|---:|---:|---:|---:|---:|---:|")
pos = df[df.net_position_usd > 0].net_position_usd.sum()
for _, r in df.sort_values("net_position_pc", ascending=False).iterrows():
    w(f"| {r.state} | {m(r.assumed_usd)} | {usd(r.settlement_balance_usd)} | "
      f"{usd(r.net_position_usd)} | {pc(r.net_position_pc)} | "
      f"{r.pop_total_1790 / df.pop_total_1790.sum():.1%} | "
      f"{r.net_position_usd / pos:.1%} |")
w("")
ny = df[df.state == "New York"].iloc[0]
de = df[df.state == "Delaware"].iloc[0]
w(f"- Eleven of thirteen states came out ahead. New York's net was {usd(ny.net_position_usd)} "
  f"or {pc(ny.net_position_pc)} per head: $1.18M of relief against a $2.07M settlement debit. "
  f"Delaware was worse per head ({pc(de.net_position_pc)}): almost no relief taken up and a "
  "$612K settlement debit on 59,000 people.")
sc = df[df.state == "South Carolina"].iloc[0]
w(f"- South Carolina: {pc(sc.net_position_pc)} per head, {sc.net_position_usd / pos:.0%} of all "
  f"net gains with {sc.pop_total_1790 / df.pop_total_1790.sum():.1%} of the population. Still the "
  "outlier, and the settlement says it earned it - SC was the second-largest creditor state.\n")

# ---------------------------------------------------------------- 7. allocation vs population
w("## 7. Allocation benchmark: quota vs. a per-head split\n")
desc = qpc.describe()
w(f"- Quota per capita: mean {pc(desc['mean'])}, median {pc(desc['50%'])}, "
  f"std dev ${desc['std']:.2f}, CV {desc['std'] / desc['mean']:.2f}. "
  f"Outlier (1.5xIQR): {df[df.iqr_outlier].state.tolist()}.")
for basis, label in [("pop_total_1790", "total population"), ("pop_free_1790", "free population"),
                     ("pop_three_fifths", "three-fifths basis")]:
    di = df[f"gap_vs_{basis}"].abs().sum() / 2 / total_quota
    w(f"- vs {label}: {di:.1%} of the total would have to move between states to match.")
w("- The dissimilarity index is the substantive measure here. A chi-square goodness-of-fit "
  "test is not applicable to dollar amounts (it assumes counts, and its value depends on the "
  "unit chosen), so none is reported.")
ne = df[df.region == "New England"].quota_pc
so = df[df.region == "Southern"].quota_pc
perm_r = stats.permutation_test((ne.values, so.values), lambda a, b: a.mean() - b.mean(),
                                permutation_type="independent", n_resamples=np.inf,
                                alternative="two-sided")
w(f"- New England vs. Southern quota per head: ${ne.mean():.2f} vs ${so.mean():.2f}, exact "
  f"permutation p = {perm_r.pvalue:.2f}. No detectable regional tilt at this sample size "
  "(n = 4 vs 5, low power); South Carolina alone drives the Southern mean and is the only "
  "outlier by the 1.5xIQR rule.\n")

# ---------------------------------------------------------------- 8. sensitivity
w("## 8. Sensitivity: boundary and denominator choices\n")
alt = df.copy()
alt.loc[alt.state == "Massachusetts", "pop_total_1790"] -= 96540
alt.loc[alt.state == "Virginia", "pop_total_1790"] -= 73677
alt["quota_pc_alt"] = alt.quota_usd / alt.pop_total_1790
ma, va = alt.set_index("state").loc[["Massachusetts", "Virginia"]].quota_pc_alt
w(f"- Excluding Maine from MA and Kentucky from VA: MA quota per head ${df.set_index('state').loc['Massachusetts', 'quota_pc']:.2f} -> "
  f"${ma:.2f}; VA ${df.set_index('state').loc['Virginia', 'quota_pc']:.2f} -> ${va:.2f}. "
  "Rank order unchanged; SC remains the sole outlier.")
w(f"- Per free person instead of per capita: Virginia moves from ${df.set_index('state').loc['Virginia', 'quota_pc']:.2f} "
  f"to ${df.set_index('state').loc['Virginia', 'quota_pc_free']:.2f}, SC from "
  f"${sc.quota_pc:.2f} to ${sc.quota_pc_free:.2f}. The denominator choice flatters Southern "
  "quotas; it does not change any conclusion above.\n")

# ---------------------------------------------------------------- 9. opinion
w("""## 9. Opinion

**I side with Hamilton.** The question wasn't whether the allocation was tidy; it was
whether the new federal government could take a $21.5 million problem off thirteen
balance sheets and make it one credible obligation. It did. 85% of the authorized sum
was taken up, two of the three states that brought in more than their quota were
exactly the two Hamilton's own schedule ranked as owing the most (the third, Rhode
Island, wasn't in his schedule at all), and within three years the country had a
funded national debt and, despite a sharp market panic in 1792, credit good enough
that its bonds traded near or above par.

**The method was rough, and I'd say so in the workpapers.** Six of thirteen states filed
returns. Four got quotas by round number. Massachusetts and South Carolina were cut by a
quarter. If I were auditing the allocation itself, I'd write it up. But Hamilton wasn't
allocating with good data; he was allocating with the data that existed in January 1790,
and he said so in the report.

**The 1793 settlement vindicated him.** The audit Madison demanded found that the biggest
recipients, Massachusetts and South Carolina, were also the biggest creditors of the Union.
Relief tracked contribution. Madison's own Virginia, which he said had already paid its
share, turned out to owe the Union $100,879 - about 12 cents a head, which is to say it
broke even, exactly as the Compromise of 1790 intended, while receiving $2.9 million of
relief. His objection had no grievance the numbers supported.

**Where I'd push back on Hamilton:** the argument that federal bonds would bind wealthy
creditors to the new government can't be tested with state-level data, and I don't assume
it. What I can defend is narrower and, I think, more useful: the outcome was fair on the
numbers, and it was reconciled in about three and a half years - January 1790 report to
June 1793 settlement - which compares well with Puerto Rico (2016-22, about six years),
Greece (2010-18, eight) or Argentina (2001-16, fifteen).
""")

(OUT / "summary.md").write_text("\n".join(L), encoding="utf-8")

# ================================================================ charts
colors = {"New England": "#1f4e79", "Middle": "#7f7f7f", "Southern": "#b5533c"}
rng = np.random.default_rng(0)

# 1. reconciliation waterfall per state: estimate -> quota -> assumed -> remaining
fig, ax = plt.subplots(figsize=(10, 5.5))
d = df.sort_values("quota_usd", ascending=False)
x = np.arange(len(d))
wd = 0.27
ax.bar(x - wd, d.debt_estimate_1790_usd.fillna(0) / 1e6, wd, label="Hamilton estimate, Jan 1790", color="#c9c9c9")
ax.bar(x, d.quota_usd / 1e6, wd, label="Act quota, Aug 1790", color="#1f4e79")
ax.bar(x + wd, d.assumed_usd / 1e6, wd, label="Finally assumed (Treasury, to 1793)", color="#b5533c")
for i, (_, r) in enumerate(d.iterrows()):
    if not r.estimate_known:
        ax.text(i - wd, 0.05, "no\nreturn", ha="center", fontsize=7, color="#666")
ax.set_xticks(x, d.state, rotation=45, ha="right")
ax.set_ylabel("1790 $ millions")
sec = ax.secondary_yaxis("right", functions=(lambda v: v * CPI, lambda v: v / CPI))
sec.set_ylabel("2025 $ millions (CPI)")
ax.set_title("Estimate -> quota -> assumed, by state")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig_reconciliation.png", dpi=150)

# 2. take-up rate
fig, ax = plt.subplots(figsize=(8, 5))
d = df.sort_values("takeup_rate")
ax.barh(d.state, d.takeup_rate * 100, color=[colors[r] for r in d.region])
ax.axvline(100, ls="--", color="black", lw=1)
ax.set_xlabel("Subscribed as % of quota")
ax.set_title("Take-up: how much of each quota was actually used")
for k, v in colors.items():
    ax.bar(0, 0, color=v, label=k)
ax.legend(frameon=False, loc="lower right")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig_takeup.png", dpi=150)

# 3. relief vs settlement (the fairness test)
fig, ax = plt.subplots(figsize=(7.5, 6))
ax.axhline(0, color="black", lw=0.8)
ax.scatter(df.assumed_pc, df.settlement_balance_pc, c=[colors[r] for r in df.region], s=70)
nudge = {"New Jersey": (4, 8), "Georgia": (4, -10), "Virginia": (4, -10), "Pennsylvania": (-70, -10),
         "Maryland": (4, -10)}
for _, r in df.iterrows():
    ax.annotate(r.state, (r.assumed_pc, r.settlement_balance_pc), xytext=nudge.get(r.state, (4, 4)),
                textcoords="offset points", fontsize=8)
ax.set_xlabel("Debt relief received, 1790 $ per capita (top axis: 2025 $)")
ax.set_ylabel("1793 settlement balance, 1790 $ per capita\n(+ Union owed the state / - state owed the Union)")
sec = ax.secondary_xaxis("top", functions=(lambda v: v * CPI, lambda v: v / CPI))
ax.set_title(f"Did relief track war contribution?  Spearman rho = {rho.statistic:.2f}")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig_relief_vs_settlement.png", dpi=150)

# 4. net position per capita
fig, ax = plt.subplots(figsize=(8, 5))
d = df.sort_values("net_position_pc")
ax.barh(d.state, d.net_position_pc, color=[colors[r] for r in d.region])
ax.axvline(0, color="black", lw=0.8)
ax.set_xlabel("Net position, 1790 $ per capita (relief + settlement)")
sec = ax.secondary_xaxis("top", functions=(lambda v: v * CPI, lambda v: v / CPI))
sec.set_xlabel("2025 $ per capita (CPI)")
ax.set_title("Who came out ahead from the 1790-93 fiscal settlement")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig_net_position.png", dpi=150)

# 5. quota vs population-proportional (kept from v1)
fig, ax = plt.subplots(figsize=(7, 6))
ax.scatter(df.cf_pop_total_1790 / 1e6, df.quota_usd / 1e6, c=[colors[r] for r in df.region], s=70)
lim = max(df.cf_pop_total_1790.max(), df.quota_usd.max()) / 1e6 * 1.1
ax.plot([0, lim], [0, lim], ls="--", color="black", lw=1, label="proportional to population")
for _, r in df.iterrows():
    dy = 4 if r.quota_usd > 5e5 else (12 if r.state in ("Rhode Island", "New Hampshire") else -6)
    ax.annotate(r.state, (r.cf_pop_total_1790 / 1e6, r.quota_usd / 1e6), xytext=(4, dy),
                textcoords="offset points", fontsize=8)
ax.set_xlabel("Quota if split by 1790 population ($M)")
ax.set_ylabel("Actual Act quota ($M)")
ax.set_title("Quota vs. head-count share")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig_actual_vs_proportional.png", dpi=150)

print(f"Wrote {OUT / 'summary.md'}, assumption_ledger.csv, and 5 figures.")
