# Hamilton's 1790 Debt Assumption - analysis summary

Total authorized assumption: $21,500,000 across 13 states.

## Per-capita assumption (authorized $ / 1790 total population)

- Mean: $5.31   Median: $4.26   Std dev: $3.69
- Min: $2.11 (New Hampshire)   Max: $16.06 (South Carolina)
- Coefficient of variation: 0.70 (std dev as a fraction of the mean - a 'how unequal is this' number)
- Skew: 2.33

| State | Region | Assumed $ | Pop (1790) | $ per capita | $ per free person | z-score |
|---|---|---:|---:|---:|---:|---:|
| South Carolina | Southern | 4,000,000 | 249,073 | 16.06 | 28.17 | +2.91 |
| Massachusetts | New England | 4,000,000 | 475,327 | 8.42 | 8.42 | +0.84 |
| Connecticut | New England | 1,600,000 | 237,946 | 6.72 | 6.80 | +0.38 |
| North Carolina | Southern | 2,400,000 | 393,751 | 6.10 | 8.19 | +0.21 |
| Pennsylvania | Middle | 2,200,000 | 434,373 | 5.06 | 5.11 | -0.07 |
| New Jersey | Middle | 800,000 | 184,139 | 4.34 | 4.63 | -0.26 |
| Virginia | Southern | 3,500,000 | 821,287 | 4.26 | 6.78 | -0.28 |
| Georgia | Southern | 300,000 | 82,548 | 3.63 | 5.63 | -0.45 |
| New York | Middle | 1,200,000 | 340,120 | 3.53 | 3.76 | -0.48 |
| Delaware | Middle | 200,000 | 59,094 | 3.38 | 3.98 | -0.52 |
| Rhode Island | New England | 200,000 | 68,825 | 2.91 | 2.95 | -0.65 |
| Maryland | Southern | 800,000 | 319,728 | 2.50 | 3.69 | -0.76 |
| New Hampshire | New England | 300,000 | 141,885 | 2.11 | 2.12 | -0.87 |

IQR-rule outliers (1.5xIQR): ['South Carolina']. States with |z| > 1.5: ['South Carolina']

## Regional comparison: New England vs. Southern

- New England: n=4, mean $5.04, median $4.82
- Middle: n=4, mean $4.08, median $3.94
- Southern: n=5, mean $6.51, median $4.26

- Observed difference in means (NE - South): $-1.47
- Welch t-test: t = -0.51, p = 0.627
- Mann-Whitney U: U = 9, p = 0.905
- Exact permutation test (all 126 relabelings): p = 0.778

**Interpretation caveat.** These 13 states are the entire population of interest, not a sample from a larger one, so a p-value here answers a narrower question: 'if the regional labels were shuffled at random, how often would a gap this big appear?' With n=4 vs n=5 the tests have little power, so a non-significant result is weak evidence of 'no regional tilt', not proof of it. The effect size (the dollar gap) is the more honest headline.

## Allocation gap: actual quota vs. population-proportional quota

If the $21.5M had been split like congressional apportionment, each state's quota would be its population share x $21.5M. Positive gap = state got more than a per-head split would give it.

| State | Actual $ | If by total pop | Gap | If by free pop | Gap | If by 3/5 rule | Gap |
|---|---:|---:|---:|---:|---:|---:|---:|
| South Carolina | 4.00M | 1.41M | +2.59M | 0.98M | +3.02M | 1.26M | +2.74M |
| Massachusetts | 4.00M | 2.68M | +1.32M | 3.28M | +0.72M | 2.89M | +1.11M |
| Connecticut | 1.60M | 1.34M | +0.26M | 1.62M | -0.02M | 1.44M | +0.16M |
| North Carolina | 2.40M | 2.22M | +0.18M | 2.02M | +0.38M | 2.15M | +0.25M |
| Delaware | 0.20M | 0.33M | -0.13M | 0.35M | -0.15M | 0.34M | -0.14M |
| Georgia | 0.30M | 0.47M | -0.17M | 0.37M | -0.07M | 0.43M | -0.13M |
| Rhode Island | 0.20M | 0.39M | -0.19M | 0.47M | -0.27M | 0.42M | -0.22M |
| New Jersey | 0.80M | 1.04M | -0.24M | 1.19M | -0.39M | 1.09M | -0.29M |
| Pennsylvania | 2.20M | 2.45M | -0.25M | 2.97M | -0.77M | 2.64M | -0.44M |
| New Hampshire | 0.30M | 0.80M | -0.50M | 0.98M | -0.68M | 0.86M | -0.56M |
| New York | 1.20M | 1.92M | -0.72M | 2.20M | -1.00M | 2.02M | -0.82M |
| Maryland | 0.80M | 1.81M | -1.01M | 1.50M | -0.70M | 1.70M | -0.90M |
| Virginia | 3.50M | 4.64M | -1.14M | 3.56M | -0.06M | 4.26M | -0.76M |

- vs total population: chi2 = 72.0, p = 1.35e-10; 20.2% of the total would have to move between states to match this basis.
- vs free population: chi2 = 113.4, p = 1.28e-18; 19.1% of the total would have to move between states to match this basis.
- vs three-fifths basis: chi2 = 81.3, p = 2.31e-12; 19.8% of the total would have to move between states to match this basis.

The 'share that would have to move' figure (half the sum of absolute gaps, as a % of the total) is a dissimilarity index - the same idea used to measure how far a budget is from a benchmark allocation.

## Concentration

- Top 3 states by dollars (South Carolina, Massachusetts, Virginia) hold 53.5% of the assumption with 40.6% of the population.
- Spearman rank correlation, population vs. assumed $: rho = 0.85 (p = 0.000). Bigger states got more, but far from proportionally.
