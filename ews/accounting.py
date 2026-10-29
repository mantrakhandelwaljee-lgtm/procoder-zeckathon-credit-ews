"""Explicit financial definitions; incomplete screens stay incomplete."""
from __future__ import annotations
import math

COMMON = {
    'X1': 'net_income / total_assets',
    'X2': 'total_liabilities / total_assets',
    'X3': '(current_assets - current_liabilities) / total_assets',
    'X4': 'current_assets / current_liabilities',
    'X6': 'retained_earnings / total_assets',
    'X7': 'ebit / total_assets',
    'X8': 'equity / total_liabilities',
    'X9': 'sales / total_assets',
    'X20': 'inventory * 365 / sales',
    'X23': 'net_income / sales',
    'X44': 'receivables * 365 / sales',
    'X46': '(current_assets - inventory) / current_liabilities',
}

def value(d, key):
    x = d.get(key)
    try:
        return float(x) if x is not None and math.isfinite(float(x)) else None
    except (ValueError, TypeError):
        return None

def div(a, b):
    if a is None or b is None or b <= 0:
        return None
    return a / b

def sub(a, b):
    return None if a is None or b is None else a - b

def common_ratios(d):
    v = {k: value(d, k) for k in ['net_income','total_assets','total_liabilities',
        'current_assets','current_liabilities','retained_earnings','ebit','equity',
        'sales','inventory','receivables']}
    ta, cl, tl, sales = (v[k] for k in ['total_assets','current_liabilities','total_liabilities','sales'])
    annual = d.get('period_months', 12) == 12
    return {
        'X1': div(v['net_income'], ta) if annual else None, 'X2': div(tl, ta),
        'X3': div(sub(v['current_assets'], cl), ta),
        'X4': div(v['current_assets'], cl), 'X6': div(v['retained_earnings'], ta),
        'X7': div(v['ebit'], ta) if annual else None, 'X8': div(v['equity'], tl),
        'X9': div(sales, ta) if annual else None,
        'X20': div(None if v['inventory'] is None else v['inventory'] * 365, sales) if annual else None,
        'X23': div(v['net_income'], sales),
        'X44': div(None if v['receivables'] is None else v['receivables'] * 365, sales) if annual else None,
        'X46': div(sub(v['current_assets'], v['inventory']), cl),
    }

def beneish(current, prior):
    """Eight-variable 1999 coefficient specification; no universal threshold asserted.

    TATA uses continuing-operations income minus operating cash flow, / assets.
    PPE is net PPE; SG&A and COGS must have separately verified definitions.
    """
    if any(d.get('period_months',12)!=12 for d in [current,prior]):
        return {'score':None,'components':{},'missing':['non_12_month_period_requires_verified_TTM_reconstruction'],'specification':'Beneish-8-1999'}
    required = ['sales','receivables','cogs','current_assets','ppe','total_assets',
                'depreciation','sga','current_liabilities','long_term_debt']
    missing = [f'{period}.{k}' for period,d in [('current',current),('prior',prior)]
               for k in required if value(d,k) is None]
    missing += [f'current.{k}' for k in ['income_continuing_operations','cfo'] if value(current,k) is None]
    if missing:
        return {'score': None, 'components': {}, 'missing': missing, 'specification':'Beneish-8-1999'}
    c = {k:value(current,k) for k in required + ['income_continuing_operations','cfo']}
    p = {k:value(prior,k) for k in required}
    def asset_quality(x):
        a = div(x['current_assets'] + x['ppe'], x['total_assets'])
        return None if a is None else 1-a
    def dep_rate(x): return div(x['depreciation'], x['ppe']+x['depreciation'])
    def leverage(x): return div(x['current_liabilities']+x['long_term_debt'], x['total_assets'])
    comp = {
        'DSRI': div(div(c['receivables'],c['sales']),div(p['receivables'],p['sales'])),
        'GMI': div(div(p['sales']-p['cogs'],p['sales']),div(c['sales']-c['cogs'],c['sales'])),
        'AQI': div(asset_quality(c),asset_quality(p)),
        'SGI': div(c['sales'],p['sales']),
        'DEPI': div(dep_rate(p),dep_rate(c)),
        'SGAI': div(div(c['sga'],c['sales']),div(p['sga'],p['sales'])),
        'LVGI': div(leverage(c),leverage(p)),
        'TATA': div(c['income_continuing_operations']-c['cfo'],c['total_assets']),
    }
    invalid = [k for k,v in comp.items() if v is None]
    weights = {'DSRI':.920,'GMI':.528,'AQI':.404,'SGI':.892,
               'DEPI':.115,'SGAI':-.172,'TATA':4.679,'LVGI':-.327}
    score = None if invalid else -4.840 + sum(weights[k]*comp[k] for k in weights)
    return {'score':score,'components':comp,'missing':invalid,'specification':'Beneish-8-1999',
            'interpretation':'Accounting-risk screen; not proof of manipulation. No fitted Indian fraud threshold.'}

def piotroski(current, prior, older):
    """Beginning-assets ROA/CFO/turnover (paper section 2.3); average-assets leverage.

    Debt explicitly includes current maturities. Profit explicitly excludes
    extraordinary items. Shared generic NI/debt fields are not presumed mapped.
    """
    if any(d.get('period_months',12)!=12 for d in [current,prior,older]):
        return {'score':None,'components':{},'missing':['non_12_month_period_requires_verified_TTM_reconstruction'],'specification':'Piotroski-2000-beginning-assets'}
    c,p,o = current,prior,older
    roa = div(value(c,'net_income_before_extraordinary'),value(p,'total_assets'))
    prev_roa = div(value(p,'net_income_before_extraordinary'),value(o,'total_assets'))
    cfo = div(value(c,'cfo'),value(p,'total_assets'))
    def average_assets(first,second):
        a,b=value(first,'total_assets'),value(second,'total_assets')
        return None if a is None or b is None or a<=0 or b<=0 else (a+b)/2
    lev = div(value(c,'long_term_debt_including_current_maturities'),average_assets(c,p))
    prev_lev = div(value(p,'long_term_debt_including_current_maturities'),average_assets(p,o))
    liq = div(value(c,'current_assets'),value(c,'current_liabilities'))
    prev_liq = div(value(p,'current_assets'),value(p,'current_liabilities'))
    margin = div(sub(value(c,'sales'),value(c,'cogs')),value(c,'sales'))
    prev_margin = div(sub(value(p,'sales'),value(p,'cogs')),value(p,'sales'))
    turn = div(value(c,'sales'),value(p,'total_assets'))
    prev_turn = div(value(p,'sales'),value(o,'total_assets'))
    def gt(a,b): return None if a is None or b is None else int(a>b)
    issued = c.get('equity_issued')
    if issued is not None and not isinstance(issued,bool):
        raise ValueError('equity_issued must be a reviewed boolean or None, not a string/share-count proxy')
    components = {'positive_roa':gt(roa,0),'positive_cfo':gt(cfo,0),
        'improving_roa':gt(roa,prev_roa),'cash_above_earnings':gt(cfo,roa),
        'lower_leverage':gt(prev_lev,lev),'higher_liquidity':gt(liq,prev_liq),
        'no_equity_issue':None if issued is None else int(not issued),
        'higher_gross_margin':gt(margin,prev_margin),'higher_asset_turnover':gt(turn,prev_turn)}
    missing=[k for k,v in components.items() if v is None]
    return {'score':None if missing else sum(components.values()),'components':components,
            'missing':missing,'specification':'Piotroski-2000-beginning-assets'}

def altman(d, variant='z_double_prime'):
    """Z'' (no emerging-market +3.25 intercept) or original public manufacturing Z."""
    r=common_ratios(d)
    if variant == 'z_double_prime':
        terms={'working_capital_assets':(r['X3'],6.56),'retained_earnings_assets':(r['X6'],3.26),
               'ebit_assets':(r['X7'],6.72),'book_equity_liabilities':(r['X8'],1.05)}
    elif variant == 'public_manufacturing':
        terms={'working_capital_assets':(r['X3'],1.2),'retained_earnings_assets':(r['X6'],1.4),
               'ebit_assets':(r['X7'],3.3),
               'market_equity_liabilities':(div(value(d,'market_equity'),value(d,'total_liabilities')),.6),
               'sales_assets':(r['X9'],.999)}
    else: raise ValueError('Unsupported Altman variant')
    missing=[k for k,(v,w) in terms.items() if v is None]
    return {'score':None if missing else sum(v*w for v,w in terms.values()),
            'components':{k:v for k,(v,w) in terms.items()},'missing':missing,'variant':variant,
            'interpretation':'Industrial/non-financial screen; not a calibrated Indian default probability.'}
