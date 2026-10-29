"""Indian evidence pilot and guarded historical replay. No invented portfolio metrics."""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from .accounting import COMMON,common_ratios,altman,beneish,piotroski
from .benchmark import load_data,SEED
from .policy import rank_watchlist,lead_cutoff,asof_financials
from .evidence import load_documents,reviewed_versions

NAMES={
'X1':('Return on assets','Check recurring profitability and reconcile earnings with operating cash flow.'),
'X2':('Liabilities / assets','Review funding dependence, creditor protection and upcoming refinancing.'),
'X3':('Working capital / assets','Review short-term funding needs and the realizability of current assets.'),
'X4':('Current ratio','Check accessible cash, restricted balances and liability maturities.'),
'X6':('Retained earnings / assets','Verify earned-reserve classifications and the buffer against further losses.'),
'X7':('EBIT / assets','Review recurring operating earnings and their capacity to cover financing costs.'),
'X8':('Book equity / liabilities','Assess the equity cushion and the recoverable value of assets backing creditor claims.'),
'X9':('Sales / assets','Review asset utilization against comparable businesses and project maturity.'),
'X20':('Inventory days relative to sales','Check stock realization, obsolescence and sector-specific inventory needs.'),
'X23':('Net margin','Investigate sustainable margins, exceptional items and financing expense.'),
'X44':('Receivable days relative to sales','Check collection delays, revenue recognition and receivable ageing.'),
'X46':('Quick ratio','Assess readily realizable assets against short-term obligations.'),
}


def driver_interpretation(feature,effect):
    direction='raises' if effect>=0 else 'reduces'
    return f'This observed value {direction} the model score relative to the Polish background. {NAMES[feature][1]}'


def json_clean(obj):
    if isinstance(obj,dict):return {k:json_clean(v) for k,v in obj.items()}
    if isinstance(obj,list):return [json_clean(v) for v in obj]
    if isinstance(obj,np.generic):obj=obj.item()
    if isinstance(obj,float) and not np.isfinite(obj):return None
    return obj

def explain_model(model,X,root):
    import shap
    clean,_=load_data(root/'data/raw/polish-bankruptcy.zip')
    splits=pd.read_csv(root/'results/benchmark/frozen_split.csv')
    dev=clean.loc[splits.split=='development',list(COMMON)]
    background=dev.sample(32,random_state=SEED)
    # Explanation model is the actual calibrated ensemble used for the displayed score.
    def predict(a):return model.predict_proba(pd.DataFrame(a,columns=list(COMMON)))[:,1]
    explainer=shap.PermutationExplainer(predict,background,feature_names=list(COMMON),seed=SEED)
    explanation=explainer(X,max_evals=25*20,silent=True)
    assert np.allclose(explanation.values.sum(axis=1)+explanation.base_values,predict(X),atol=1e-6)
    return explanation

def pilot(root,accounts):
    root=Path(root);out=root/'results/india';out.mkdir(parents=True,exist_ok=True)
    current=accounts[accounts.period_end=='2016-03-31'].copy().sort_values('entity_id')
    ratios=pd.DataFrame([common_ratios(r) for r in current.to_dict('records')],index=current.entity_id)
    if ratios.isna().any().any():raise ValueError('Reviewed pilot unexpectedly missing a deployed ratio')
    model=joblib.load(root/'results/benchmark/model.joblib')
    current['score']=model.predict_proba(ratios)[:,1]
    current['score_type']='transferred_Polish_risk_score_not_calibrated_Indian_PD'
    ranges=pd.read_csv(root/'results/benchmark/training_feature_ranges.csv').set_index('feature')
    current['outside_training_clip_range']=((ratios<ranges.low)|(ratios>ranges.high)).sum(axis=1).to_numpy()
    explanations=explain_model(model,ratios,root)
    cards=[];contrib=[]
    for i,r in enumerate(current.to_dict('records')):
        entity=r['entity_id'];vals=ratios.loc[entity]
        order=np.argsort(-explanations.values[i])
        drivers=[]
        for j in order[:3]:
            feature=ratios.columns[j];effect=float(explanations.values[i,j])
            direction='raises' if effect>=0 else 'reduces'
            concern=driver_interpretation(feature,effect)
            drivers.append({'feature':feature,'label':NAMES[feature][0],'value':float(vals[feature]),
                'score_contribution':effect,'direction':direction,'credit_interpretation':concern,
                'source_document_id':r['source_document_id'],
                'caution':'Association relative to Polish training background; sector/domain effects may dominate.'})
        prior=accounts[(accounts.entity_id==entity)&(accounts.period_end=='2015-03-31')].iloc[0].to_dict()
        card={'entity_id':entity,'period_end':r['period_end'],'source_document_id':r['source_document_id'],
            'source_url':r['source_url'],'score':r['score'],'score_type':r['score_type'],
            'historical_use_status':'excluded_from_primary_backtest_pending_publication_verification',
            'shap_base_value':float(explanations.base_values[i]),'drivers':drivers,
            'altman_z_double_prime':altman(r),'beneish_m':beneish(r,prior),
            'piotroski_f':piotroski(r,prior,{}),
            'missing_screen_context':'COGS, SG&A, actual issuance and older beginning assets are not fully verified; incomplete scores remain null.',
            'outside_training_clip_range':r['outside_training_clip_range']}
        cards.append(card)
        for j,feature in enumerate(ratios.columns):contrib.append({'entity_id':entity,'feature':feature,
            'value':vals[feature],'contribution':explanations.values[i,j],'base_value':explanations.base_values[i]})
    current['altman_z_double_prime']=[altman(r)['score'] for r in current.to_dict('records')]
    # This four-name evidence pilot is too small to have even one 5% review slot.
    ranked=rank_watchlist(current[['entity_id','score','score_type','altman_z_double_prime','outside_training_clip_range']])
    ranked['status']='evidence_pilot_only_publication_dates_pending'
    ranked.to_csv(out/'pilot_scores.csv',index=False)
    ratios.to_csv(out/'pilot_ratios.csv')
    pd.DataFrame(contrib).to_csv(out/'pilot_shap_contributions.csv',index=False)
    (out/'pilot_evidence_cards.json').write_text(json.dumps(json_clean(cards),indent=2,allow_nan=False))
    write_cards(cards,out)
    return ranked

def write_cards(cards,out):
    lines=['# Indian evidence pilot','',
      '**These are source-reviewed financial examples, not a validated historical watch-list.**',
      'Historical publication dates remain unverified. No four- or eight-quarter recovery claim is made.',
      'Scores are transferred from the Polish benchmark and are not calibrated Indian default probabilities.',
      'A four-company universe has floor(4 x 5%) = 0 formal alert slots. All four are shown for evidence review only.','']
    for c in sorted(cards,key=lambda c:-c['score']):
        lines += [f"## {c['entity_id']} | FY2016",'',f"Transferred risk score: **{c['score']:.4f}**. Altman Z'' screen: **{c['altman_z_double_prime']['score']:.3f}**.",
          f"Source: [original annual report]({c['source_url']}); field-level PDF pages are in `pilot_field_sources.csv`.",'',
          'The actual calibrated ensemble is explained using permutation SHAP with a development-only background. Contributions sum to the displayed score relative to the baseline.','']
        for d in c['drivers']:
            lines += [f"- **{d['label']} = {d['value']:.4f}**; contribution {d['score_contribution']:+.4f}. {d['credit_interpretation']}"]
        lines += ['',"Beneish M-Score: **incomplete**. Piotroski F-Score: **incomplete**. Missing required data is recorded in the JSON card; no replacement zero or invented score is used.",'',
                  'Investigation: verify publication timing, accounting definitions, liquidity availability, group exposure and debt maturities before any credit action.','']
    (out/'pilot-evidence-cards.md').write_text('\n'.join(lines))

def readiness(root,accounts):
    root=Path(root);d=root/'data/curated';out=root/'results/india';out.mkdir(parents=True,exist_ok=True)
    entities=pd.read_csv(d/'entities.csv');docs=load_documents(root);facts=pd.read_csv(d/'financial_candidates.csv')
    versions=reviewed_versions(root,accounts)
    events=pd.read_csv(d/'events.csv')
    core=entities[entities.role.isin(['case','peer'])]
    quarters=pd.date_range('2012-03-31','2022-06-30',freq='QE')
    rows=[]
    for q in quarters:
        valid=asof_financials(accounts,q)
        rows.append({'quarter':q.date().isoformat(),'verified_available_issuers':len(valid),
                     'status':'not_evaluated_missing_verified_historical_panel','recall_4q':None,'recall_8q':None})
    pd.DataFrame(rows).to_csv(out/'historical_replay_status.csv',index=False)
    leads=[]
    for r in events[events.event_type=='cirp_admission'].itertuples():
        for h in [12,24]:
            leads.append({'entity_id':r.entity_id,'event_type':r.event_type,'event_date':r.date_lower,
                'lead_months':h,'required_cutoff':lead_cutoff(r.date_lower,h).date().isoformat(),
                'status':'CIRP_reference_only_first_payment_default_must_be_resolved','recovered':None})
    pd.DataFrame(leads).to_csv(out/'required_lead_cutoffs.csv',index=False)
    coverage=[]
    for r in core.itertuples():
        local=docs[(docs.entity_id==r.entity_id)&(docs.document_type=='annual')]
        extracted=facts[facts.entity_id==r.entity_id]
        verified=versions[versions.entity_id==r.entity_id]
        coverage.append({'entity_id':r.entity_id,'name':r.historical_name,'role':r.role,
            'downloaded_annual_reports':int((local.status=='downloaded').sum()),
            'extraction_candidate_rows':len(extracted),'reviewed_source_versions':len(verified),
            'reviewed_distinct_periods':int(verified.period_end.nunique()),
            'strict_point_in_time_accounts':int(((verified.publication_status=='verified')&(verified.verification_status=='verified')).sum()),
            'missing_gate':'publication_dates; annual ratio coverage; control/default qualification; complete M/F inputs'})
    pd.DataFrame(coverage).to_csv(out/'coverage_review_queue.csv',index=False)
    result={'status':'research_build_incomplete_for_competition_submission',
        'benchmark_complete':True,'downloaded_documents':int((docs.status=='downloaded').sum()),
        'failed_document_routes':int((docs.status=='failed').sum()),
        'core_case_candidates':int((core.role=='case').sum()),'core_peer_candidates':int((core.role=='peer').sum()),
        'documented_cirp_dates':int((events.event_type=='cirp_admission').sum()),
        'documented_earlier_payment_default_cases':int((events.event_type=='documented_payment_default').sum()),
        'automatically_extracted_candidate_rows':len(facts),
        'source_reviewed_issuers_all_groups':int(versions.entity_id.nunique()),
        'source_reviewed_versions_all_groups':len(versions),
        'source_version_counts_by_group':versions.review_group.value_counts().to_dict(),
        'source_reviewed_pilot_issuers':int(accounts.entity_id.nunique()),
        'source_reviewed_pilot_records':len(accounts),
        'verified_historical_publication_records':int((versions.publication_status=='verified').sum()),
        'recall_at_5_percent_4q':None,'recall_at_5_percent_8q':None,'indian_expected_loss':None,
        'remaining_requirements':['Complete source-reviewed 3-year financial panel for at least 10 cases and 30 qualified distinct controls.',
            'Verify historical public availability before each scoring cutoff.',
            'Resolve earlier payment defaults and interval-dated events before claiming lead times.',
            'Complete and verify COGS, SG&A, actual issuance and prior beginning assets for M/F screens.',
            'Verify control listing, matching and non-default outcomes over observation horizons.',
            'Expand two signal-family coverage across the panel and obtain pre-cutoff evidence.',
            'Run and audit primary Indian recall/cost metrics only after these gates pass.']}
    (out/'readiness.json').write_text(json.dumps(result,indent=2))
    return result

def run(root):
    root=Path(root);a=pd.read_csv(root/'data/curated/pilot_reviewed_accounts.csv')
    result=readiness(root,a)
    pilot(root,a)
    print(json.dumps(result,indent=2),flush=True)
    return result

if __name__=='__main__':
    import sys
    run(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
