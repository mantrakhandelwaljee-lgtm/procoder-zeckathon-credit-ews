"""Real historical replay once a fully approved panel is supplied.

Approval input schema is in docs/DATA_REVIEW.md. This module does not use the
unreviewed extraction candidates or any assumed publication lag.
"""
from pathlib import Path
import json
import hashlib
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from .accounting import COMMON,common_ratios
from .policy import asof_financials,rank_watchlist,error_cost,lead_cutoff
from . import validation

def approved_population(entities):
    return validation.population(entities)

def replay(accounts,entities,model,cutoffs):
    """Rank a contemporaneous eligible universe; never shrink it to the complete cases."""
    entities=approved_population(entities)
    accounts=validation.accounts(accounts,entities.entity_id)
    rows=[];rankings=[]
    for cutoff in pd.to_datetime(cutoffs):
        e=entities[(entities.listed_from<=cutoff)&(entities.default_date.isna()|(entities.default_date>cutoff))]
        a=asof_financials(accounts,cutoff)
        a=a[a.entity_id.isin(e.entity_id)]
        missing=sorted(set(e.entity_id)-set(a.entity_id))
        if missing or len(e)==0:
            rows.append({'cutoff':cutoff.date().isoformat(),'status':'missing_verified_financials',
                         'eligible_count':len(e),'missing_count':len(missing),'missing_entities':';'.join(missing)})
            continue
        a=a.set_index('entity_id').loc[e.entity_id].reset_index()
        X=pd.DataFrame([common_ratios(r) for r in a.to_dict('records')])
        if X.isna().any().any():
            rows.append({'cutoff':cutoff.date().isoformat(),'status':'incomplete_required_ratios','eligible_count':len(e)})
            continue
        scores=model.predict_proba(X[list(COMMON)])[:,1]
        queue=rank_watchlist(pd.DataFrame({'entity_id':e.entity_id.to_numpy(),'score':scores}),max_reviews=40)
        queue['cutoff']=cutoff.date().isoformat();rankings.append(queue)
        for h in [12,24]:
            end=cutoff+pd.DateOffset(months=h)
            labels=e.default_date.notna()&(e.default_date<=end)
            observed=labels|(e.observed_through>=end)
            if not observed.all():
                rows.append({'cutoff':cutoff.date().isoformat(),'horizon_months':h,'status':'censored_outcomes',
                             'eligible_count':len(e),'unknown_outcomes':int((~observed).sum())})
                continue
            ordered=queue.set_index('entity_id').reindex(e.entity_id)
            stats=error_cost(labels.astype(int),ordered.selected.to_numpy())
            rows.append({'cutoff':cutoff.date().isoformat(),'horizon_months':h,'status':'evaluated',
                         'eligible_count':len(e),**stats})
    rank=pd.concat(rankings,ignore_index=True) if rankings else pd.DataFrame(columns=['entity_id','score','rank','selected','capacity','cutoff'])
    lead_rows=[]
    for r in entities[entities.role=='case'].itertuples():
        for h in [12,24]:
            cutoff=lead_cutoff(r.default_date,h).date().isoformat()
            match=rank[(rank.entity_id==r.entity_id)&(rank.cutoff==cutoff)]
            lead_rows.append({'entity_id':r.entity_id,'lead_months':h,'cutoff':cutoff,
                'actual_lead_days':(r.default_date-pd.Timestamp(cutoff)).days,
                'recovered':None if match.empty else bool(match.iloc[0].selected),
                'status':'unavailable' if match.empty else 'evaluated'})
    leads=pd.DataFrame(lead_rows)
    summary={}
    for h in [12,24]:
        sub=leads[leads.lead_months==h];valid=sub[sub.status=='evaluated']
        recovered=int(valid.recovered.fillna(False).sum())
        summary[f'recall_{h}m']={'case_denominator':len(sub),'evaluated_cases':len(valid),'recovered_cases':recovered,
            'all_case_recall_missing_counted_as_miss':recovered/len(sub) if len(sub) else None,
            'complete_case_recall':recovered/len(valid) if len(valid) else None}
    return pd.DataFrame(rows),rank,leads,summary

def invalidate_previous(out):
    """Archive known generated metrics so a failed/new run cannot display stale success."""
    names=['quarterly_metrics.csv','rankings.csv','lead_outcomes.csv','summary.json','status.json']
    existing=[out/n for n in names if (out/n).exists()]
    if existing:
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        target=out/'superseded'/stamp;target.mkdir(parents=True)
        for p in existing:p.rename(target/p.name)


def run_if_approved(root):
    root=Path(root);d=root/'data/curated';out=root/'results/india/primary';out.mkdir(parents=True,exist_ok=True)
    invalidate_previous(out)
    population=d/'approved_population.csv';accounts=d/'approved_accounts.csv'
    if not population.exists() or not accounts.exists():
        (out/'status.json').write_text(json.dumps({'status':'not_run',
            'reason':'Approved full population and publication-verified accounts not yet supplied; draft candidates are excluded.',
            'required_inputs':['data/curated/approved_population.csv','data/curated/approved_accounts.csv']},indent=2))
        return
    import joblib
    provenance={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [population,accounts,root/'results/benchmark/model.joblib']}
    try:
        e=pd.read_csv(population,dtype=str);a=pd.read_csv(accounts,dtype=str)
        from .evidence import load_documents
        docs=load_documents(root).set_index('document_id')
        for record in a.to_dict('records'):
            doc_id=record.get('source_document_id')
            if doc_id not in docs.index:raise ValueError(f'Unknown accounting source document: {doc_id}')
            source=docs.loc[doc_id]
            if source.status!='downloaded' or record.get('source_sha256')!=source.sha256 or record.get('source_url')!=source.source_url:
                raise ValueError(f'Accounting source provenance does not match manifest: {doc_id}')
        model=joblib.load(root/'results/benchmark/model.joblib')
        cutoffs=pd.date_range('2011-03-31','2022-06-30',freq='QE')
        metrics,rank,leads,summary=replay(a,e,model,cutoffs)
    except Exception as exc:
        (out/'status.json').write_text(json.dumps({'status':'invalid_input_or_execution_failed',
            'reason':str(exc),'input_sha256':provenance},indent=2))
        raise
    metrics.to_csv(out/'quarterly_metrics.csv',index=False);rank.to_csv(out/'rankings.csv',index=False)
    leads.to_csv(out/'lead_outcomes.csv',index=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    (out/'status.json').write_text(json.dumps({'status':'executed_on_approved_inputs',
        'input_sha256':provenance,'evaluated_quarter_horizons':int((metrics.status=='evaluated').sum()),
        'warning':'Inspect unavailable quarters, follow-up censoring and complete-case versus all-case denominators.'},indent=2))
