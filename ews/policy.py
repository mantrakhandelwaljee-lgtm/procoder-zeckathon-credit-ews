"""Capacity, lead-time and error-cost definitions used by the backtest."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd

def error_cost(y, selected):
    y=np.asarray(y);selected=np.asarray(selected)
    if y.ndim!=1 or selected.ndim!=1 or len(y)!=len(selected) or not np.isin(y,[0,1]).all() or not np.isin(selected,[0,1]).all():
        raise ValueError('Labels and selections must be equally sized one-dimensional binary arrays')
    y=y.astype(int);selected=selected.astype(bool)
    tp=int(((y==1)&selected).sum()); fp=int(((y==0)&selected).sum())
    fn=int(((y==1)&~selected).sum()); tn=int(((y==0)&~selected).sum())
    return {'tp':tp,'fp':fp,'fn':fn,'tn':tn,'cost':20*fn+fp,
            'recall':tp/(tp+fn) if tp+fn else None,
            'precision':tp/(tp+fp) if tp+fp else None,'alerts':tp+fp}

def rank_watchlist(frame, score='score', rate=.05, threshold=None, max_reviews=None):
    if not 0<=rate<=1: raise ValueError('Invalid alert rate')
    if max_reviews is not None and (isinstance(max_reviews,bool) or not isinstance(max_reviews,(int,np.integer)) or max_reviews<0):
        raise ValueError('max_reviews must be a nonnegative integer')
    if frame.entity_id.isna().any() or not frame.entity_id.map(lambda x:isinstance(x,str) and bool(x.strip())).all():
        raise ValueError('Every ranked issuer requires a nonblank string ID')
    if frame.entity_id.duplicated().any(): raise ValueError('One row per issuer per quarter required')
    if not np.isfinite(frame[score]).all(): raise ValueError('Non-finite scores cannot be ranked')
    out=frame.sort_values([score,'entity_id'],ascending=[False,True]).copy()
    k=math.floor(rate*len(out)+1e-10)
    if max_reviews is not None: k=min(k,max_reviews)
    out['rank']=np.arange(1,len(out)+1)
    out['selected']=out['rank']<=k
    if threshold is not None: out['selected'] &= out[score]>threshold
    out['capacity']=k
    return out

def lead_cutoff(event_date, months):
    target=pd.Timestamp(event_date)-pd.DateOffset(months=months)
    return pd.Period(target,freq='Q').end_time.normalize() if target.is_quarter_end else (pd.Period(target,freq='Q')-1).end_time.normalize()

def optimize_policy(y, scores, rate=.05):
    """Choose k and score threshold using development predictions only, under capacity."""
    y=np.asarray(y); scores=np.asarray(scores)
    order=np.argsort(-scores,kind='stable'); cap=math.floor(rate*len(y)+1e-10)
    candidates=[]
    # Include all score ties together; a production rank cap provides deterministic final tie handling.
    for k in range(cap+1):
        selected=np.zeros(len(y),dtype=bool);selected[order[:k]]=True
        m=error_cost(y,selected)
        if k==0: threshold=float('inf')
        elif k==len(y): threshold=float('-inf')
        elif scores[order[k-1]]==scores[order[k]]: continue
        else: threshold=float((scores[order[k-1]]+scores[order[k]])/2)
        candidates.append({**m,'k':k,'threshold':threshold})
    best=min(candidates,key=lambda x:(x['cost'],x['alerts']))
    return best,candidates

def asof_financials(facts, cutoff, require_verified=True):
    """One latest complete accounting record per issuer. Never backfill individual fields."""
    x=facts.copy();cutoff=pd.Timestamp(cutoff)
    x['public_available_at']=pd.to_datetime(x['public_available_at'],errors='coerce')
    x['period_end']=pd.to_datetime(x['period_end'])
    x=x[(x.public_available_at<=cutoff)&(x.period_end<=cutoff)]
    if require_verified:
        x=x[(x.verification_status=='verified')&(x.publication_status=='verified')]
    if not x.empty and x.duplicated(['entity_id','period_end','public_available_at']).any():
        raise ValueError('Ambiguous financial versions at the same availability date')
    if x.empty: return x
    return x.sort_values(['entity_id','period_end','public_available_at']).drop_duplicates('entity_id',keep='last')
