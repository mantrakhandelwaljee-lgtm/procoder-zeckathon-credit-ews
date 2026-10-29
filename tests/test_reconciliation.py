from pathlib import Path
import json
import numpy as np,pandas as pd
from ews.policy import lead_cutoff
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/india/bhushan-reconciliation'

def test_original_gross_assets_reconcile_without_using_future_classifications():
    a=pd.read_csv(OUT/'gross_balance_reconciliation.csv').set_index('entity_id')
    expected={'BHUSHAN':(2322003.15+205734.04+4842.71)/100,'JSW':35565.15+10201.93+399.45,'TATASTEEL':101722.16+26671.06+7089.92,'SAIL':60434.27+11613.06+6062.64}
    for e,v in expected.items():assert np.isclose(a.loc[e,'gross_assets'],v)
    assert np.abs(a.residual_crore).max()<.011
    data=json.loads((ROOT/'data/curated/fy2011_original_accounts.json').read_text())
    assert all(x['source_report_year']==2011 and x['source_column']=='current_original' for x in data)
    assert all(x['current_assets'] is None and x['current_liabilities'] is None for x in data)

def test_original_and_later_profit_versions_remain_separate():
    original=pd.read_csv(OUT/'original_accounts.csv').set_index('entity_id')
    later=pd.read_csv(ROOT/'results/india/bhushan-case/reviewed_accounts.csv')
    s=later[(later.entity_id=='SAIL')&(later.period_end=='2011-03-31')].iloc[0]
    assert original.loc['SAIL','net_income_parent']==5017.18
    assert s.net_income==5013.91
    assert original.loc['SAIL','source_document_id']=='SAIL_2011_annual'
    assert s.source_document_id=='SAIL_2012_annual'
    assert not pd.read_csv(OUT/'original_vs_later_comparatives.csv').later_values_backdated.any()

def test_finance_income_offsets_are_not_treated_as_gross_finance_expense():
    a=pd.read_csv(OUT/'original_accounts.csv').set_index('entity_id')
    assert np.isclose(a.loc['JSW','finance_cost_before_income_offsets']-79.24-32.29,a.loc['JSW','reported_net_finance_charge'])
    assert np.isclose(a.loc['TATASTEEL','finance_cost_before_income_offsets'],3426.67-219.63)
    assert np.isclose(a.loc['TATASTEEL','reported_net_finance_charge'],3207.04-437)

def test_reported_cure_is_not_an_invented_actual_payment_date():
    p=pd.read_csv(ROOT/'data/curated/reconciled_payment_episodes.csv')
    first=p[p.due_date=='2013-12-31'].iloc[0]
    assert first.reported_paid_in_status_asof=='2014-02-26'
    assert p.actual_settlement_date.isna().all() and p['isin'].isna().all()
    jan1=p[p.due_date=='2014-01-01'].iloc[0]
    assert pd.isna(jan1.reported_paid_in_status_asof) # undated subsequent-receipt footnote
    assert all(not x['complete_render_review'] for x in json.loads((ROOT/'data/curated/payment_remote_source_reviews.json').read_text()))

def test_filing_signature_and_archive_metadata_do_not_clear_publication_gate():
    a=pd.read_csv(ROOT/'data/curated/fy2011_availability_review.csv')
    assert a.public_available_at.isna().all() and not a.strict_eligible.any()
    reg=a[a.evidence_type=='official_regulator_filing_register'].iloc[0]
    assert reg.evidence_date=='2012-02-22'
    assert lead_cutoff('2013-12-31',24).date().isoformat()=='2011-12-31'
    assert pd.Timestamp(reg.evidence_date)>lead_cutoff('2013-12-31',24)
    status=json.loads((OUT/'status.json').read_text())
    assert status['primary_scores_emitted']==0 and status['primary_recall_8q'] is None
