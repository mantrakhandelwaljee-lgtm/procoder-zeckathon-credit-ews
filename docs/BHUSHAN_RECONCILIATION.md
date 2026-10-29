# Payment reconciliation and original FY2011 verification

29 October 2026. **The December 2013 payment-date assertion is now corroborated by contemporaneous trustee notices. Original FY2011 statement values have been reviewed for all four issuers. Exact settlement dates, first-default completeness and historical public-release timestamps remain unverified.**

This review improves the evidence; it does not clear the case for the primary backtest.

## Payment episodes: what is resolved

The trustee's January 2014 noncompliance notice, status as of 16 January, identifies unpaid quarterly interest due **31 December 2013** under the Bhushan Steel entry labelled INR500 crore. Its February notice, status as of 26 February, retains that due date and reports receipt of payment. The later September 2015 half-year report also records the December 2013 event and payment receipt.

The January notice separately identifies half-yearly interest due **1 January 2014** under an INR105 crore programme, a holder email dated 6 January and a trustee follow-up dated 7 January. Its subsequent-receipt footnote has no settlement date. Do not assume payment occurred by the notice's nominal status date merely because that footnote was later attached.

| Episode | Initial evidence | Cure evidence | Decision |
|---|---|---|---|
| INR500 crore programme, 31 December 2013 interest | January 2014 notice plus later full report | February 2014 status notice says holders received payment | Earliest payment failure documented in this review; exact settlement date unknown |
| INR105 crore programme, 1 January 2014 interest | January 2014 notice | Undated subsequent-receipt note | Separate subsequent failure; no invented cure date |
| INR500 crore programme, April date | Later reports conflict between April 2014 narrative and April 2015 due-date field | Unresolved | Retain source inconsistency; it cannot displace the earlier December event |
| INR175 crore programme, 26 August 2014 interest | Original September 2014 notice, PDF page 12 | Later half-year report, PDF page 15, records receipt | Subsequent failure; not the first documented event |

**Source-access qualification:** the January and February noncompliance notices were readable through indexed excerpts of the primary documents. Their direct PDF fetches returned rejected/non-PDF responses; they have not been represented as downloaded, hashed or visually reviewed originals. The source-review ledger distinguishes this from the original PDFs reviewed locally. Search-engine crawl/publication labels were not treated as historical upload timestamps.

Sources: [January noncompliance notice](https://www.axistrustee.in/pdf/Non-Compliance-with-the-Terms-Jan-14.pdf), [February noncompliance notice](https://www.axistrustee.in/pdf/ATSL-Non-Compliance-with-terms-of-Issue-Feb-14.pdf), [September 2015 half-year report](https://www.axistrustee.in/pdf/SEBI-Half-Yearly-Report-September-2015.pdf).

The INR500/105/175 crore labels identify trustee programme sizes. They are not unpaid coupon amounts, and they do not establish a unique ISIN or outstanding principal balance. The original trust deed, instrument-to-ISIN mapping, coupon schedule, holder statements and bank payment/value-date receipts have not been verified. No exact day count of delay is calculated.

The FY2014 CARO statement of no default does not nullify a specifically dated trustee record. A cured payment failure and a later clean position can coexist, but the precise reason for the auditor's wording is not established here. Record both sources rather than infer the auditor's intention.

**Endpoint status:** `earliest_documented_not_exhaustively_established`. This closes the question of whether the December 2013 date appears only in a much later retrospective table. It does not prove that no earlier bank or other debt-instrument payment failed. The primary engine still requires a verified first-default endpoint. Later cure, downgrade or CIRP dates do not replace the earlier payment failure under a first-delay target.

## Original FY2011 financials

The balance sheet, profit and loss, operating cash-flow statement and reserve/finance notes were reviewed from each issuer's original FY2011 consolidated report. The review adds **99 source-linked numerical and derived fields**, four gross-balance reconciliations and 42 original-versus-later comparisons. It is a single-researcher source review, not an independent second sign-off or verification of every note in each report.

Old Schedule VI statements net current liabilities and provisions against the asset side. Restore gross assets by adding those deducted amounts back to the printed net total. This is an arithmetic reconciliation, not a reconstruction of later current/non-current classifications.

All values below are INR crore:

| Issuer | Printed net balance total | Current liabilities + provisions deducted | Reconstructed gross assets | Original parent-attributable net profit | Original operating cash flow |
|---|---:|---:|---:|---:|---:|
| Bhushan Steel | 23,220.0315 | 2,105.7675 | 25,325.7990 | 1,007.3946 | 994.1987 |
| JSW Steel | 35,565.15 | 10,601.38 | 46,166.53 | 1,753.98 | 2,830.24 |
| Tata Steel | 101,722.16 | 33,760.98 | 135,483.14 | 8,982.69 | 6,462.91 |
| SAIL | 60,434.27 | 17,675.70 | 78,109.97 | 5,017.18 | 2,496.25 |

Gross assets reconcile to parent funds, separately reported equity-like items and all liabilities for all four issuers. Bhushan's separately presented translation reserve is retained in the equity reconciliation. Tata's perpetual securities, subsidiary warrants and minority interest are separately identified. SAIL's original deferred expenditure is not silently deleted from reported assets.

Original sources and PDF pages:

- [Bhushan FY2011](https://www.bseindia.com/bseplus/AnnualReport/500055/5000550311.pdf): balance 86, P&L 87, CFO 88, reserves 90; working-capital notes 94–95.
- [JSW FY2011](https://www.bseindia.com/bseplus/AnnualReport/500228/5002280311.pdf): balance 90, P&L 91, CFO 92, reserves 93, finance 96.
- [Tata FY2011](https://www.bseindia.com/bseplus/AnnualReport/500470/5004700311.pdf): balance 188, P&L 189, CFO 190, finance 192, reserves 194.
- [SAIL FY2011](https://www.bseindia.com/bseplus/AnnualReport/500113/5001130311.pdf): balance 95, P&L 96, CFO 97, reserves 98.

### Version differences that must survive the data pipeline

Compared with the FY2011 columns reproduced in FY2012 reports, reconstructed original gross assets differ by INR2.05 crore for JSW, INR5.09 crore for Tata and INR12.82 crore for SAIL. Original SAIL profit is INR5,017.18 crore; the later comparative is INR5,013.91 crore. The later figures are not backdated or substituted for the originals.

These are observed version or definition differences. The ledger does not automatically label every difference a restatement: consolidation scope, reclassification and accounting definitions require separate explanations. In particular, an old broad current-assets-and-advances bucket and a later current-only subtotal are not like-for-like quantities.

Finance charges also require care. JSW's original INR945.41 crore net charge equals INR1,056.94 crore before income offsets, less INR79.24 crore interest income and INR32.29 crore current-investment gains. Tata's INR3,426.67 crore interest less INR219.63 crore capitalised yields INR3,207.04 crore charged before income offsets; deducting INR437 crore offsets gives the reported INR2,770.04 crore net charge. Neither is replaced with a later comparative finance figure.

The original reports do not fully establish all current loan maturities, recoverability classifications, consistent operating-revenue/EBIT definitions and full earned-reserve mappings needed by the deployed model. The raw old-presentation buckets are retained, while canonical `current_assets` and `current_liabilities` stay missing. No full model score, Z-score or primary alert is emitted from these incomplete mappings. Partial verified ratios are available for inspection; accounting uncertainty is not turned into a fabricated exact value.

## Report availability: what is and is not verified

The official SEBI processing register, PDF page 21 row 243, records **22 February 2012** as the Bhushan rights draft filing date and **22 August 2012** as the observation date. The draft itself is dated 21 February 2012 and reproduces original FY2011 consolidated accounts, including the netted balance presentation. Thus the FY2011 version is corroborated in another regulatory source. This proves filing history, not the exact date when the full document became public.

Sources: [official SEBI processing register](https://www.sebi.gov.in/sebi_data/commondocs/jan-2020/Issues%20Obs%20Issued%20-%2024.01.2020_p.pdf), [draft offer](https://www.sebi.gov.in/sebi_data/attachdocs/1330081238429.pdf), [NSE copy](https://nsearchives.nseindia.com/corporates/offerdocument/rights/Bhushan_dfa_rights.pdf).

Additional archive checks are retained in `archive_availability_queries.json`:

- The queried BSE FY2011 URLs produced no capture, or nearest captures in 2019–2021. A missing archive capture does not prove a report was unavailable.
- The Internet Archive API reports a Tata FY2011 financials-index capture on 3 May 2012. The archived content request was rejected, so only capture metadata is retained; exact linked PDF contents/version were not verified. The current issuer index does link the original consolidated statements.
- Auditor signatures, AGM dates, file creation metadata and a regulator's receipt date are kept distinct from public dissemination. None is automatically promoted to an exact historical public timestamp.

**Availability decision: zero original FY2011 records clear the strict public-release gate.** For the documented 31 December 2013 payment event, the latest qualifying quarterly cutoffs are 31 December 2012 for four quarters and **31 December 2011 for eight quarters**. A February or May 2012 document cannot establish availability at that earlier eight-quarter cutoff even if its later public release were confirmed.

## What remains necessary

The next evidence must resolve specific gaps: original payment/settlement and instrument records, exclusion of earlier issuer defaults, an original exchange submission or public dissemination record before each cutoff, and contemporaneous current-maturity/recoverability mappings. A later comparative, current website download or assumed publication lag cannot substitute for that evidence.

No primary Indian recall, loss savings or successful lead-time claim is added. The benchmark model, split, calibration and threshold remain unchanged.

Run `python -m ews.reconcile_bhushan` to regenerate this review's data outputs, or `python run.py --test` for the complete build.

[Original field provenance](../results/india/bhushan-reconciliation/original_field_sources.csv) · [Gross balance checks](../results/india/bhushan-reconciliation/gross_balance_reconciliation.csv) · [Version comparison](../results/india/bhushan-reconciliation/original_vs_later_comparatives.csv) · [Payment episodes](../data/curated/reconciled_payment_episodes.csv) · [Availability decisions](../data/curated/fy2011_availability_review.csv) · [Status and remaining gaps](../results/india/bhushan-reconciliation/status.json)
