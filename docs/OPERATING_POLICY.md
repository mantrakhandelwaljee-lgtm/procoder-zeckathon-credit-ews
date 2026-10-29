# Quarterly review policy

Status: proposed research policy. It has numerical tests; staffing workload and Indian deployment performance are not validated.

1. Establish the eligible borrower universe at the quarter-end. Remove already-defaulted issuers from the first-default prediction task and retain their workout records separately.
2. Complete data freshness, provenance and accounting checks. Do not quietly drop missing issuers to make the review budget easier. Record unavailable scores and any data-quality escalations.
3. Rank eligible issuers by the frozen, selected score. Break score ties by stable entity ID. The evaluation queue has `floor(0.05 x N)` slots; the bank's 800-name universe has forty.
4. Select the production threshold using development predictions under `20 FN + FP`, with the same capacity cap. The current benchmark's development threshold is stored in `results/benchmark/metrics.json`; it is not an approved Indian threshold.
5. A calibrated probability for the same horizon/population has theoretical benefit `21p - 1`; the unconstrained error-cost cutoff is `1/21`. A transferred score or expert overlay does not inherit that calibration.
6. Show up to forty ranked names, with formal alerts distinguished from lower-priority monitoring. Do not create extra formal alerts simply to consume unused review capacity.
7. Provide a credit card for each formal alert: historical cutoff, source freshness, actual score type, three drivers, M/F/Z components, soft evidence, missingness, maturity questions and reviewer owner.
8. An analyst verifies the evidence, prepares liquidity/covenant/refinancing questions, and records the investigation. A senior credit officer confirms or rejects the alert. The credit committee decides exposure or approval actions after that investigation.
9. Repeat reviews and carryovers consume slots. Record new names, existing names and replacements. An urgent override consumes a budgeted slot or replaces a selected name; it does not become an unnoticed forty-first full review.
10. Log disposition, follow-up owner and due date. A suggested planning allocation is eight analysts with five names each per quarter; validate actual hours per case before calling the policy operationally proven.

Report quarterly error-cost units and unique default outcomes separately. Repeated missed borrower-quarter decisions are not several independent company defaults, and the cost index is not rupees of credit loss or proven losses prevented.

The current frozen primary scoring architecture is financial-only. Accounting screens and related-party/rating evidence support investigation. An overlay can replace it only after independent development evidence shows an improvement under the same review budget; no weights were fitted to the small Indian pilot.
