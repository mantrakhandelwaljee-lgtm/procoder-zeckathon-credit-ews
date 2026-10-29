# Evidence review and completion queue

The software and benchmark run, but the Indian submission is incomplete. Do not turn the extraction candidates into verified history without reviewing them.

The [Bhushan case dossier](BHUSHAN_CASE_DOSSIER.md) adds reviewed numerical examples and cutoff checks. It documents August 2014 payment failure and conflicting earlier retrospective assertions. First-default status remains unresolved. Its AGM availability assumptions and earned-reserve proxies are deliberately excluded from approved inputs; eight-quarter results require original FY2011 source mappings.

The [subsequent reconciliation](BHUSHAN_RECONCILIATION.md) now corroborates December 2013 using contemporaneous indexed trustee records, separates later cure reporting from actual settlement dates, and reviews four original FY2011 financial versions. Original current classifications and exact historical public release remain unresolved; a February 2012 regulatory filing cannot clear a December 2011 cutoff.

## Existing evidence

- `data/curated/documents.csv` and `bhushan_documents.csv`: combined inventory, currently 196 downloaded PDFs and 13 failed routes. Original URLs, local files, hashes, retrieval status and publication-status fields. A download date is not a historical publication date.
- `data/curated/financial_candidates.csv`: numerical candidates with original source lines, pages, accounting basis and units. Every row remains `requires_review`.
- `data/curated/statement_page_index.csv`: page index for balance sheets, income statements and cash-flow statements.
- `data/curated/pilot_reviewed_accounts.csv`: four issuers' FY2016 and comparative FY2015 financial values reviewed against source statements and notes. Publication timing remains unverified.
- `data/curated/pilot_field_sources.csv`: field-level provenance for that pilot, including earned-reserve reconstruction and calculated liabilities/EBIT.
- `data/curated/events.csv`: ten documented CIRP admission dates, five earlier payment-default records, and a separately identified ITNL technical payment delay.
- `data/curated/peer_matches.csv`: provisional matches. None is certified as a qualified non-default control solely because it appears here.
- `results/india/coverage_review_queue.csv`: company-by-company outstanding work.

## First priority: resolve event definitions

The trustee's October 2015 notice documents earlier payment failures for Alok, Amtek, Bhushan Steel, Era Infra and Jaypee Infratech. Do not use their later CIRP dates to claim that a warning after those defaults was early.

Era's May 2015 and Jaypee's June 2015 references are month intervals. Their first days are lower bounds, not invented exact default dates. Look for instruments, actual payment schedules, cure periods, earlier defaults and contemporaneous disclosure dates. Label the target consistently before evaluating a model.

The ITNL June 2018 one-day payment delay was treated as a technical event by ICRA because its paying-agent account was funded on the due date. It is not silently equated with a first bank-loan default or the parent's default.

## Second priority: verify availability and versions

For every input, locate the original exchange submission or equivalent public source. A dated exchange filing is stronger evidence than an auditor's signature. Distinguish issuer-stated filing dates from independently recorded exchange timestamps and document any residual uncertainty. A conservative, disclosed availability upper bound may be used in a sensitivity run; do not invent a quarter-end availability date.

Keep original financial versions. FY2015 figures reproduced in a FY2016 report are available from that FY2016 source, not automatically from FY2015. The ITNL FY2015 original and later comparative totals differ; retain separate versions rather than overwriting history.

## Third priority: complete accounting fields

Extract three pre-event annual periods plus enough earlier data for changes and eight-quarter cutoffs. Verify all 12 deployed features. Review current/non-current classification, minority interest, exceptional items, finance income, accumulated earned reserves and annual period length.

- Retained earnings: include documented accumulated earned reserves, excluding share premium and capital reserves. Do not substitute the entire reserves-and-surplus balance.
- Receivables: use the specified current trade-receivables definition, not a long-term receivables row.
- Borrowings and liabilities are different. For consolidated statements, minority interest is equity and is excluded from total liabilities.
- The pilot uses profit attributable to parent owners and parent equity, with group assets/liabilities. This is an explicit mapping limitation when transferring from anonymous Polish firms.
- Alok has 18-month periods. Reconstruct verified trailing twelve-month flows or mark affected scores unavailable; never pretend those are ordinary annual observations.
- For Beneish, verify COGS and SG&A classifications and continuing-operations income. For Piotroski, verify actual equity issuance and older beginning assets. Missing inputs must stay missing.
- The toll-road pilot's intangible/concession assets and deferred project liabilities differ from manufacturing businesses. An in-range feature value does not establish that the transferred model is applicable.

## Fourth priority: qualify controls

Verify historical listing, matching business mix/size and observed non-default outcomes over each target horizon. Three proposed controls have already been excluded: Jindal Steel & Power (default evidence), HCC (continuing default rating dating to 2012), and PNC (2015 IPO does not cover earlier cutoffs). Their replacements remain provisional. Steel-products comparators for Electrosteel are imperfect matches and need review.

## Approved input schema

To run the strict replay, create these two input files. The normal pipeline never creates them from unreviewed candidates.

### `data/curated/approved_population.csv`

Required columns:

`entity_id,role,sector,listed_from,observed_through,default_date,endpoint_status,qualification_status,qualification_evidence_ref,match_case_id,match_status,match_evidence_ref`

- `role`: `case` or `peer`; at least 10 cases and 30 distinct peers.
- `listed_from`: verified historical equity-listing start date.
- `observed_through`: date through which outcome status has been established.
- `default_date`: verified first-default date, or blank for a non-default control over its observation window. A peer later defaulting needs its actual date here.
- Case `endpoint_status`: `verified_first_default`. A CIRP date cannot pass this gate. Healthy peers require `verified_nondefault_horizon`; later-defaulting peers require `verified_first_default`.
- `sector` uses the same historically verified business classification for each case and its peers. Each peer names an existing `match_case_id`, has `match_status=verified` and a nonblank `match_evidence_ref`. Every case needs at least one documented match, in addition to the overall 30-peer minimum. Document size/business-mix suitability in that evidence.
- `qualification_evidence_ref` points to reviewed listing, endpoint and follow-up evidence. Dates must be valid ISO `YYYY-MM-DD`; malformed nonempty defaults are rejected. Listing must precede follow-up, and any default must fall within the observed listed window.
- `qualification_status`: `verified`, only after the above work is complete.

Retain event and qualification evidence in the source ledger. These status strings are attestations, not a replacement for evidence.

### `data/curated/approved_accounts.csv`

Required metadata:

`entity_id,period_end,period_months,public_available_at,verification_status,publication_status,accounting_mapping_status,source_document_id,source_url,source_sha256,source_pages,basis`

Numerical verification, publication verification and accounting-mapping status must all be `verified`. Exact daily public-availability evidence is required; a filing/signature/AGM assumption cannot pass this primary gate. Availability must be on or after period end. Annual period length must be explicitly 12 months. Same-issuer, same-period, same-publication-date duplicates are rejected. Include only one chosen accounting basis per issuer. Each record is a complete statement snapshot; missing individual items are not filled from a later version.

Required numeric fields for the deployed common model:

`total_assets,total_liabilities,current_assets,current_liabilities,equity,other_equity,retained_earnings,ebit,net_income,sales,inventory,receivables`

Use consistent units, twelve-month flows and documented definitions. `other_equity` explicitly records minority/hybrid/other equity excluded from parent equity; use a reviewed zero where absent. Gross assets must reconcile to liabilities + equity + other equity (tolerance: max 0.02 reported units or one part per million of assets). Asset and liability components must reconcile. All required values must be finite. Source URL and SHA-256 must match a downloaded document in the combined manifests; `source_pages` is a quoted CSV cell of comma-separated positive PDF page numbers, such as `"86,87,90"`. Evidence-status flags are attestations that still require human review. Add the M/F/Z inputs and field-source references separately. Keep all source pages and document hashes.

Run `python run.py --test`. If the approved inputs pass, primary rankings, quarterly metrics and lead outcomes are written under `results/india/primary/`. Known outputs from earlier primary runs are archived under `primary/superseded/` before every attempt; a missing or rejected input cannot leave stale current metrics. Input/model hashes are recorded on approved runs. Missing financials do not shrink the universe; an incomplete quarter is withheld. Unknown follow-up outcomes are censored rather than labeled healthy.

## Current retrieval exceptions

Some failed URL guesses are not missing economic years: Alok did not publish a separate ordinary FY2014 report because of its 18-month period. PNC's pre-IPO report route is no longer relevant to the control pool. The ITNL mirror with the FY2016 cover letter returned HTTP 403. The BSE annual report itself was downloaded; a mirrored letter's search snippet is not promoted to a verified exchange timestamp.

The remaining Era FY2015 route requires a company/exchange archive lookup. The manifest retains failed routes instead of silently claiming complete collection. Source availability and human accounting review remain the critical path.
