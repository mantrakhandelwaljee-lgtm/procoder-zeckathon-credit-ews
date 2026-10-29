# Project audit and improvement priorities

Reviewed 29 October 2026 against the two-page Zeckathon problem statement, the source ledgers, accounting formulas, benchmark/training code, historical replay, saved predictions, explanations, reports and portable execution.

**The benchmark is a useful completed baseline. The Indian evaluation remains an evidence-reconstruction project. Completing verified historical data has greater value than trying more model configurations.** The review fixes software defects without retraining the benchmark or changing its published hold-out results.

## Requirements versus current evidence

| Requirement | Current position | What still prevents completion |
|---|---|---|
| Public benchmark and genuinely out-of-sample evaluation | Frozen grouped hold-out; AP 0.3976 and trapezoidal PR-AUC 0.3934 | Anonymous records prevent confirmation of calendar/issuer separation. Published test results must not become a tuning target. |
| At least 10 listed distress cases and 30 matched non-default peers | Candidate roster reaches those counts | First-default reconstruction, historical listing/eligibility, business/size matching and outcome follow-up remain unapproved. CIRP and payment default must remain separate endpoints. |
| Three pre-event annual periods | 21 reviewed source versions across 8 issuers, representing 17 distinct issuer-periods | This is not 21 complete approved annual observations. At least 120 issuer-periods are needed for a minimal 40-name, three-year panel, plus earlier beginnings/comparative versions needed for changes and lead cutoffs. None currently clears the full primary gates. |
| Historical public availability | Sources, hashes and some filing/AGM/archive evidence are retained | Zero reviewed financial versions have an exact approved historical public-availability date. A recent download or auditor signature cannot establish it. |
| Beneish, Piotroski and Altman/learned equivalent | Functions and numerical tests; exploratory Z''/learned scores | Complete M/F inputs and accounting classifications remain missing. Null scores are correct here. |
| At least two soft-signal families | Related-party, rating and subsidiary-audit evidence exists in the example ledgers | Comparable, dated, pre-cutoff coverage across the panel and explicit missingness are still needed. No panel-wide fraud-detection claim is supported. |
| Three drivers per flagged company | Actual calibrated-model permutation SHAP on reviewed examples | Historical alert cards need approved data and dated soft evidence. Four-name examples have zero formal slots at a strict 5% budget. |
| Quarterly policy and 20:1 error cost | Capacity, deterministic ties, cost and conservative replay implemented | Indian threshold effectiveness, staffing workload and representative portfolio performance remain unvalidated. |
| Indian recall at 4q and 8q | Intentionally withheld | Both approved input files are absent. Missing results must not be converted into a success estimate. |

The [UCI source description](https://archive.ics.uci.edu/dataset/365/polish+companies+bankruptcy+data) confirms that `5year.arff` has a **one-year** bankruptcy horizon. Its score cannot be presented as a calibrated two-year Indian default probability.

## Corrections implemented in this review

| Finding | Correction and practical effect |
|---|---|
| Piotroski leverage used ending assets | Uses average beginning/ending assets for each year's leverage. Dedicated fields require debt including current maturities and income before extraordinary items, rather than silently accepting generic debt/profit proxies. An unequal-assets regression case catches the previous wrong signal. |
| Malformed peer default dates could become missing dates | Strict ISO parsing rejects malformed nonempty values; invalid dates cannot silently become healthy labels. Unknown roles, impossible observation windows and unverified peer endpoints fail validation. |
| Population approval lacked explicit matching evidence | Requires sector, qualification evidence, an existing matched case, matching evidence/status and coverage of every case. This validates the contract, while substantive size/business review remains a human task. |
| Accounting approval lacked a mapping/provenance contract | Requires verified accounting mapping, annual periods, explicit basis, source hash/pages, valid dates, finite values and balance/component reconciliation. Run-time source references must match the combined manifest. Minority/other equity is separately identified. |
| Failed/missing approvals could leave old current metrics | Previous known generated primary outputs are moved to `superseded/` before a new attempt. Missing/rejected inputs leave an explicit current status; approved attempts record input and model hashes. |
| Coverage/integrity summaries omitted later research | One merged inventory now covers 196 downloaded PDFs and 13 failed routes. Reviewed versions are counted across the pilot, steel dossier and original FY2011 work. Distinct periods and source versions remain separate concepts. |
| Cached integrity claims could become stale | Every pipeline run hashes cached PDFs; altered files stop the run. Portable runs report originals as uncached, never as locally verified. Conflicting manifest entries cannot silently replace an original. |
| Positive SHAP effects were described as unconditional financial weakness | Credit cards now describe the observed value's contribution relative to the Polish background and give specific investigation prompts. Model association alone does not prove distress, manipulation or causation. |
| Collection could silently accept a size-limited response | Oversized downloads fail explicitly instead of saving a truncated PDF. Extraction only considers downloaded-status routes. |
| Release validation depended on workspace-only scripts and stale counts | `release.py` rebuilds/tests, executes the notebook, proves benchmark artifact preservation, refreshes validation metadata and produces a checksummed portable ZIP. |

The [Piotroski paper, sections 2.3.1–2.3.3 and variable table](https://www.anderson.ucla.edu/documents/areas/prg/asam/2019/F-Score.pdf) supports beginning-assets profitability and average-assets leverage; its debt definition includes current maturities. The body and variable table differ on turnover's denominator. We explicitly retain section 2.3.3's beginning-assets turnover convention and document that inconsistency. The formula correction does not change the learned model's twelve inputs; complete example F-scores remain unavailable.

## Methodology caveats that need honest reporting

Calibration is nested inside the selected model configuration. Configuration selection itself used all development cross-validation labels before outer calibration predictions were generated. Consequently, development threshold-selection performance is not a fully nested estimate of the whole model-selection procedure and may be optimistic. The separate hold-out was not used to choose those settings. This distinction is consistent with the [scikit-learn discussion of nested versus non-nested selection](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html). This audit documents the limitation and preserves the frozen artifacts; another tuning round would require an evaluation design decided before viewing new results.

A handpicked 10-case/30-peer panel has an artificial distress prevalence. It can test documented case recovery under its own denominator, but it cannot establish an 800-borrower bank's precision, calibrated probabilities or expected monetary loss. Report `20 FN + FP` as error-cost units, distinguish repeated borrower-quarter decisions from unique defaults, and preserve the full contemporaneously eligible denominator. Do not manufacture 760 controls or round a four-name queue up to one alert.

Historical borrower eligibility needs explicit entry/exit evidence, including delistings, mergers and restructurings. The current schema validates listing start and observed outcomes; it does not yet represent every possible membership interval. Define and validate those intervals before using the engine on a changing operational portfolio. A generic approved-status string cannot resolve a substantive evidence gap.

The primary replay currently ranks the financial model. Accounting and soft signals support investigation, without fitted overlay weights. Any future overlay needs a prespecified development rule and separate evaluation under the same capacity constraint. Soft evidence discovered after an endpoint cannot become an earlier feature.

## Most efficient next work

1. **Create a cutoff-first evidence matrix for all 40 candidates.** Record the proposed endpoint, exact/interval status, required 4q/8q quarter-ends, listing/membership window, matched peers and the annual versions actually available by each cutoff. Use the current Bhushan reconciliation as the template. Resolve endpoint and availability feasibility before transcribing large tables.
2. **Close one complete case-and-three-peer packet.** Bhushan/JSW/Tata/SAIL has the deepest numerical work. Finish original current/noncurrent classifications, current maturities, earned reserves and exact public timing. December 2013 is the earliest documented payment failure, not an exhaustively certified first default. A February 2012 filing cannot satisfy a December 2011 cutoff. If the evidence cannot support a cutoff, retain it as unavailable and select additional eligible cases using a documented rule.
3. **Scale the same ledger to the remaining cases and controls.** Aim for at least 120 usable annual records plus necessary earlier balances. Capture units, basis, original versus later comparative version, field pages, hashes and accounting definitions together. Have a second reviewer independently check numerical inputs and endpoint/publication decisions; the present reviews are by one researcher.
4. **Complete M/F and two dated soft-signal families in the same pass.** Treat non-disclosure and unavailable data as distinct from a measured zero. Keep generic profit, noncurrent borrowings and structured-instrument ratings from substituting for different definitions.
5. **Freeze the approved panel and run the guarded replay.** Check missing quarters and follow-up censoring; report all-case and complete-case recall, exact capacity, uncertainty and error cost. Only then assess whether a new model or overlay solves an observed deficiency. Finish the submission narrative and demo after these checks.

## Verification and deliverables

`python release.py` records actual test counts, notebook execution and all benchmark hashes in `results/release-validation.json`. The refreshed `results/source-integrity.json` describes the current machine's cache. At this review's source audit, all 196 local PDF hashes matched; archived portable distributions intentionally omit those large originals.

Regression coverage includes independent Beneish gold values, the corrected leverage comparison, missing/proxy screen inputs, saved-model predictions, SHAP additivity, temporal joins, exact capacity, first-default gating, malformed peer dates, accounting reconciliation, source corruption and stale-result invalidation. These are software checks, not certification of the outstanding Indian evidence.

Use [RESULTS.md](../RESULTS.md) for measured results, [DATA_REVIEW.md](DATA_REVIEW.md) for the strengthened input contract, [MODEL_AND_FORMULAS.md](MODEL_AND_FORMULAS.md) for conventions, and [BHUSHAN_RECONCILIATION.md](BHUSHAN_RECONCILIATION.md) for the outstanding source-specific issues.
