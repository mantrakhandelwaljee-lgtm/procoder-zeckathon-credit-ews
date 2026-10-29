"""Bhushan case research. Never promotes assumed publication to approved history."""
from pathlib import Path
import hashlib,json,math
import joblib,numpy as np,pandas as pd
from .accounting import COMMON,common_ratios,altman,beneish,piotroski
from .india import explain_model,NAMES,json_clean,driver_interpretation
from .policy import lead_cutoff
SCENARIOS=[('2013-12-31','earliest documented payment failure; contemporaneous indexed corroboration; first status not exhaustive'),('2014-04-01','later retrospective assertion with date inconsistency; not earliest documented'),('2014-08-26','subsequent contemporaneous trustee event; not earliest documented')]

def sensitivity_snapshot(accounts,cutoff):
    a=accounts.copy();keep=(pd.to_datetime(a.assumed_available_by)<=pd.Timestamp(cutoff))&(pd.to_datetime(a.period_end)<=pd.Timestamp(cutoff))
    return a[keep].sort_values(['entity_id','period_end','source_report_year']).groupby('entity_id').tail(1)

def source_integrity(root,docs):
    records=[]
    for d in docs.to_dict('records'):
        if d['status']!='downloaded':continue
        p=root/d['relative_path'];actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
        records.append(dict(document_id=d['document_id'],expected=d['sha256'],actual=actual,status='match' if actual==d['sha256'] else 'not_cached' if actual is None else 'mismatch'))
    if any(r['status']=='mismatch' for r in records):raise ValueError('Case source hash changed')
    return records

def fetch_sources(root,retry_failed=False):
    import requests,subprocess,datetime
    p=root/'data/curated/bhushan_documents.csv';rows=[]
    for row in pd.read_csv(p).fillna('').to_dict('records'):
        target=root/row['relative_path']
        if target.exists() or (row['status']!='downloaded' and not retry_failed):rows.append(row);continue
        try:
            response=requests.get(row['source_url'],timeout=45);response.raise_for_status();b=response.content
            if not b.startswith(b'%PDF'):raise ValueError('Non-PDF response; endpoint rejection retained')
            actual=hashlib.sha256(b).hexdigest()
            if row.get('sha256') and actual!=row['sha256']:raise ValueError('Hash mismatch; manual source version review required')
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
            tx=root/row['text_relative_path'];tx.parent.mkdir(parents=True,exist_ok=True)
            subprocess.run(['pdftotext','-layout',str(target),str(tx)],check=True,capture_output=True)
            row.update(status='downloaded',sha256=actual,bytes=len(b),error='',retrieved_at=datetime.date.today().isoformat())
        except Exception as e:row['error']=str(e)
        rows.append(row)
    pd.DataFrame(rows).to_csv(p,index=False)

def run(root):
    root=Path(root);d=root/'data/curated';out=root/'results/india/bhushan-case';out.mkdir(parents=True,exist_ok=True)
    a=pd.DataFrame(json.loads((d/'bhushan_case_accounts.json').read_text()));docs=pd.read_csv(d/'bhushan_documents.csv',dtype=str).fillna('')
    sources=pd.concat([pd.read_csv(d/'documents.csv',dtype=str).fillna(''),docs]).drop_duplicates('document_id',keep='last').set_index('document_id')
    integrity=source_integrity(root,docs);(out/'source-integrity.json').write_text(json.dumps(integrity,indent=2))
    checks=[];fields=[]
    numeric=['total_assets','total_liabilities','noncurrent_liabilities','current_assets','current_liabilities','equity','other_equity','inventory','receivables','sales','net_income','profit_before_tax','finance_costs','ebit','retained_earnings','long_term_debt','ppe','depreciation','cfo','capital_work_in_progress']
    for r in a.to_dict('records'):
        residual=r['total_assets']-r['equity']-r['other_equity']-r['total_liabilities']
        if abs(residual)>.011:raise ValueError(f"Unreconciled balance sheet: {r['entity_id']} {residual}")
        checks.append(dict(entity_id=r['entity_id'],period_end=r['period_end'],balance_residual_crore=residual,source_version=r['source_document_id'],historical_public_timestamp_verified=False))
        src=sources.loc[r['source_document_id']]
        for f in numeric:
            v=r.get(f)
            if v is None or not np.isfinite(v):continue
            kind='reserves' if f=='retained_earnings' else 'profit_loss' if f in ['sales','net_income','profit_before_tax','finance_costs','ebit','depreciation'] else 'balance'
            pages=[92] if f=='cfo' else r['source_pages'][kind]
            note=r['mapping_notes']
            if f=='total_liabilities':note='noncurrent_liabilities + current_liabilities; excludes separately reported equity-like items. '+note
            if f=='ebit':note='PBT after exceptional items + P&L finance_costs; not adjusted recurring EBIT. '+note
            fields.append(dict(entity_id=r['entity_id'],period_end=r['period_end'],field=f,value=v,unit='INR crore',source_document_id=r['source_document_id'],source_column=r['source_column'],source_url=src.source_url,source_sha256=src.sha256,pdf_pages=','.join(map(str,pages)),review_status='numeric_reviewed_mapping_pending',publication_status='unverified',note=note))
    pd.DataFrame(fields).to_csv(out/'field_sources.csv',index=False);pd.DataFrame(checks).to_csv(out/'accounting_checks.csv',index=False)
    a.drop(columns=['source_pages']).to_csv(out/'reviewed_accounts.csv',index=False)
    ratios=pd.DataFrame([common_ratios(r) for r in a.to_dict('records')])
    if ratios.isna().any().any():raise ValueError('Incomplete common case inputs')
    model=joblib.load(root/'results/benchmark/model.joblib');scores=model.predict_proba(ratios)[:,1];ex=explain_model(model,ratios,root)
    cards=[];contrib=[];rows=[]
    for i,r in enumerate(a.to_dict('records')):
        drivers=[]
        for j in np.argsort(-ex.values[i])[:3]:
            f=ratios.columns[j];eff=float(ex.values[i,j]);drivers.append(dict(feature=f,label=NAMES[f][0],value=float(ratios.iloc[i,j]),contribution=eff,direction='raises' if eff>=0 else 'reduces',interpretation=driver_interpretation(f,eff)))
        prev=a[(a.entity_id==r['entity_id'])&(a.period_end==f"{int(r['period_end'][:4])-1}-03-31")];prior=prev.iloc[0].to_dict() if len(prev) else {}
        card=dict(entity_id=r['entity_id'],period_end=r['period_end'],source_document_id=r['source_document_id'],score=float(scores[i]),score_type='transferred_Polish_score_not_Indian_PD',base_value=float(ex.base_values[i]),drivers=drivers,altman_z_double_prime_proxy=altman(r),beneish_m=beneish(r,prior),piotroski_f=piotroski(r,prior,{}),primary_eligible=False,publication_status='unverified',retained_earnings_mapping='core_earned_reserve_proxy_pending_approval')
        cards.append(card);rows.append(dict(entity_id=r['entity_id'],period_end=r['period_end'],source_document_id=r['source_document_id'],source_column=r['source_column'],score=scores[i],altman_z_double_prime_proxy=card['altman_z_double_prime_proxy']['score'],formal_alert=False,primary_eligible=False))
        for j,f in enumerate(ratios.columns):contrib.append(dict(entity_id=r['entity_id'],period_end=r['period_end'],feature=f,value=ratios.iloc[i,j],contribution=ex.values[i,j],base_value=ex.base_values[i]))
    pd.DataFrame(rows).to_csv(out/'scores.csv',index=False);pd.concat([a[['entity_id','period_end','source_document_id']],ratios],axis=1).to_csv(out/'ratios.csv',index=False)
    pd.DataFrame(contrib).to_csv(out/'shap_contributions.csv',index=False);(out/'evidence_cards.json').write_text(json.dumps(json_clean(cards),indent=2,allow_nan=False))
    replay=[]
    for date,status in SCENARIOS:
        for months in [12,24]:
            cutoff=lead_cutoff(date,months).date().isoformat();chosen=sensitivity_snapshot(a,cutoff)
            for entity in ['BHUSHAN','JSW','TATASTEEL','SAIL']:
                b=chosen[chosen.entity_id==entity]
                replay.append(dict(entity_id=entity,event_scenario=date,event_status=status,lead_months=months,cutoff=cutoff,strict_status='withheld_unverified_publication_and_endpoint',strict_score=None,sensitivity_status='AGM_assumption_only_mapping_pending' if len(b) else 'withheld_no_eligible_source_version',sensitivity_period_end=b.iloc[0].period_end if len(b) else None,sensitivity_source_document_id=b.iloc[0].source_document_id if len(b) else None,sensitivity_score=float(scores[int(b.index[0])]) if len(b) else None,formal_alert=False,recovered=None))
    pd.DataFrame(replay).to_csv(out/'lead_time_scenarios.csv',index=False)
    cohort=pd.DataFrame(rows);cohort=cohort[cohort.period_end=='2012-03-31'].sort_values(['score','entity_id'],ascending=[False,True]);cohort['descriptive_rank']=range(1,len(cohort)+1);cohort.to_csv(out/'fy2012_peer_comparison.csv',index=False)
    status=dict(status='case_dossier_completed_with_material_unresolved_evidence',numeric_examples=len(a),reviewed_issuers=4,first_default_status='earliest_documented_not_exhaustively_established',primary_replay_status='withheld',strict_recall_4q=None,strict_recall_8q=None,formal_capacity_slots=math.floor(.05*4),assumptions=['AGM report circulation is sensitivity only; no verified historical public timestamp.','Retained earnings is a disclosed core proxy; classification approval pending.','Peers remain provisional; historical nondefault follow-up not certified.'],main_finding=f"Frozen FY2012 model ranks BHUSHAN {int(cohort[cohort.entity_id=='BHUSHAN'].descriptive_rank.iloc[0])} of 4; no model tuning or success claim.",downloaded_additional_sources=int((docs.status=='downloaded').sum()),failed_additional_routes=int((docs.status=='failed').sum()),source_integrity_checked=sum(r['status']=='match' for r in integrity),source_integrity_not_cached=sum(r['status']=='not_cached' for r in integrity))
    (out/'status.json').write_text(json.dumps(status,indent=2));write_tables(cohort,cards,out);print(json.dumps(status,indent=2),flush=True);return status

def write_tables(cohort,cards,out):
    lines=['# Numerical evidence: Bhushan Steel case','','**Exploratory scores; publication, mapping and endpoint gates remain unresolved.**','FY2011 figures are later comparative versions and cannot be backdated. Input amounts are INR crore.','','| Issuer (FY2012) | Transferred score | Z\'\' proxy | Descriptive rank |','|---|---:|---:|---:|']
    for r in cohort.itertuples():lines.append(f'| {r.entity_id} | {r.score:.6f} | {r.altman_z_double_prime_proxy:.3f} | {r.descriptive_rank} |')
    lines+=['','Four companies yield zero formal 5% slots. These ranks are descriptive.','']
    for c in cards:
        if c['entity_id']!='BHUSHAN':continue
        lines += [f"## BHUSHAN {c['period_end']}",'',f"Transferred score **{c['score']:.6f}**; Z'' proxy **{c['altman_z_double_prime_proxy']['score']:.3f}**.",'']
        for dr in c['drivers']:lines.append(f"- **{dr['label']}** {dr['value']:.4f}; score contribution {dr['contribution']:+.5f}. {dr['interpretation']}")
        lines+=['','M/F screens remain incomplete. Missing fields and partial flags are recorded in `evidence_cards.json`.','']
    (out/'numerical-evidence.md').write_text('\n'.join(lines))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--retry-failed',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parents[1]
    if args.fetch:fetch_sources(root,args.retry_failed)
    run(root)
