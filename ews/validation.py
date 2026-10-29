"""Validate approved inputs before any primary historical result can be emitted."""
import re
import numpy as np
import pandas as pd

ACCOUNT_FIELDS=['total_assets','total_liabilities','current_assets','current_liabilities','equity','other_equity','retained_earnings','ebit','net_income','sales','inventory','receivables']
ACCOUNT_META=['entity_id','period_end','period_months','public_available_at','verification_status','publication_status','accounting_mapping_status','source_document_id','source_url','source_sha256','source_pages','basis']
POPULATION_FIELDS=['entity_id','role','sector','listed_from','observed_through','default_date','endpoint_status','qualification_status','qualification_evidence_ref','match_case_id','match_status','match_evidence_ref']

def require_columns(frame,columns,label):
    missing=set(columns)-set(frame)
    if missing:raise ValueError(f'Missing {label} fields: {sorted(missing)}')

def nonblank(frame,columns):
    for col in columns:
        if not frame[col].map(lambda x:isinstance(x,str) and bool(x.strip())).all():
            raise ValueError(f'{col} requires nonblank text/evidence')

def dates(series,name,allow_blank=False):
    out=[]
    for v in series:
        blank=pd.isna(v) or (isinstance(v,str) and not v.strip())
        if blank and allow_blank:out.append(pd.NaT);continue
        if not isinstance(v,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',v):
            raise ValueError(f'{name} must be a valid ISO date YYYY-MM-DD; malformed values cannot become healthy labels')
        try:out.append(pd.Timestamp(v))
        except (ValueError,TypeError) as exc:raise ValueError(f'Invalid {name}: {v}') from exc
    return pd.Series(out,index=series.index,dtype='datetime64[ns]')

def population(frame):
    require_columns(frame,POPULATION_FIELDS,'population');e=frame.copy()
    nonblank(e,['entity_id','role','sector','qualification_evidence_ref','endpoint_status'])
    if e.entity_id.duplicated().any():raise ValueError('Duplicate population entity')
    if not e.role.isin(['case','peer']).all():raise ValueError('Unknown population role')
    if not e.qualification_status.eq('verified').all():raise ValueError('Unverified population qualification')
    cases=e.role.eq('case');peers=e.role.eq('peer')
    if cases.sum()<10 or peers.sum()<30:raise ValueError('Requires at least 10 cases and 30 distinct qualified peers')
    for c in ['listed_from','observed_through']:e[c]=dates(e[c],c)
    e['default_date']=dates(e.default_date,'default_date',allow_blank=True)
    if (e.observed_through<e.listed_from).any():raise ValueError('Follow-up cannot precede listing')
    if (e.default_date.notna()&((e.default_date<e.listed_from)|(e.default_date>e.observed_through))).any():
        raise ValueError('Default must fall within the verified listed observation window')
    if e.loc[cases,'default_date'].isna().any() or not e.loc[cases,'endpoint_status'].eq('verified_first_default').all():
        raise ValueError('Primary evaluation requires exact verified first-default endpoints, not later CIRP dates')
    healthy=peers&e.default_date.isna();later_default=peers&e.default_date.notna()
    if not e.loc[healthy,'endpoint_status'].eq('verified_nondefault_horizon').all():raise ValueError('Peers require verified non-default follow-up')
    if not e.loc[later_default,'endpoint_status'].eq('verified_first_default').all():raise ValueError('A later-defaulting peer needs a verified first-default endpoint')
    p=e[peers];nonblank(p,['match_case_id','match_evidence_ref'])
    if not p.match_status.eq('verified').all():raise ValueError('Unverified peer matching')
    case_sectors=e[cases].set_index('entity_id').sector
    if not p.match_case_id.isin(case_sectors.index).all():raise ValueError('Peer references unknown matched case')
    if not p.sector.eq(p.match_case_id.map(case_sectors)).all():raise ValueError('Matched peers must have the same sector as the case')
    if set(case_sectors.index)-set(p.match_case_id):raise ValueError('Every case requires a documented peer match')
    return e

def accounts(frame,entity_ids):
    require_columns(frame,ACCOUNT_META+ACCOUNT_FIELDS,'accounting');a=frame.copy()
    nonblank(a,['entity_id','basis','source_document_id','source_url','source_sha256','source_pages'])
    if not a.entity_id.isin(entity_ids).all():raise ValueError('Accounting input contains an unknown issuer')
    if not a.basis.isin(['standalone','consolidated']).all() or a.groupby('entity_id').basis.nunique().gt(1).any():
        raise ValueError('Use one explicit accounting basis per issuer')
    for c in ['verification_status','publication_status','accounting_mapping_status']:
        if not a[c].eq('verified').all():raise ValueError(f'Primary accounting requires {c}=verified; exploratory proxies cannot pass')
    a['period_end']=dates(a.period_end,'period_end');a['public_available_at']=dates(a.public_available_at,'public_available_at')
    if (a.public_available_at<a.period_end).any():raise ValueError('A complete financial period cannot be published before its end')
    if a.duplicated(['entity_id','period_end','public_available_at']).any():raise ValueError('Ambiguous accounting versions at same publication date')
    if not pd.to_numeric(a.period_months,errors='coerce').eq(12).all():raise ValueError('Primary input requires verified twelve-month periods')
    a['period_months']=12
    if not a.source_sha256.str.fullmatch(r'[0-9a-f]{64}').all():raise ValueError('Every accounting version requires a SHA-256 source reference')
    if not a.source_url.str.match(r'^https?://').all() or not a.source_pages.str.fullmatch(r'[1-9]\d*(?:,[1-9]\d*)*').all():
        raise ValueError('Accounting provenance requires a public source URL and comma-separated positive PDF pages')
    for c in ACCOUNT_FIELDS:a[c]=pd.to_numeric(a[c],errors='coerce')
    if not np.isfinite(a[ACCOUNT_FIELDS].to_numpy(dtype=float)).all():raise ValueError('Required accounting values must be finite and complete')
    if (a[['total_assets','total_liabilities','current_liabilities','sales']]<=0).any().any():raise ValueError('Invalid nonpositive accounting denominator')
    if (a[['current_assets','inventory','receivables']]<0).any().any():raise ValueError('Negative asset component')
    tol=np.maximum(.02,a.total_assets.abs()*1e-6)
    if ((a.current_assets>a.total_assets+tol)|(a.inventory+a.receivables>a.current_assets+tol)|(a.current_liabilities>a.total_liabilities+tol)).any():
        raise ValueError('Accounting components do not reconcile with their totals')
    residual=a.total_assets-a.total_liabilities-a.equity-a.other_equity
    if (residual.abs()>tol).any():raise ValueError('Gross assets must reconcile to liabilities and separately identified equity components')
    return a
