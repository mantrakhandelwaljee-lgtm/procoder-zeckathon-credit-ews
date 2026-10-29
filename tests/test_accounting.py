import pytest
from ews.accounting import common_ratios, beneish, piotroski, altman

@pytest.fixture
def accounts():
    return dict(total_assets=100,current_assets=40,current_liabilities=20,total_liabilities=60,
        equity=40,retained_earnings=10,ebit=15,net_income=10,net_income_before_extraordinary=10,sales=100,inventory=10,
        receivables=20,cogs=60,ppe=30,depreciation=5,sga=10,long_term_debt=30,long_term_debt_including_current_maturities=30,
        income_continuing_operations=10,cfo=10,equity_issued=False)

def test_common_definition_and_negative_equity(accounts):
    r=common_ratios(accounts)
    assert r['X3']==pytest.approx(.2)
    assert r['X20']==pytest.approx(36.5)
    assert r['X44']==pytest.approx(73)
    accounts['equity']=-10
    assert common_ratios(accounts)['X8']==pytest.approx(-1/6)

def test_beneish_unchanged_accounts_gold_value(accounts):
    x=beneish(accounts,accounts)
    assert all(v==1 for k,v in x['components'].items() if k!='TATA')
    assert x['components']['TATA']==0
    assert x['score']==pytest.approx(-2.48)

def test_beneish_missing_sga_is_not_zero(accounts):
    prior=accounts.copy();prior.pop('sga')
    assert beneish(accounts,prior)['score'] is None
    assert 'prior.sga' in beneish(accounts,prior)['missing']

def test_piotroski_beginning_assets_and_actual_issuance(accounts):
    current=accounts|{'cfo':11}
    assert piotroski(current,accounts,accounts)['score']==4
    current['equity_issued']=True
    assert piotroski(current,accounts,accounts)['score']==3
    assert piotroski(current,accounts,{})['score'] is None

def test_altman_variants_are_distinct(accounts):
    x=altman(accounts)
    expected=6.56*.2+3.26*.1+6.72*.15+1.05*(40/60)
    assert x['score']==pytest.approx(expected)
    assert altman(accounts,'public_manufacturing')['score'] is None

def test_no_division_by_nonpositive_assets(accounts):
    accounts['total_assets']=0
    assert common_ratios(accounts)['X1'] is None
    assert altman(accounts)['score'] is None

def test_beneish_against_author_affiliated_sunbeam_example():
    # Independent published example: https://apps.kelley.iu.edu/Beneish/Content/Examples/SunbeamExample.pdf
    c=dict(receivables=295.6,current_assets=658,current_liabilities=198.1,total_assets=1120.3,ppe=240.9,
           long_term_debt=194.6,sales=1168.2,depreciation=38.6,cogs=837.7,sga=131,cfo=-8.2,income_continuing_operations=109.4)
    p=dict(receivables=213.4,current_assets=624.2,current_liabilities=271.6,total_assets=1072.7,ppe=220.1,
           long_term_debt=201.1,sales=984.2,depreciation=47.4,cogs=900.6,sga=214)
    result=beneish(c,p)
    assert result['score']==pytest.approx(-1.884,abs=.0005)
    assert result['components']['DSRI']==pytest.approx(1.1670,abs=.00005)

def test_nonannual_periods_are_not_silently_annual(accounts):
    nonannual=accounts|{'period_months':18}
    assert common_ratios(nonannual)['X1'] is None
    assert common_ratios(nonannual)['X7'] is None
    assert beneish(nonannual,accounts)['score'] is None
    assert piotroski(nonannual,accounts,accounts)['score'] is None


def test_piotroski_average_assets_changes_leverage_signal(accounts):
    # Year-end denominators falsely imply falling leverage: 55/200 < 30/100.
    # The paper's average assets give 55/150 > 30/150: leverage worsens.
    older=accounts|{'total_assets':200}
    prior=accounts|{'total_assets':100,'long_term_debt_including_current_maturities':30}
    current=accounts|{'total_assets':200,'long_term_debt_including_current_maturities':55}
    assert piotroski(current,prior,older)['components']['lower_leverage']==0
    assert piotroski(current,prior,{})['components']['lower_leverage'] is None


def test_issuance_string_cannot_invert_boolean(accounts):
    with pytest.raises(ValueError):piotroski(accounts|{'equity_issued':'False'},accounts,accounts)


def test_piotroski_generic_debt_and_profit_are_not_unverified_proxies(accounts):
    c=accounts.copy();c.pop('net_income_before_extraordinary');c.pop('long_term_debt_including_current_maturities')
    result=piotroski(c,accounts,accounts)
    assert result['score'] is None
    assert result['components']['lower_leverage'] is None
    assert result['components']['positive_roa'] is None
