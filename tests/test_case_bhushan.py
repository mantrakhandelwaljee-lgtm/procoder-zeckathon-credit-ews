from pathlib import Path
import json
import numpy as np
import pandas as pd
from ews.case_bhushan import sensitivity_snapshot

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/india/bhushan-case'

def test_later_comparative_version_cannot_fill_eight_quarter_cutoffs():
    accounts=pd.DataFrame(json.loads((ROOT/'data/curated/bhushan_case_accounts.json').read_text()))
    assert len(accounts[accounts.period_end=='2011-03-31'])==4
    for cutoff in ['2011-12-31','2012-03-31','2012-06-30']:
        assert sensitivity_snapshot(accounts,cutoff).empty
    selected=sensitivity_snapshot(accounts,'2012-12-31')
    assert len(selected)==4
    assert set(selected.period_end)=={'2012-03-31'}
    assert not (selected.publication_status=='verified').any()

def test_bhushan_gross_assets_and_other_equity_reconcile_to_statement():
    a=pd.read_csv(OUT/'reviewed_accounts.csv');r=a[(a.entity_id=='BHUSHAN')&(a.period_end=='2012-03-31')].iloc[0]
    # Independent statement subtotals (INR lakh), not total-assets-minus-common-equity.
    assert np.isclose(r.total_assets,3372418.19/100)
    assert np.isclose(r.total_liabilities,(1807369.67+760559.29)/100)
    assert np.isclose(r.total_assets-r.equity-r.total_liabilities,(38301+8915.65)/100)
    # Old report presentation nets current liabilities; the printed total is not gross assets.
    assert np.isclose((2322003.15+210576.75)/100,2532579.90/100)

def test_uncertainty_never_becomes_a_primary_score_or_formal_alert():
    replay=pd.read_csv(OUT/'lead_time_scenarios.csv')
    assert len(replay)==24
    assert replay.strict_score.isna().all() and replay.recovered.isna().all()
    assert not replay.formal_alert.any()
    assert replay[replay.lead_months==24].sensitivity_score.isna().all()
    status=json.loads((OUT/'status.json').read_text())
    assert status['first_default_status']=='earliest_documented_not_exhaustively_established'
    assert status['strict_recall_4q'] is None and status['strict_recall_8q'] is None
    events=pd.read_csv(ROOT/'data/curated/bhushan_case_events.csv')
    assert not (events.first_default_status=='verified_first_default').any()

def test_case_explanations_reproduce_all_nine_actual_scores():
    c=pd.read_csv(OUT/'shap_contributions.csv');s=pd.read_csv(OUT/'scores.csv').set_index(['entity_id','period_end']).score
    reconstructed=c.groupby(['entity_id','period_end']).contribution.sum()+c.groupby(['entity_id','period_end']).base_value.first()
    assert len(s)==9 and np.allclose(reconstructed.loc[s.index],s,atol=1e-6)
