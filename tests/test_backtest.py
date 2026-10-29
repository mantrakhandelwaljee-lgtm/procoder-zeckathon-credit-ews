import numpy as np
import pandas as pd
import pytest
from ews.backtest import replay,approved_population

class ToyModel:
    def predict_proba(self,X):
        p=np.asarray(X['X2']);return np.column_stack([1-p,p])

def population():
    # Synthetic fixture for numerical correctness only; never a reported Indian result.
    return pd.DataFrame([dict(entity_id=f'E{i:02}',role='case' if i<10 else 'peer',
        listed_from='2010-01-01',observed_through='2021-12-31',default_date='2018-07-10' if i<10 else '',
        endpoint_status='verified_first_default' if i<10 else 'verified_nondefault_horizon',
        qualification_status='verified',sector='steel',qualification_evidence_ref='fixture-only',
        match_case_id=f'E{(i-10)%10:02}' if i>=10 else '',
        match_status='verified' if i>=10 else '',match_evidence_ref='fixture-only' if i>=10 else '') for i in range(40)])

def accounts():
    return pd.DataFrame([dict(entity_id=f'E{i:02}',period_end='2016-03-31',period_months=12,
        public_available_at='2016-08-01',publication_status='verified',verification_status='verified',
        accounting_mapping_status='verified',source_document_id='fixture',source_url='https://example.org/fixture.pdf',
        source_sha256='a'*64,source_pages='1,2',basis='consolidated',other_equity=0,
        total_assets=100,total_liabilities=90-i,net_income=5,current_assets=40,current_liabilities=20,
        equity=10+i,retained_earnings=10,ebit=10,sales=100,inventory=5,receivables=10) for i in range(40)])

def test_true_lead_recall_capacity_and_cost():
    m,r,l,s=replay(accounts(),population(),ToyModel(),['2016-06-30','2017-06-30'])
    assert r.groupby('cutoff').selected.sum().to_dict()=={'2017-06-30':2}
    assert m[(m.status=='evaluated')&(m.horizon_months==24)].iloc[0]['cost']==160
    assert s['recall_12m']['recovered_cases']==2
    assert s['recall_12m']['all_case_recall_missing_counted_as_miss']==.2
    assert s['recall_24m']['evaluated_cases']==0 # 2016-06-30 predates publication; no fake backfill

def test_missing_data_does_not_shrink_the_ranking_universe():
    a=accounts().iloc[:-1]
    m,r,l,s=replay(a,population(),ToyModel(),['2017-06-30'])
    assert r.empty
    assert m.iloc[0]['missing_count']==1

def test_cirp_labels_cannot_pass_as_first_default():
    e=population();e.loc[0,'endpoint_status']='cirp_admission'
    with pytest.raises(ValueError):approved_population(e)


@pytest.mark.parametrize('column,value',[
    ('default_date','not-a-date'),('default_date','2018-02-30'),
    ('role','control'),('observed_through','2009-01-01'),
    ('endpoint_status','unverified'),('qualification_evidence_ref',''),
    ('match_case_id','UNKNOWN'),('sector','unmatched_sector'),('match_status','candidate')])
def test_invalid_peer_cannot_become_a_healthy_label(column,value):
    e=population();e.loc[10,column]=value
    with pytest.raises(ValueError):approved_population(e)

@pytest.mark.parametrize('column,value',[
    ('period_months',18),('accounting_mapping_status','proxy'),('source_sha256','bad'),
    ('source_pages','0'),('public_available_at','2016-02-29'),
    ('current_assets',110),('total_assets',101),('basis','unknown'),('sales',float('inf'))])
def test_unapproved_or_inconsistent_accounts_cannot_score(column,value):
    a=accounts().astype(object);a.loc[0,column]=value
    with pytest.raises(ValueError):replay(a,population(),ToyModel(),['2017-06-30'])


def test_missing_accounting_metadata_and_ambiguous_versions_rejected():
    a=accounts()
    with pytest.raises(ValueError):replay(a.drop(columns='period_months'),population(),ToyModel(),['2017-06-30'])
    with pytest.raises(ValueError):replay(pd.concat([a,a.iloc[:1]]),population(),ToyModel(),['2017-06-30'])
    extra=a.iloc[:1].copy();extra['basis']='standalone';extra['public_available_at']='2016-08-02'
    with pytest.raises(ValueError):replay(pd.concat([a,extra]),population(),ToyModel(),['2017-06-30'])


def test_removed_approval_inputs_cannot_leave_stale_success(tmp_path):
    import json
    from ews.backtest import run_if_approved
    out=tmp_path/'results/india/primary';out.mkdir(parents=True)
    (out/'quarterly_metrics.csv').write_text('status\nevaluated\n')
    (out/'summary.json').write_text('{"recall":1}')
    run_if_approved(tmp_path)
    assert not (out/'quarterly_metrics.csv').exists()
    assert not (out/'summary.json').exists()
    assert json.loads((out/'status.json').read_text())['status']=='not_run'
    assert len(list((out/'superseded').rglob('quarterly_metrics.csv')))==1
