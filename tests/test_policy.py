import numpy as np
import pandas as pd
import pytest
from ews.policy import rank_watchlist, error_cost, lead_cutoff, asof_financials, optimize_policy

def test_capacity_exact_and_tie_break():
    df=pd.DataFrame({'entity_id':[f'E{i:03}' for i in range(800)],'score':np.ones(800)})
    out=rank_watchlist(df,max_reviews=40)
    assert out.selected.sum()==40
    assert out.loc[out.selected,'entity_id'].iloc[-1]=='E039'

def test_small_panel_no_rounding_up():
    df=pd.DataFrame({'entity_id':['a']*0,'score':[]})
    assert rank_watchlist(df).selected.sum()==0
    df=pd.DataFrame({'entity_id':list('abc'),'score':[.9,.8,.7]})
    assert rank_watchlist(df).selected.sum()==0

def test_duplicate_issuer_cannot_consume_two_slots():
    with pytest.raises(ValueError):rank_watchlist(pd.DataFrame({'entity_id':['a','a'],'score':[.1,.2]}))

def test_cost_arithmetic():
    y=np.r_[np.ones(20),np.zeros(780)]
    selected=np.zeros(800,dtype=bool);selected[:12]=True;selected[20:48]=True
    m=error_cost(y,selected)
    assert (m['tp'],m['fp'],m['fn'],m['cost'])==(12,28,8,188)

def test_strict_lead_calendar_and_boundary():
    assert str(lead_cutoff('2017-07-26',12).date())=='2016-06-30'
    assert str(lead_cutoff('2017-06-30',12).date())=='2016-06-30'
    assert str(lead_cutoff('2017-07-26',24).date())=='2015-06-30'

def test_asof_excludes_future_and_unverified_and_does_not_mix_fields():
    df=pd.DataFrame([
        dict(entity_id='A',period_end='2015-03-31',public_available_at='2015-07-01',verification_status='verified',publication_status='verified',sales=90),
        dict(entity_id='A',period_end='2016-03-31',public_available_at='2016-07-20',verification_status='verified',publication_status='verified',sales=100),
        dict(entity_id='B',period_end='2016-03-31',public_available_at='2016-05-20',verification_status='requires_review',publication_status='verified',sales=100),
    ])
    out=asof_financials(df,'2016-06-30')
    assert len(out)==1 and out.iloc[0].sales==90

def test_optimized_policy_has_capacity_and_no_test_input():
    y=np.r_[np.ones(10),np.zeros(190)];p=np.linspace(.99,.01,200)
    policy,curve=optimize_policy(y,p)
    assert policy['alerts']<=10
    assert policy['cost']==min(r['cost'] for r in curve)


@pytest.mark.parametrize('y,selected',[([.5],[1]),([0],['False']),([[0]],[[1]]),([0,1],[1])])
def test_cost_does_not_coerce_invalid_labels(y,selected):
    with pytest.raises(ValueError):error_cost(y,selected)

@pytest.mark.parametrize('capacity',[-1,1.5,True])
def test_invalid_capacity_rejected(capacity):
    with pytest.raises(ValueError):rank_watchlist(pd.DataFrame({'entity_id':['A'],'score':[.1]}),max_reviews=capacity)
