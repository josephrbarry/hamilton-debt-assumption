# Data sources

## assumed_authorized_usd
"An Act making provision for the Debt of the United States" (Funding Act of 1790),
1 Stat. 138, approved August 4, 1790, Section 14. The section names the maximum
amount of each state's debt the federal government would assume.
Total: $21,500,000. Only about $18.3M was ultimately subscribed - not every state
filled its quota - so this column is the *authorized ceiling*, not cash paid.
- Text: https://www.govinfo.gov/content/pkg/STATUTE-1/pdf/STATUTE-1-Pg138.pdf
  (Statutes at Large, vol. 1, pp. 138-144; sec. 14 on p. 142). The Library of Congress
  copy at loc.gov/law/help/statutes-at-large/1st-congress/c1.pdf sits behind a
  bot-check and may not open from a script. Section 14 is also reproduced in the
  Wikipedia article "Funding Act of 1790", which is where the figures were first read.

## pop_total_1790, pop_enslaved_1790
"Return of the Whole Number of Persons within the Several Districts of the
United States" (First Census, 1790). Authoritative publication, U.S. Census Bureau:
https://www.census.gov/library/publications/1793/dec/number-of-persons.html
Figures were first read from the Wikipedia article "1790 United States census",
which reproduces the Census Bureau return, and then verified against the Census
Bureau publication in the independent data audit. All thirteen matched.

Boundary decisions (the debts belonged to the states as they existed in 1790):
- Massachusetts includes the District of Maine (96,540, no enslaved persons).
- Virginia includes the Kentucky District (73,677 total, 12,430 enslaved).
  Kentucky became a state in 1792.
- Vermont (85,539) is excluded: not a state until 1791 and received no assumption.

## region
Conventional grouping used in the 1790 congressional debate:
New England = NH, MA, RI, CT; Middle = NY, NJ, PA, DE; Southern = MD, VA, NC, SC, GA.

## hamilton_1790_schedule_e.csv - what Hamilton knew when he proposed assumption
Schedule E, "Abstract of the Public Debt of the States," enclosed with the
Report Relative to a Provision for the Support of Public Credit, 9 Jan 1790.
https://founders.archives.gov/documents/Hamilton/01-06-02-0076-0002-0006
Six states sent returns (MA, CT, NY, NJ, VA, SC); Hamilton estimated three
(NH, PA, MD) and had nothing for RI, DE, NC, GA. He put the six-plus-three total
at "about twenty-one millions and a half" and guessed $25M for everything.
Dollar conversions are his (e.g. MA at 6s/dollar, NY at 8s, SC at 4s 8d).

## subscriptions_1792.csv - what creditors actually turned in
Enclosure D, "Statement of Subscriptions to the Loan payable in Certificates or
Notes issued by the respective States," Treasury Department, 25 Jan 1792, issued
under Hamilton as an enclosure to his Report on the Public Debt and Loans (23 Jan
1792); the statement itself was prepared in the Register's office (Joseph Nourse),
as was usual for Treasury tabular statements.
https://founders.archives.gov/documents/Hamilton/01-10-02-0124-0005
Covers the first subscription window, 1 Oct 1790 - 30 Sep 1791. Three states
(MA, RI, SC) subscribed more than their quota in this window; the quota was a
ceiling, so none received more than it. Final amounts (Bayley): RI exactly at
quota, SC $348 under, MA $18,267 under. The window was extended by Act of
8 May 1792 to 1 March 1793; the final assumed total was $18,271,786.47.
"Remaining state debt" is Hamilton's estimate of what the states still owed
after assumption, with his own letter-coded reliability grades (a-f).

## settlement_1793.csv - the final accounting of who paid for the war
Report of the Commissioners for Settling Accounts Between the United States and
the Individual States to George Washington, 29 June 1793.
https://founders.archives.gov/documents/Washington/05-13-02-0110
Positive = creditor state (the Union owed it money for war expenses beyond its
fair share). Negative = debtor state. Interest computed to 31 Dec 1789. Totals:
creditors $3,517,584, debtors $3,517,584 (the settlement nets to zero by design).

### Footing note on Enclosure D (found while tying out the table)
As published on Founders Online, the subscribed column sums to $17,798,186.21, not the
$18,328,186.21 the document states. Tying each row (quota - subscribed = unsubscribed,
or subscribed - quota = over-subscribed):
- North Carolina: printed $1,166,355.57 subscribed vs $733,644.43 unsubscribed against a
  $2,400,000 quota. These only reconcile if subscribed = $1,666,355.57 ($500,000 dropped).
- Massachusetts: printed $4,447,013.81 subscribed vs $477,013.81 over-subscribed against a
  $4,000,000 quota. These only reconcile if subscribed = $4,477,013.81 ($30,000 dropped).
  An earlier pass of this project corrected the over-subscribed line instead and concluded
  the Treasury had carried a $30,000 error into its total; that was wrong (see below).
- Maryland: printed $299,225.40 subscribed vs $500,744.60 unsubscribed against an $800,000
  quota; reconciles only if unsubscribed = $500,774.60 ($30 dropped).
- Reconciliation: with those three cells corrected, the subscribed column sums to
  $18,328,186.21, the over-subscribed column to $1,255,851.82 and the unsubscribed column to
  $4,427,665.61 - each exactly the total the document prints. The Treasury's arithmetic was
  right; the published cells are what is wrong. This file uses the reconciled figures.
- Provenance of the errors (checked 19 Sep 2026 against four witnesses): the 1792 Childs &
  Swaine pamphlet printing (Evans / TCP N19158, p. 15), Adam Seybert, *Statistical Annals*
  (1818), p. 726, *American State Papers: Finance* vol. 1 (1832), and the Founders Online
  transcription. Each printing has its own slips (the pamphlet keys MA as 4,177,013.81 and
  is $2 out in the unsubscribed total; Seybert has a $60 slip in Virginia), but the $500,000
  NC, $30,000 MA and $30 MD errors first appear in the 1832 *American State Papers* and were
  carried into Founders Online from there. No published source was found that notes them.

## assumed_final_bayley.csv - the final assumed amount per state
Rafael A. Bayley, *History of the National Loans of the United States from July 4,
1776, to June 30, 1880* (U.S. Treasury Department, 1881), p. 33, "taken from the
official reports." Covers the extended subscription window (to 1 March 1793).
Total $18,271,786.47. Scanned copies: https://archive.org/details/cu31924030228245
and https://archive.org/details/nationalloansun00treagoog. Three figures (NY, DE, SC)
were partly illegible in OCR; the digits used are the ones that appear in both scans
AND make the column foot exactly to Bayley's printed total.

## inflation.csv - converting 1790 dollars to 2025 dollars
- CPI: MeasuringWorth, https://www.measuringworth.com/calculators/uscompare/
  $1 (1790) = $36.30 (2025). Standard academic series; reaches back to 1774.
- Federal anchor: Federal Reserve Bank of Minneapolis, CPI 1800- table,
  https://www.minneapolisfed.org/about-us/monetary-policy/inflation-calculator/consumer-price-index-1800-
  1800 = 51, 2025 = 967.5 (1967=100) -> 19x from 1800. No 1790 value published.
- Economic share: MeasuringWorth, 159,000x. Use this for "how big was it" questions:
  $21.5M was about 11% of 1790 GDP (~$193M). 1790 GDP is a modern reconstruction
  (no national accounts existed), so treat the share as an order of magnitude.
Note on "inflation at the time": all figures in these documents are already in
specie (hard-money) dollars. Continental paper was pegged at 40:1 to specie by
Congress (18 March 1780) for redemption, had fallen to roughly 100:1 or worse in
the market by early 1781, and effectively stopped circulating that year. The state
certificates assumed here were specie-denominated, so no paper-money deflator applies.
