"""Readable research results and an executable review notebook."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .benchmark import load_data,metric_values,top_policy
from .policy import error_cost

def baselines(root):
    """Prespecified formula comparison; never used for model/feature/policy selection."""
    clean,_=load_data(root/'data/raw/polish-bankruptcy.zip')
    split=pd.read_csv(root/'results/benchmark/frozen_split.csv')
    dev=clean[split.split=='development'];test=clean[split.split=='holdout']
    cols=['X3','X6','X7','X8'];med=dev[cols].replace([np.inf,-np.inf],np.nan).median()
    a=test[cols].replace([np.inf,-np.inf],np.nan)
    missing=int(a.isna().any(axis=1).sum());a=a.fillna(med)
    risk=-(6.56*a.X3+3.26*a.X6+6.72*a.X7+1.05*a.X8).to_numpy()
    y=test.label.to_numpy(dtype=int)
    from sklearn.metrics import average_precision_score,precision_recall_curve,auc
    precision,recall,_=precision_recall_curve(y,risk)
    k=int(np.floor(.05*len(test)))
    result={'altman_z_double_prime':{'average_precision':float(average_precision_score(y,risk)),
        'pr_auc_trapezoidal':float(auc(recall,precision)),
        'top5':error_cost(y,top_policy(y,risk)),'holdout_rows_with_imputed_formula_input':missing,
        'missingness_policy':'Development-only medians; raw formula otherwise; no Indian applicability implied.'},
        'random_top5_expected':{'alerts':k,'expected_tp':k*y.mean(),
            'expected_recall':k/len(test),'expected_cost':20*(y.sum()-k*y.mean())+k*(1-y.mean())}}
    (root/'results/benchmark/baselines.json').write_text(json.dumps(result,indent=2))
    return result

def run(root):
    root=Path(root);b=json.loads((root/'results/benchmark/metrics.json').read_text());h=b['holdout']
    r=json.loads((root/'results/india/readiness.json').read_text());base=baselines(root)
    coverage=pd.read_csv(root/'results/india/coverage_review_queue.csv')
    pilot=pd.read_csv(root/'results/india/pilot_scores.csv')
    from .evidence import load_documents
    docs=load_documents(root)
    case_manifest=root/'data/curated/bhushan_documents.csv'
    additional_source_count=0
    if case_manifest.exists():
        case_docs=pd.read_csv(case_manifest)
        additional_source_count=int((case_docs.status=='downloaded').sum())

    facts=pd.read_csv(root/'data/curated/financial_candidates.csv')
    test_summary='See results/test-results.xml.'
    test_file=root/'results/test-results.xml'
    if test_file.exists():
        import xml.etree.ElementTree as ET
        suites=list(ET.parse(test_file).getroot().iter('testsuite'))
        test_count=sum(int(s.get('tests','0')) for s in suites)
        failed=sum(int(s.get('failures','0'))+int(s.get('errors','0')) for s in suites)
        test_summary=f'{test_count} tests; {failed} failures/errors. Includes independent published formula example, serialization, temporal joins, capacity and lead-time checks.'
    a=b['data_audit'];top=h['top5'];z=base['altman_z_double_prime']
    lines=[
      '# Execution results: corporate early-warning research build','',
      '29 October 2026. **The benchmark and core pipeline are implemented. The full Indian competition submission is not complete.**',
      'Indian four-quarter/eight-quarter recall and expected loss are deliberately withheld until the historical panel and publication timing are verified.','',
      '## What is working','',
      '| Deliverable | Actual status |','|---|---|',
      '| Public benchmark model | Trained, calibrated and evaluated with a frozen grouped hold-out |',
      '| Reproducible pipeline | Source collection, extraction candidates, reviewed fact ledger, ratios, M/F/Z functions, ranking and guarded replay |',
      f"| Source corpus | {int((docs.status=='downloaded').sum())} downloaded PDFs, including {int(((docs.status=='downloaded')&(docs.document_type=='annual')).sum())} annual reports; hashes and original URLs retained |",
      '| Indian case events | Ten documented CIRP dates; five earlier payment-default records separately identified |',
      '| Case/control roster | Ten case candidates and thirty provisional distinct controls, after removing known unsuitable controls |',
      f'| Financial extraction | {len(facts):,} source-linked numerical candidates; these are not automatically verified |',
      '| Source-reviewed pilot | Four toll-road/EPC issuers; FY2016 plus comparative FY2015 values, with field-level source pages |',
      '| Steel case dossier | Bhushan and three peers: nine numerical examples, explicit accounting proxies, conflicting default evidence and guarded cutoff checks |',
      '| FY2011 original-source review | Four original consolidated statement reviews, 99 numerical/derived fields, gross balance checks and 42 version/definition comparisons; exact public-release timestamps remain unverified |',
      '| Explanations | Permutation SHAP of the actual calibrated ensemble, with a development-only background |',
      '| Accounting screens | Implemented and tested; pilot Z\'\' calculated; pilot M/F remain incomplete because required inputs are unverified |',
      '| Indian recall and loss | Not reported: minimum approved point-in-time panel is not ready |','',
      '## Verification','',test_summary,
      'The combined corpus hash audit is refreshed on each run in `results/source-integrity.json`; uncached originals are explicitly marked. See [the project audit](docs/PROJECT_AUDIT.md) for corrections, remaining gaps and priorities. These software/integrity checks do not replace accounting and historical-availability verification.','',
      '## Measured benchmark results','',
      'Dataset: UCI Polish Companies Bankruptcy, `5year.arff` (one-year horizon). The features are the twelve explicit transferable ratios in `ews/accounting.py`.','',
      '| Metric | Result |','|---|---|',
      f"| Raw observations / bankrupt observations | {a['raw_rows']:,} / {a['raw_positives']} |",
      f"| After exact original-record deduplication | {a['clean_rows']:,} / {a['clean_positives']} bankrupt ({a['clean_prevalence']:.2%}) |",
      f"| Frozen hold-out | {h['sample_count']:,} records; {h['positive_count']} bankrupt ({h['prevalence']:.2%}) |",
      f"| Average precision (AP) | {h['average_precision']:.4f} |",
      f"| Trapezoidal PR-AUC | {h['pr_auc_trapezoidal']:.4f} |",
      f"| AP bootstrap 95% interval | {h['ap_bootstrap_95_interval'][0]:.4f}–{h['ap_bootstrap_95_interval'][1]:.4f} |",
      f"| Alerts within a 5% budget | {top['alerts']} / {h['sample_count']} ({top['alerts']/h['sample_count']:.2%}) |",
      f"| True positives / false positives / missed bankruptcies | {top['tp']} / {top['fp']} / {top['fn']} |",
      f"| Recall at that budget | {top['recall']:.2%} |",
      f"| Precision at that budget | {top['precision']:.2%} |",
      f"| Error-cost index, 20 FN + FP | {top['cost']} |",
      f"| Error cost with no alerts | {h['no_alert']['cost']} |",
      f"| Altman Z'' baseline: AP / recall at 5% | {z['average_precision']:.4f} / {z['top5']['recall']:.2%} |",'',
      '![Benchmark validation](results/benchmark/benchmark-validation.png)','',
      'These are benchmark results on anonymous Polish financial snapshots. They do not demonstrate calendar-time validation, independent-issuer validation, Indian probability calibration, fraud-detection accuracy or Indian lead-time recall. The bootstrap intervals condition on these anonymous observations and do not correct for unknown issuer clustering.','',
      'The selected model is histogram gradient boosting, maximum depth 5, unweighted, with sigmoid calibration. Configuration choices use grouped development folds. The source archive contains 60 exact full-row duplicates. After feature reduction, 42 additional duplicate deployed vectors are grouped so that none crosses the hold-out boundary.','',
      'An initial diagnostic split did not group the reduced vectors correctly. That result was discarded and the fixed search rerun after correcting the split. The audit and correction are documented in `docs/MODEL_AND_FORMULAS.md`.','',
      '## Cost and capacity','',
      f"The development-selected score threshold is **{b['development_selected_policy']['threshold']:.4f}**, always subject to the 5% cap. On the hold-out it selects {h['development_selected_threshold_with_cap']['alerts']} names with cost {h['development_selected_threshold_with_cap']['cost']}. No test-based threshold adjustment was made.",
      'The theoretical 1/21 = 4.76% cutoff applies only to calibrated probabilities for the same population/horizon under the stated error costs. It is not an approved Indian threshold. The bank\'s 800-name capacity rule is forty; the anonymous hold-out has a different denominator and therefore 58 evaluation slots.','',
      '## Indian evidence pilot','',
      '| Issuer | Transferred score | Altman Z\'\' | Formal alerts |',
      '|---|---:|---:|---:|',
    ]
    for row in pilot.itertuples():lines.append(f'| {row.entity_id} | {row.score:.4f} | {row.altman_z_double_prime:.3f} | 0 |')
    lines += ['',
      'The pilot ranks ITNL first among these four reviewed examples. That is not evidence of recovery in an 800-borrower universe. Four names produce zero formal slots at a strict 5% budget, and publication dates are not yet verified. No historical early-warning success is claimed. All four Z\'\' scores are low; shared project-finance structures and concessions can affect industrial-model applicability.','',
      '[Read the evidence cards](results/india/pilot-evidence-cards.md). [Inspect every numerical input and PDF page](data/curated/pilot_field_sources.csv).',
      'The reconstructed retained-earnings input includes documented earned general/debenture reserves as well as the P&L balance; share premium and capital reserves are excluded. Net income is attributable to parent owners; this consolidated/foreign-model accounting mapping is disclosed.','',
      'M-Score and F-Score remain null in these examples because COGS, SG&A, actual issuance and older beginning assets are not fully verified. The M-Score implementation independently reproduces the author-affiliated Sunbeam example (-1.884). Missing fields were not replaced with invented zero values.','',
      '## Findings that change the research strategy','',
      '- [The payment/FY2011 reconciliation](docs/BHUSHAN_RECONCILIATION.md) corroborates the December 2013 payment failure using contemporaneous indexed trustee notices and later cure reporting. Exact settlement and first-default completeness remain unverified. Original FY2011 figures are preserved separately from later comparatives; no historical recovery claim clears the publication/mapping gates.',
      '- Alok, Amtek, Bhushan Steel, Era Infra and Jaypee Infratech have documented payment defaults earlier than their CIRP admissions. Evaluating the later dates without removing already-defaulted observations would overstate warning lead.',
      '- Three proposed controls were removed: Jindal Steel & Power and HCC have default evidence; PNC did not cover earlier cutoffs because of its 2015 IPO. Replacements still need horizon-specific qualification.',
      '- Alok has 18-month reporting periods. Annual-flow features and change scores require verified TTM reconstruction or explicit exclusions.',
      '- Automated extraction produced substantive classification errors in the pilot. Corrections and their reasons are retained in `data/curated/review_decisions.json`.',
      '- A rating on a structured instrument is not the same as an issuer rating. The ITNL February 2018 document cannot support a warning in 2017.',
      '- The June 2018 ITNL technical payment delay is kept distinct from a first bank-loan default.','',
      '## Work still required before submission','',
      '1. Complete and independently check three pre-event financial years for all ten cases and thirty qualified distinct controls, including prior periods needed for changes.',
      '2. Verify actual historical public availability, original/restated versions and first-default endpoints. Retain interval uncertainty rather than inventing dates.',
      '3. Finish required M/F inputs and dated soft-signal coverage. Current related-party and rating evidence is a pilot, not a complete panel.',
      '4. Approve the population and accounting inputs, run strict quarterly replay, and publish Indian four-/eight-quarter recall, exclusions, capacity and cost.',
      '5. Complete workload validation and submission presentation after the evidence gates pass.','',
      '[Exact completion queue and input schema](docs/DATA_REVIEW.md). [Operating policy](docs/OPERATING_POLICY.md). [Model/formula specification](docs/MODEL_AND_FORMULAS.md).','',
      'The primary replay is implemented: it refuses unqualified populations, later-CIRP labels masquerading as first defaults, future financials, incomplete issuer universes and censored negative outcomes. Its output remains `not_run` until approved inputs exist.','',
      '## Reproduce and inspect','',
      '`python run.py --test` rebuilds extraction candidates, the reviewed pilot, explanations, source coverage and this report from cached files. `python run.py --fetch` restores the exact source manifest. `python run.py --train --test` reproduces the frozen benchmark protocol.','',
      'Start with [README](README.md), [the executable notebook](research-review.ipynb), [benchmark metrics](results/benchmark/metrics.json), [Indian readiness](results/india/readiness.json), and [the source manifest](data/curated/documents.csv).','',
      'The portable code archive excludes the large company-PDF corpus; those files are available in this local project and can be restored from the manifest. No site was published and no credit decision was taken.','',
      'Primary research references: [UCI benchmark](https://archive.ics.uci.edu/dataset/365/polish+companies+bankruptcy+data), [trustee default notice](https://www.axistrustee.in/pdf/Press-Release-dated-20-October-2015.pdf), [IBBI CIRP registry source](https://ibbi.gov.in/uploads/meetings/Agenda_7%28a%29_210917.pdf), [Beneish reference example](https://apps.kelley.iu.edu/Beneish/Content/Examples/SunbeamExample.pdf), [Altman original research](https://w4.stern.nyu.edu/finance/docs/WP/2002/pdf/wpa02052.pdf).'
    ]
    (root/'RESULTS.md').write_text('\n'.join(lines))
    make_notebook(root)

def make_notebook(root):
    import nbformat as nbf
    nb=nbf.v4.new_notebook()
    md=nbf.v4.new_markdown_cell;code=nbf.v4.new_code_cell
    nb.cells=[md('# Corporate early-warning research review\n\nBenchmark results are measured. Indian historical recall is withheld pending complete verified evidence. Run the pipeline before this notebook; the notebook reads saved results and does not tune on the test set.'),
      code("from pathlib import Path\nimport json, pandas as pd\nfrom IPython.display import display, Image\nROOT=Path.cwd()\nif not (ROOT/'results/benchmark/metrics.json').exists():\n    ROOT=Path('credit-ews')\nmetrics=json.loads((ROOT/'results/benchmark/metrics.json').read_text())\nreadiness=json.loads((ROOT/'results/india/readiness.json').read_text())\ndisplay(pd.DataFrame([{'metric':k,'value':v} for k,v in metrics['holdout'].items() if not isinstance(v,(dict,list))]))"),
      md('## Benchmark validation\n\nThe split groups on the actual deployed financial vectors. AP and trapezoidal PR-AUC are separately reported.'),
      code("display(Image(filename=str(ROOT/'results/benchmark/benchmark-validation.png')))\ndisplay(pd.read_csv(ROOT/'results/benchmark/holdout_predictions.csv').head(10))"),
      md('## Development choices\n\nThis table contains development cross-validation results, not repeated model selection on hold-out scores.'),
      code("comparison=json.loads((ROOT/'results/benchmark/development_comparison.json').read_text())\ndisplay(pd.json_normalize(comparison)[['config.kind','config.balanced','average_precision','top5.recall','top5.cost']])"),
      md('## Readiness and remaining evidence\n\nA candidate roster and downloaded reports do not establish a complete Indian panel.'),
      code("display(pd.DataFrame([{'item':k,'value':v} for k,v in readiness.items() if not isinstance(v,list)]))\ndisplay(pd.read_csv(ROOT/'results/india/coverage_review_queue.csv'))"),
      md('## Indian numerical pilot\n\nThese four source-reviewed examples have unverified publication dates. The transferred score is not an Indian PD. A four-name sample has zero formal slots at a strict 5% rate.'),
      code("display(pd.read_csv(ROOT/'results/india/pilot_scores.csv'))\ndisplay(pd.read_csv(ROOT/'results/india/pilot_ratios.csv'))"),
      md('## Inspect a credit evidence card\n\nChange the entity identifier to inspect another reviewed example. The SHAP values explain the actual displayed score.'),
      code("entity='ITNL'\ncards=json.loads((ROOT/'results/india/pilot_evidence_cards.json').read_text())\ncard=next(c for c in cards if c['entity_id']==entity)\ndisplay(pd.DataFrame(card['drivers']))\ndisplay(pd.read_csv(ROOT/'data/curated/pilot_field_sources.csv').query('entity_id == @entity'))\nprint('M-Score missing inputs:',card['beneish_m']['missing'])\nprint('F-Score missing inputs:',card['piotroski_f']['missing'])"),
      md('## Events and original documents\n\nFirst-default reconstruction must precede the early-warning claim. Month intervals remain intervals.'),
      code("display(pd.read_csv(ROOT/'data/curated/events.csv'))\nfrom ews.evidence import load_documents\ndocs=load_documents(ROOT)\ndisplay(docs[['document_id','status','source_url','sha256','publication_status']].head(20))"),
      md('## Primary historical replay\n\nThe engine requires approved population and accounting inputs. Read docs/DATA_REVIEW.md for the schemas.'),
      code("print((ROOT/'results/india/primary/status.json').read_text())"),
      md('## Bhushan Steel dossier\n\nThe FY2012 peer comparison is exploratory. First-default dates conflict, public timestamps are unverified, and earned-reserve mappings remain proxies. FY2011 comparative figures from FY2012 sources are excluded from the eight-quarter cutoffs.'),
      code("case=ROOT/'results/india/bhushan-case'\ndisplay(pd.read_csv(case/'fy2012_peer_comparison.csv'))\ndisplay(pd.read_csv(case/'lead_time_scenarios.csv'))\nprint((case/'status.json').read_text())\ndisplay(pd.read_csv(ROOT/'data/curated/bhushan_case_events.csv'))"),
      md('## Original FY2011 and payment reconciliation\n\nOriginal reports remain distinct from later comparative versions. A documented payment event is not an exhaustive first-default certification, and filing/signature/archive metadata do not automatically establish public availability.'),
      code("recon=ROOT/'results/india/bhushan-reconciliation'\ndisplay(pd.read_csv(recon/'gross_balance_reconciliation.csv'))\ndisplay(pd.read_csv(recon/'original_vs_later_comparatives.csv'))\ndisplay(pd.read_csv(ROOT/'data/curated/reconciled_payment_episodes.csv'))\ndisplay(pd.read_csv(ROOT/'data/curated/fy2011_availability_review.csv'))\nprint((recon/'status.json').read_text())"),
    ]
    nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}}
    path=root/'research-review.ipynb'
    # Preserve executed outputs on an unchanged notebook when refreshing the report.
    if path.exists():
        old=nbf.read(path,as_version=4)
        if [c.source for c in old.cells]==[c.source for c in nb.cells]:return
    nbf.write(nb,path)
