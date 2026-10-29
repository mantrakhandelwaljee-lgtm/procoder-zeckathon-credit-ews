"""Original FY2011 verification, version reconciliation and publication gates."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from .accounting import common_ratios

COMPARE={
 'gross_total_assets':'total_assets','gross_total_liabilities':'total_liabilities',
 'reported_parent_funds':'equity','net_income_parent':'net_income',
 'harmonized_operating_revenue':'sales','inventories':'inventory',
 'sundry_debtors':'receivables','profit_before_tax':'profit_before_tax',
 'core_earned_reserve_proxy':'retained_earnings','depreciation':'depreciation',
 'reported_current_assets_loans_advances':'current_assets',
}

def run(root):
    root=Path(root);d=root/'data/curated';out=root/'results/india/bhushan-reconciliation';out.mkdir(parents=True,exist_ok=True)
    a=json.loads((d/'fy2011_original_accounts.json').read_text());later=json.loads((d/'bhushan_case_accounts.json').read_text())
    docs=pd.read_csv(d/'bhushan_documents.csv',dtype=str).set_index('document_id')
    fields=[];checks=[];changes=[];ratios=[]
    for r in a:
        assert r['source_report_year']==2011 and r['source_column']=='current_original'
        src=docs.loc[r['source_document_id']];assert src['status']=='downloaded'
        residual=r['gross_total_assets']-r['reported_parent_funds']-r['reported_other_equity']-r['gross_total_liabilities']
        if abs(residual)>.011:raise ValueError(f"Original balance sheet failed: {r['entity_id']}, {residual}")
        checks.append(dict(entity_id=r['entity_id'],period_end=r['period_end'],source_document_id=r['source_document_id'],gross_assets=r['gross_total_assets'],liabilities=r['gross_total_liabilities'],parent_funds=r['reported_parent_funds'],other_equity=r['reported_other_equity'],residual_crore=residual,model_eligible=False,publication_verified=False))
        for field,value in r.items():
            if isinstance(value,bool) or not isinstance(value,(int,float)):continue
            if field in ['source_report_year','period_months']:continue
            kind='reserves' if field in ['general_reserve','debenture_redemption_reserve','profit_loss_surplus','core_earned_reserve_proxy'] else 'cash_flow' if field=='cfo' else 'finance' if 'finance' in field else 'profit_loss' if field in ['sales_net_excise','other_operating_income','harmonized_operating_revenue','net_income_parent','profit_before_tax','depreciation'] else 'balance'
            formula=''
            if field=='gross_total_assets':formula='printed_net_balance_total + reported_current_liabilities + reported_provisions'
            if field=='gross_total_liabilities':formula='reported_debt + deferred_tax_liability + other_noncurrent_liability + reported_current_liabilities + reported_provisions'
            if field=='core_earned_reserve_proxy':formula='general_reserve + debenture_redemption_reserve + P&L_surplus; mapping proxy, not certified full retained earnings'
            fields.append(dict(entity_id=r['entity_id'],period_end=r['period_end'],field=field,value=value,unit='INR crore',source_document_id=r['source_document_id'],source_url=src.source_url,source_sha256=src.sha256,pdf_page=r['source_pages'][kind],source_column='current_original',numeric_review='text_and_render_review_single_researcher',publication_status=r['publication_status'],formula=formula,mapping_note=r['mapping_notes']))
        old=next(x for x in later if x['entity_id']==r['entity_id'] and x['period_end']=='2011-03-31')
        for orig,comp in COMPARE.items():
            x=r.get(orig);y=old[comp]
            if x is None:continue
            note='Observed source-version/definition difference; cause not automatically inferred.'
            if orig=='reported_current_assets_loans_advances':note='Different presentation: old broad current-assets/loans bucket versus later current-only subtotal. NOT a like-for-like restatement amount.'
            changes.append(dict(entity_id=r['entity_id'],original_field=orig,later_field=comp,original_value=x,later_comparative_value=y,delta_later_minus_original=y-x,unit='INR crore',original_source=r['source_document_id'],later_source=old['source_document_id'],original_available_at=None,later_values_backdated=False,note=note))
        # Retain unknown current classifications as missing. Neither old broad
        # labels nor later comparative reclassifications manufacture exact inputs.
        model_view=dict(period_months=12,total_assets=r['gross_total_assets'],total_liabilities=r['gross_total_liabilities'],equity=r['reported_parent_funds'],retained_earnings=None,net_income=r['net_income_parent'],sales=r['harmonized_operating_revenue'],inventory=r['inventories'],receivables=None,current_assets=None,current_liabilities=None,ebit=None)
        rr=common_ratios(model_view);ratios.append(dict(entity_id=r['entity_id'],source_document_id=r['source_document_id'],**rr,model_score=None,strict_eligible=False,missing_inputs='current_assets;current_liabilities;retained_earnings_full_mapping;current_trade_receivables_mapping;EBIT_harmonisation'+(';operating_revenue_harmonisation' if r['harmonized_operating_revenue'] is None else '')))
    pd.DataFrame(fields).to_csv(out/'original_field_sources.csv',index=False)
    pd.DataFrame(checks).to_csv(out/'gross_balance_reconciliation.csv',index=False)
    pd.DataFrame(changes).to_csv(out/'original_vs_later_comparatives.csv',index=False)
    pd.DataFrame(a).drop(columns='source_pages').to_csv(out/'original_accounts.csv',index=False)
    pd.DataFrame(ratios).to_csv(out/'partial_common_ratios.csv',index=False)
    payment=pd.read_csv(d/'reconciled_payment_episodes.csv');availability=pd.read_csv(d/'fy2011_availability_review.csv')
    summary=dict(status='public_evidence_reconciled_with_explicit_remaining_gaps',original_issuers_reviewed=4,original_records=4,source_fields_reviewed=len(fields),gross_balance_checks_passed=len(checks),comparison_rows=len(changes),
        earliest_documented_payment_failure='2013-12-31',earliest_documented_programme_size_crore=500,
        actual_cure_date=None,cure_reporting_status='reported_paid_in_2014_02_26_status_notice_indexed_source',
        first_default_status='earliest_documented_not_exhaustively_established',
        regulator_filing_date_verified='2012-02-22',exact_historical_public_timestamps_verified=0,
        cutoff_4q_for_documented_event='2012-12-31',cutoff_8q_for_documented_event='2011-12-31',
        primary_scores_emitted=0,primary_recall_4q=None,primary_recall_8q=None,
        unresolved=['Original bank coupon/settlement receipts and ISIN-to-programme mapping are not publicly verified.',
                    'Earlier bank or debt-instrument failures have not been exhaustively excluded.',
                    'Jan/Feb2014noncompliancePDFs were reviewed through indexed primary excerpts; direct downloads were rejected.',
                    'Original FY2011current/noncurrent mappings, revenue/finance definitions and full earned reserves remain incomplete.',
                    'Exact publication of each original financial version before relevant cutoff remains unverified.'])
    (out/'status.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2),flush=True)
    return summary

if __name__=='__main__':run(Path(__file__).resolve().parents[1])
