# Model and accounting specifications

## Benchmark protocol

UCI Polish Companies Bankruptcy, `5year.arff`, one-year forecast horizon. Download SHA-256 and final sample counts are in `results/benchmark/metrics.json`. Exact original input duplicates are removed; no conflicting full-feature labels were found. After reduction to the deployed twelve ratios, identical deployed vectors are kept in the same hold-out and cross-validation group.

An initial diagnostic split grouped only the original 64-column vectors. The audit found 15 deployed-feature groups crossing that split. That diagnostic result was discarded. Protocol 2 groups on the actual deployed vectors for the hold-out, model selection and calibration. The fixed ten-configuration search was rerun for this integrity correction, not to optimize the revised test score. No hyperparameters, features or policy were subsequently selected on the revised hold-out.

Five-fold stratified grouping supplies a roughly 20% locked test set. The remaining records support three-fold grouped model selection. Six logistic configurations and four histogram gradient-boosting configurations are compared using development out-of-fold average precision, with error cost as a tie-break. Preprocessing is fold-local: finite-value handling, 0.5/99.5 percentile clipping, median imputation, missingness indicators and standardization.

Configuration selection uses all development CV labels before the outer calibration predictions. Calibration is nested; model selection is **not** fully nested in those outer folds. Development threshold results can therefore be optimistic. The separate hold-out remains independent of all development choices. A future methodological change needs a fresh evaluation plan; do not tune against the published hold-out.

The selected configuration and calibration are recorded in the metrics file. Policy selection uses outer out-of-fold predictions; each outer model uses separately grouped inner sigmoid calibration. The final calibrated ensemble is fitted only on the development set. Its hold-out predictions are used once after those choices. Test-set stratified bootstrap intervals are conditional on the anonymous observations; they do not establish issuer-disjoint uncertainty.

Both AP and trapezoidal PR-AUC are reported. The benchmark has no usable issuer identities/calendar panel, so neither a temporal-validation claim nor an Indian probability-calibration claim is made.

## Beneish

Eight-variable coefficients:

`M = -4.840 + .920 DSRI + .528 GMI + .404 AQI + .892 SGI + .115 DEPI - .172 SGAI + 4.679 TATA - .327 LVGI`

DSRI compares receivables/sales; GMI compares prior/current gross margin; AQI compares `1 - (current assets + net PPE)/assets`; SGI is sales growth; DEPI compares prior/current depreciation rates; SGAI compares SG&A/sales; LVGI compares `(current liabilities + long-term debt)/assets`; TATA is `(continuing-operations income - CFO)/assets`.

The implementation reproduces Kelley's published Sunbeam example to rounding: **-1.884**. The reference specifies a -1.78 cutoff for this model. It is an external reference threshold, not a fitted Indian fraud boundary. The Indian pilot has missing verified COGS/SG&A and therefore no complete M-Score.

Source: [author-affiliated calculator example](https://apps.kelley.iu.edu/Beneish/Content/Examples/SunbeamExample.pdf).

## Piotroski

Nine binary financial-strength signals: positive ROA, positive CFO, improved ROA, CFO above earnings, lower long-term leverage, higher current ratio, no actual equity issuance, higher gross margin and higher asset turnover. ROA and turnover use beginning assets under the original paper's convention; older beginning assets are necessary for prior-period changes. ROA requires income before extraordinary items (`net_income_before_extraordinary`); leverage requires `long_term_debt_including_current_maturities`. Generic net income or noncurrent borrowings are not silently substituted. Long-term leverage uses debt divided by the average of beginning and ending assets, separately for each period. The paper's section 2.3 defines turnover with beginning assets; its variable table instead says average assets. This implementation explicitly follows section 2.3 for turnover rather than claiming the source is unambiguous. A share-count change is not substituted for issuance. The audit corrected a year-end-assets leverage denominator; complete pilot F-scores remain unavailable, and the learned model does not use this F-score.

Source: [Piotroski original paper](https://www.anderson.ucla.edu/documents/areas/prg/asam/2019/F-Score.pdf).

## Altman

Non-manufacturer Z'' without the separate emerging-market rating-equivalent intercept:

`Z'' = 6.56 WC/TA + 3.26 RE/TA + 6.72 EBIT/TA + 1.05 book_equity/total_liabilities`

Original public-manufacturing option:

`Z = 1.2 WC/TA + 1.4 RE/TA + 3.3 EBIT/TA + .6 market_equity/total_liabilities + .999 sales/TA`

Do not add the EM-model +3.25 intercept and continue interpreting the result as the unshifted Z''. No Indian default probability is derived from either score.

Source: [Altman 2002, NYU, sections 8-9](https://w4.stern.nyu.edu/finance/docs/WP/2002/pdf/wpa02052.pdf).

## Explainability

The Indian pilot uses permutation SHAP on the actual calibrated ensemble with 32 development-only background records and a fixed random seed. The sum of all contributions plus the baseline is checked against each displayed score. This avoids displaying an uncalibrated model's explanation as though it explained a different calibrated score. Explanations describe model associations, not causes or proof of manipulation.

## Missingness and period length

Non-finite or non-positive denominators produce missing ratios rather than extreme invented values. Negative equity/profit numerators remain valid. Non-twelve-month flow records cannot silently pass as ordinary annual observations. Incomplete M/F screens remain null and list missing components. The primary replay requires all twelve deployable ratios rather than imputing most of an Indian record from the foreign benchmark.
