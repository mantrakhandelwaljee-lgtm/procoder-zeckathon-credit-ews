# procoder | Zeckathon Problem Statement 02

**Team:** procoder  
**Members:** Mantra Khandelwal, Mohit Peshwani, Om Kumar, Omkar Mainkar  
**Repository:** https://github.com/mantrakhandelwaljee-lgtm/procoder-zeckathon-credit-ews

Read [the solution report](submission/Zeckathon_Credit_EWS_Report.pdf) or its [editable Markdown version](submission/Zeckathon_Credit_EWS_Report.md). Status: benchmark and pipeline implemented; Indian historical evaluation remains incomplete. This repository begins with a truthful snapshot of the existing work; the initial commit is not a reconstruction of earlier development history.

# Corporate credit early-warning research build

**Start with [RESULTS.md](RESULTS.md) and [the project audit](docs/PROJECT_AUDIT.md).** The benchmark and core pipeline run. The full Indian competition submission is incomplete: a publication-verified three-year panel, qualified controls, complete M/F inputs and primary Indian lead-time evaluation are still required. No Indian recall, fraud accuracy or loss-saving claim is fabricated.

## Run

Python 3.12 is the validated runtime. Poppler's `pdftotext` is needed for extraction (on macOS: `brew install poppler`).

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py --test
```

To restore source PDFs/text omitted from the portable code archive:

```bash
python run.py --fetch --test
```

The corpus contains hundreds of megabytes of public annual reports. The manifest preserves exact URLs, including non-March fiscal periods and exceptional filenames. Hash mismatches are quarantined for version review. `--retry-failed` retries documented failed routes; a failed URL guess does not always indicate a missing fiscal period.

To reproduce the fixed model selection, calibration, frozen split and hold-out results:

```bash
python run.py --train --test
```

The portable archive runs from saved extraction/curation results without fetching the company PDFs. Original text is re-extracted only when the full text cache is available; otherwise the saved candidate table is preserved. Use `--fetch` before independently auditing or repeating source extraction.

No cloud service, API key, external publication or paid database is required for the implemented build. Some source sites may become unavailable; cached originals and hashes are retained locally.

## Inspect

- `research-review.ipynb`: executable, pre-executed review notebook.
- `results/benchmark/metrics.json`: measured benchmark results, counts, protocol and limitations.
- `results/benchmark/frozen_split.csv`: split membership; grouped on the actual deployed inputs.
- `results/benchmark/holdout_predictions.csv`: immutable evaluation evidence for the fixed protocol.
- `results/benchmark/model.joblib`: calibrated ensemble; load only trusted model files.
- `results/india/pilot-evidence-cards.md`: four reviewed financial examples and actual-model SHAP drivers.
- `results/india/readiness.json`: honest completion status; Indian recall fields remain null.
- `data/curated/documents.csv`: evidence manifest.
- `data/curated/financial_candidates.csv`: source-linked extraction candidates, all requiring review.
- `data/curated/pilot_field_sources.csv`: reviewed pilot values and page-level provenance.
- `data/curated/events.csv`: CIRP dates distinguished from earlier default evidence.
- `docs/DATA_REVIEW.md`: exact remaining work and approved-input schema.
- `docs/BHUSHAN_CASE_DOSSIER.md`: steel case research, conflicting endpoints, numerical peer comparison and source timing decisions.
- `docs/BHUSHAN_RECONCILIATION.md`: contemporaneous payment-notice reconciliation, original FY2011 statement review, version differences and publication evidence decisions.
- `results/india/bhushan-case/`: nine numerical examples, provenance, actual-model explanations and strict/conditional cutoff decisions.
- `docs/MODEL_AND_FORMULAS.md`: model, equations, independent formula validation and split correction audit.
- `docs/OPERATING_POLICY.md`: review capacity, costs, escalation and queue handling.

## Implementation

`ews/collect.py` collects immutable public sources. `extract.py` proposes table candidates. `curate.py` records explicit source-review decisions; it never promotes the whole candidate table. `accounting.py` calculates the transferable ratios and M/F/Z screens. `benchmark.py` trains and validates. `policy.py` implements temporal joins, capacity and cost. `india.py` produces the reviewed pilot and readiness audit. `backtest.py` runs the strict primary replay when approved inputs exist. `report.py` generates the readable results and review notebook.

The original benchmark archive is [UCI Polish Companies Bankruptcy](https://archive.ics.uci.edu/dataset/365/polish+companies+bankruptcy+data), one-year horizon (`5year.arff`), with UCI citation metadata retained in `data/raw/uci-365.json`. Company disclosures retain their original issuer/exchange attribution in the manifest; the portable archive omits the large company-PDF corpus and raw report-text cache.

The software is a research prototype. Numerical tests do not establish that the foreign model is appropriate for Indian lending, that the proposed controls are all valid, or that the source timing is complete. The accounting review gates are part of the implementation, not hidden footnotes.

The separate case manifest is `data/curated/bhushan_documents.csv`. Restore those additional sources with `python -m ews.case_bhushan --fetch`; run `python -m ews.case_bhushan` to rebuild only that dossier's numerical outputs. The combined `run.py` also rebuilds them. Curated case JSON/CSV review decisions are inputs and are not overwritten by the normal pipeline.

Run `python -m ews.reconcile_bhushan` for the original FY2011 verification and payment/publication review outputs. This preserves original values without filling unresolved current classifications from future comparative statements. The combined pipeline runs this review as well.


## Validate and package a release

```bash
python release.py
```

This rebuilds the pipeline, runs the tests, executes every notebook code cell with the current Python environment, checks that all benchmark artifact hashes are unchanged, writes `results/release-validation.json`, and creates the portable ZIP plus SHA-256 manifest. It never invokes training. Large source PDFs/text and superseded primary results are excluded; each run distinguishes uncached sources from locally verified originals. To restore the complete two-manifest corpus, run both `python run.py --fetch` and `python -m ews.case_bhushan --fetch`, then rebuild.
