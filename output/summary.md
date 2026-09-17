# Hamilton's 1790 Debt Assumption - an accountant's reconciliation

Every figure below is from a document Hamilton wrote or received. See `data/SOURCES.md`.

**Dollars are shown as 1790 $ [2025 $ in brackets]**, converted at 36.3x by CPI (MeasuringWorth; the Federal Reserve's series starts in 1800 and gives ~19x from that year). Negatives are in parentheses. CPI understates the scale of these sums: the $21.5M authorized was about 11% of 1790 GDP (a modern reconstruction, so an order of magnitude); the same share of the 2025 economy is $3.4 trillion.

## 0. Tie-out: do the source documents foot?

Before analyzing, each table was footed against its own printed totals.

- Funding Act quotas sum to $21,500,000 [$780,450,000] - ties to the Act's $21.5M.
- 1793 settlement: creditors $3,517,584 [$127,688,299], debtors $3,517,584 [$127,688,299] - ties to Jefferson's pencilled total of $3,517,584 and nets to zero.
- Enclosure D (1792 subscriptions): **does not foot as printed.** The subscribed column sums to $17,798,186 against a stated $18,328,186. Row-level tie-out (quota - subscribed = unsubscribed) isolates a $500,000 error in the North Carolina line; the reconciled figure $1,666,355.57 is used here. A second line error: Massachusetts's over-subscription is printed as $477,013.81 but $4,447,013.81 less the $4,000,000 quota is $447,013.81 - $30,000 high. That error was carried into the printed total, which is why the reconciled column ($18,298,186) is $30,000 below it. A $30 Maryland difference is immaterial. Both errors are in single printed lines, not in the Treasury's arithmetic. See `data/SOURCES.md`.
- Schedule E: Hamilton's nine known states sum to $21,501,206; he wrote 'about twenty-one millions and a half'. Ties.

## 1. Opening balance: what Hamilton knew (Schedule E, 9 Jan 1790)

- Returns or estimates for **9 of 13 states**, totaling $21,501,206 [$780,493,764]. Hamilton rounded this to 'about twenty-one millions and a half' and guessed $25M including the four states with no data.
- No data at all for: North Carolina, Georgia, Delaware, Rhode Island. Three more (NH, PA, MD) were Hamilton's own round-number estimates, not state returns.
- Audit note: the quotas Congress wrote into the Act were set on a balance sheet that was one-third estimate and one-third blank. Any fairness verdict inherits that.

## 2. Setting the quota: variance between the Act and Hamilton's estimate

| State | Hamilton est. (Jan 1790) | Act quota (Aug 1790) | Variance | % |
|---|---:|---:|---:|---:|
| South Carolina | 5.39M [196M] | 4.00M [145M] | -1.39M [50M] | -26% |
| Massachusetts | 5.23M [190M] | 4.00M [145M] | -1.23M [45M] | -23% |
| Connecticut | 1.95M [71M] | 1.60M [58M] | -0.35M [13M] | -18% |
| Virginia | 3.68M [134M] | 3.50M [127M] | -0.18M [7M] | -5% |
| Pennsylvania | 2.20M [80M] | 2.20M [80M] | +0.00M [0M] | +0% |
| Maryland | 0.80M [29M] | 0.80M [29M] | +0.00M [0M] | +0% |
| New Hampshire | 0.30M [11M] | 0.30M [11M] | +0.00M [0M] | +0% |
| New Jersey | 0.79M [29M] | 0.80M [29M] | +0.01M [0M] | +1% |
| New York | 1.17M [42M] | 1.20M [44M] | +0.03M [1M] | +3% |
| North Carolina | (none) | 2.40M [87M] | n/a | n/a |
| Georgia | (none) | 0.30M [11M] | n/a | n/a |
| Delaware | (none) | 0.20M [7M] | n/a | n/a |
| Rhode Island | (none) | 0.20M [7M] | n/a | n/a |

- Congress cut **$3,144,950 [$114,161,674]** from Hamilton's estimates, almost all from Massachusetts and South Carolina (each capped at $4.0M against estimates of $5.2M and $5.4M). The three states Hamilton estimated (NH, PA, MD) were written into the Act at exactly his round numbers.
- The four blank states were assigned $3.1M between them (RI 0.2, DE 0.2, NC 2.4, GA 0.3) with no return on file. North Carolina's $2.4M is the largest number in the Act with nothing behind it.

## 3. Take-up: quota vs. what creditors actually subscribed (Enclosure D, Jan 1792)

Assumption was a *ceiling*. Creditors had to bring state paper to a federal loan office and swap it. Utilization tells you whether the quota matched real outstanding debt.

| State | Quota | Subscribed, 1st window (Jan 1792) | Final assumed (Bayley) | Take-up | Unused quota | Remaining state debt (Hamilton est.) |
|---|---:|---:|---:|---:|---:|---:|
| Connecticut | 1.60M [58M] | 1.46M [53M] | 1.60M [58M] | 100% | 0.00M [0M] | 0.46M [17M] |
| Rhode Island | 0.20M [7M] | 0.34M [12M] | 0.20M [7M] | 100% | 0.00M [0M] | 0.35M [13M] |
| South Carolina | 4.00M [145M] | 4.63M [168M] | 4.00M [145M] | 100% | 0.00M [0M] | 1.97M [71M] |
| Massachusetts | 4.00M [145M] | 4.45M [161M] | 3.98M [145M] | 100% | 0.02M [1M] | 1.84M [67M] |
| New York | 1.20M [44M] | 1.03M [37M] | 1.18M [43M] | 99% | 0.02M [1M] | 0.20M [7M] |
| New Hampshire | 0.30M [11M] | 0.24M [9M] | 0.28M [10M] | 94% | 0.02M [1M] | 0.10M [4M] |
| New Jersey | 0.80M [29M] | 0.60M [22M] | 0.70M [25M] | 87% | 0.10M [4M] | 0.21M [8M] |
| Virginia | 3.50M [127M] | 2.55M [93M] | 2.93M [107M] | 84% | 0.57M [21M] | 1.17M [43M] |
| Georgia | 0.30M [11M] | 0.30M [11M] | 0.25M [9M] | 82% | 0.05M [2M] | 0.40M [15M] |
| North Carolina | 2.40M [87M] | 1.67M [60M] | 1.79M [65M] | 75% | 0.61M [22M] | 0.71M [26M] |
| Maryland | 0.80M [29M] | 0.30M [11M] | 0.52M [19M] | 65% | 0.28M [10M] | 0.43M [16M] |
| Pennsylvania | 2.20M [80M] | 0.68M [25M] | 0.78M [28M] | 35% | 1.42M [52M] | 0.50M [18M] |
| Delaware | 0.20M [7M] | 0.05M [2M] | 0.06M [2M] | 30% | 0.14M [5M] | 0.00M [0M] |

- Total: 21.50M [780M] authorized; 18.30M [664M] subscribed in the first window; **18.27M [663M] finally assumed** after the window was extended to 1793 and the three over-subscribed states were scaled back to quota. Overall utilization 85%.
- 3.23M [117M] of quota went unused. Pennsylvania alone left 1.42M [52M] on the table (35% take-up). Lowest utilization: Delaware (30%), Pennsylvania (35%), Maryland (65%).
- The extension mattered: Pennsylvania's subscriptions rose from 0.68M [25M] to 0.78M [28M], Maryland's from 0.30M [11M] to 0.52M [19M], North Carolina's from 1.67M [60M] to 1.79M [65M]. Virginia's rose from 2.55M [93M] to 2.93M [107M], still 84% of quota.
- Massachusetts, Rhode Island, and South Carolina brought in *more* than their quota in the first window - their real debt exceeded the Act. Hamilton's Schedule E had said so for MA and SC; Congress capped them anyway. The quota was a ceiling: RI finished exactly at quota, SC $348 under, MA $18,267 under.
- Hamilton estimated the states still owed 8.33M [302M] after assumption. On that basis the Act absorbed about 69% of state debt, not all of it - but the residual is Hamilton's own estimate, graded a-f for reliability, so treat the share as approximate.

## 4. The true-up: final settlement of war accounts (Commissioners, 29 Jun 1793)

This is the ledger Madison wanted *before* assumption: each state's war spending, netted against its fair share of the common cost. Creditor states had over-contributed.

| Creditor states (Union owes them) | Balance | per capita | | Debtor states (owe the Union) | Balance | per capita |
|---|---:|---:|---|---|---:|---:|
| Massachusetts | $1,248,801 [$45,331,476] | $2.63 [$95] | | New York | ($2,074,846) [($75,316,910)] | ($6.10) [($221)] |
| South Carolina | $1,205,978 [$43,777,001] | $4.84 [$176] | | Delaware | ($612,428) [($22,231,136)] | ($10.36) [($376)] |
| Connecticut | $619,121 [$22,474,092] | $2.60 [$94] | | North Carolina | ($501,082) [($18,189,277)] | ($1.27) [($46)] |
| Rhode Island | $299,611 [$10,875,879] | $4.35 [$158] | | Maryland | ($151,640) [($5,504,532)] | ($0.47) [($17)] |
| New Hampshire | $75,055 [$2,724,496] | $0.53 [$19] | | Virginia | ($100,879) [($3,661,908)] | ($0.12) [($4)] |
| New Jersey | $49,030 [$1,779,789] | $0.27 [$10] | | Pennsylvania | ($76,709) [($2,784,537)] | ($0.18) [($6)] |
| Georgia | $19,988 [$725,564] | $0.24 [$9] | |  |  |  |

- Creditors total $3,517,584 [$127,688,299]; debtors the same. The settlement was designed to net to zero.
- **Virginia was a debtor state.** The commissioners found Virginia owed the Union $100,879 [$3,661,908]. Madison's 1790 argument was that Virginia had over-paid for the war and deserved credit. The audit three years later said the opposite.
- New York was the largest debtor by a wide margin (-$2.07M, or -$6.10 per head, about -$221 per head today) *and* was under-allocated in the Act. It got the worst of both.

## 5. The fairness test: did assumption relief track war contribution?

Hamilton's defense of assumption was that the state debts were incurred for a common cause, so relieving them was rough justice. If that's true, states that over-contributed (creditor states) should have received more relief per head. Test it.

- Spearman rank correlation, relief per capita vs. settlement balance per capita: rho = 0.55 (p = 0.052). Pearson r = 0.54.
- Caveat: both per-capita variables share the same denominator (population), which can inflate a correlation mechanically. On raw dollars the Spearman rho is 0.31 (p = 0.31) - same sign, weaker. Per head is the economically meaningful framing (relief and burden per resident), but the strength of the association should be read with this in mind.
- Creditor states (n=7) received a mean **$6.12 [$222]** of relief per head; debtor states (n=6) received **$2.67 [$97]**. Exact permutation test, one-sided, p = 0.047.
- Read: the states the 1793 audit later found had over-paid for the war are, on the whole, the states assumption relieved most. The relationship is moderate and sits right at the conventional p = 0.05 line; with 13 observations the effect size (creditor states got about 2.3x the relief per head) is the more reliable statement. This is one of several tests in the write-up and is reported uncorrected for multiple comparisons; it was the single pre-specified, directional test of Hamilton's stated rationale, but p = 0.047 should be read as suggestive, not confirmatory. The Act didn't have the settlement numbers, but it landed on the right side of them.

## 6. Net federal position per state (relief received + settlement balance)

Both numbers are dollars the state came out ahead by. Adding them gives each state's net gain from the whole 1790-93 fiscal settlement.

| State | Relief (assumed) | Settlement | Net position | Net per capita | Population share | Share of net gains |
|---|---:|---:|---:|---:|---:|---:|
| South Carolina | 4.00M [145M] | $1,205,978 [$43,777,001] | $5,205,630 [$188,964,359] | $20.90 [$759] | 6.5% | 26.4% |
| Massachusetts | 3.98M [145M] | $1,248,801 [$45,331,476] | $5,230,534 [$189,868,386] | $11.00 [$399] | 12.5% | 26.5% |
| Connecticut | 1.60M [58M] | $619,121 [$22,474,092] | $2,219,121 [$80,554,092] | $9.33 [$339] | 6.2% | 11.3% |
| Rhode Island | 0.20M [7M] | $299,611 [$10,875,879] | $499,611 [$18,135,879] | $7.26 [$264] | 1.8% | 2.5% |
| New Jersey | 0.70M [25M] | $49,030 [$1,779,789] | $744,233 [$27,015,647] | $4.04 [$147] | 4.8% | 3.8% |
| Virginia | 2.93M [107M] | ($100,879) [($3,661,908)] | $2,833,537 [$102,857,393] | $3.45 [$125] | 21.6% | 14.4% |
| North Carolina | 1.79M [65M] | ($501,082) [($18,189,277)] | $1,292,722 [$46,925,803] | $3.28 [$119] | 10.3% | 6.6% |
| Georgia | 0.25M [9M] | $19,988 [$725,564] | $266,019 [$9,656,480] | $3.22 [$117] | 2.2% | 1.3% |
| New Hampshire | 0.28M [10M] | $75,055 [$2,724,496] | $357,651 [$12,982,714] | $2.52 [$92] | 3.7% | 1.8% |
| Pennsylvania | 0.78M [28M] | ($76,709) [($2,784,537)] | $701,274 [$25,456,264] | $1.61 [$59] | 11.4% | 3.6% |
| Maryland | 0.52M [19M] | ($151,640) [($5,504,532)] | $365,851 [$13,280,394] | $1.14 [$42] | 8.4% | 1.9% |
| New York | 1.18M [43M] | ($2,074,846) [($75,316,910)] | ($891,129) [($32,347,994)] | ($2.62) [($95)] | 8.9% | -4.5% |
| Delaware | 0.06M [2M] | ($612,428) [($22,231,136)] | ($553,266) [($20,083,569)] | ($9.36) [($340)] | 1.6% | -2.8% |

- Eleven of thirteen states came out ahead. New York's net was ($891,129) [($32,347,994)] or ($2.62) [($95)] per head: $1.18M of relief against a $2.07M settlement debit. Delaware was worse per head (($9.36) [($340)]): almost no relief taken up and a $612K settlement debit on 59,000 people.
- South Carolina: $20.90 [$759] per head, 26% of all net gains with 6.5% of the population. Still the outlier, and the settlement says it earned it - SC was the second-largest creditor state.

## 7. Allocation benchmark: quota vs. a per-head split

- Quota per capita: mean $5.31 [$193], median $4.26 [$155], std dev $3.69, CV 0.70. Outlier (1.5xIQR): ['South Carolina'].
- vs total population: 20.2% of the total would have to move between states to match.
- vs free population: 19.1% of the total would have to move between states to match.
- vs three-fifths basis: 19.8% of the total would have to move between states to match.
- The dissimilarity index is the substantive measure here. A chi-square goodness-of-fit test is not applicable to dollar amounts (it assumes counts, and its value depends on the unit chosen), so none is reported.
- New England vs. Southern quota per head: $5.04 vs $6.51, exact permutation p = 0.78. No detectable regional tilt at this sample size (n = 4 vs 5, low power); South Carolina alone drives the Southern mean and is the only outlier by the 1.5xIQR rule.

## 8. Sensitivity: boundary and denominator choices

- Excluding Maine from MA and Kentucky from VA: MA quota per head $8.42 -> $10.56; VA $4.26 -> $4.68. Rank order unchanged; SC remains the sole outlier.
- Per free person instead of per capita: Virginia moves from $4.26 to $6.78, SC from $16.06 to $28.17. The denominator choice flatters Southern quotas; it does not change any conclusion above.

## 9. Opinion

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
