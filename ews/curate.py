"""Explicit source review decisions, separate from automated extraction candidates."""
from pathlib import Path
import json
import pandas as pd

# FY2016 consolidated statements reviewed against rendered pages and note text.
# Both columns come from the FY2016 source, so their availability is FY2016-source
# availability. The comparative values are NEVER backdated to FY2015 publication.
PILOT={
'ITNL':{
 'pages':{'balance':179,'profit_loss':180,'cash_flow':181,'retained_earnings':197},
 'total_assets':[37844.29,31894.67],'current_assets':[5324.75,3986.80],
 'current_liabilities':[7243.28,6651.29],'equity':[6693.35,5719.17],
 'minority_interest':[473.61,291.14],'retained_earnings':[2260.18,2137.03],
 'net_income':[311.54,443.60],'sales':[8263.79,6500.97],
 'inventory':[86.95,14.08],'receivables':[1298.24,1045.62],
 'profit_before_tax':[429.14,480.54],'finance_costs':[2530.87,1833.12],
 'cfo':[2783.93,1068.34],'depreciation':[275.38,152.12],
 'long_term_debt':[22488.50,18591.71],'ppe':[320.70,174.45]},
'IRB':{
 'pages':{'balance':100,'profit_loss':101,'cash_flow':102,'retained_earnings':112},
 'total_assets':[42181.073253,39392.9738614],'current_assets':[2564.6183392,2374.3510475],
 'current_liabilities':[3243.1196198,2533.140208],'equity':[4827.2316851,4360.8641318],
 'minority_interest':[35.5007259,35.0514396],'retained_earnings':[2941.3425495,2474.9749962],
 'net_income':[635.8223022,542.9079011],'sales':[5130.2314022,3848.8757911],
 'inventory':[308.8407556,259.8496975],'receivables':[103.6626603,4.9135422],
 'profit_before_tax':[867.8667959,686.4363046],'finance_costs':[1063.3395414,931.2035386],
 'cfo':[2342.38029,1823.47937],'depreciation':[853.3434309,707.0623257],
 'long_term_debt':[12651.6228797,10804.4271119],'ppe':[269.8195362,283.4755734]},
'ASHOKA':{
 'pages':{'balance':119,'profit_loss':120,'cash_flow':121,'retained_earnings':125},
 'total_assets':[15390.4545,14666.6326],'current_assets':[1700.6399,1263.8536],
 'current_liabilities':[1415.2314,1338.2753],'equity':[1868.7508,1356.9178],
 'minority_interest':[499.539,504.7481],'retained_earnings':[699.368,694.5324],
 'net_income':[58.4544,81.4827],'sales':[2614.4948,2319.7149],
 'inventory':[1088.975,728.5609],'receivables':[366.0284,364.4438],
 'profit_before_tax':[56.3095,78.2048],'finance_costs':[447.7845,272.106],
 'cfo':[529.4915,389.8229],'depreciation':[249.1411,152.6799],
 'long_term_debt':[3838.505,3583.7367],'ppe':[172.7959,161.2229]},
'SADBHAV':{
 'pages':{'balance':91,'profit_loss':92,'cash_flow':93,'retained_earnings':105},
 'total_assets':[15809.0626,11932.991],'current_assets':[1850.9562,1935.2744],
 'current_liabilities':[1974.4064,1586.8355],'equity':[1797.8163,1537.2208],
 'minority_interest':[506.0339,189.4129],'retained_earnings':[185.0341,237.0265],
 'net_income':[-46.7541,-175.4865],'sales':[3877.515,3446.7812],
 'inventory':[141.0469,213.3717],'receivables':[821.7476,683.9632],
 'profit_before_tax':[-123.175,-198.2483],'finance_costs':[726.013,615.0125],
 'cfo':[787.1706,385.0128],'depreciation':[270.1443,219.2732],
 'long_term_debt':[8069.3985,6255.542],'ppe':[575.4321,556.1025]},
}

def run(root):
    root=Path(root);d=root/'data/curated'
    documents=pd.read_csv(d/'documents.csv')
    accounts=[];sources=[]
    bs_fields={'total_assets','current_assets','current_liabilities','equity','minority_interest',
               'inventory','receivables','long_term_debt','ppe'}
    for entity,values in PILOT.items():
        doc=documents[documents.document_id==f'{entity}_2016_annual'].iloc[0]
        for ix,year in enumerate([2016,2015]):
            row={'entity_id':entity,'period_end':f'{year}-03-31','period_months':12,
                 'basis':'consolidated','source_document_id':doc.document_id,
                 'source_report_year':2016,'normalized_unit':'INR crore',
                 'verification_status':'verified','review_scope':'financial_values_single_researcher_source_review',
                 'public_available_at':'','publication_status':'unverified',
                 'net_income_definition':'attributable to owners; accounting-domain mapping limitation disclosed',
                 'equity_definition':'parent shareholders funds; minority interest separately excluded from liabilities',
                 'source_url':doc.source_url}
            for field,vals in values.items():
                if field=='pages':continue
                row[field]=vals[ix]
                kind='balance' if field in bs_fields else ('cash_flow' if field=='cfo' else ('retained_earnings' if field=='retained_earnings' else 'profit_loss'))
                sources.append({'entity_id':entity,'period_end':row['period_end'],'field':field,
                    'value':vals[ix],'normalized_unit':'INR crore','source_document_id':doc.document_id,
                    'source_url':doc.source_url,'pdf_page':values['pages'][kind],
                    'verification_status':'reviewed_numeric_source','publication_status':'unverified',
                    'note':('Reconstructed accumulated earnings: P&L surplus + earned general reserve + earned debenture-redemption reserve, excluding share premium/capital reserves. ITNL components span PDF pages 196-197. ' if field=='retained_earnings' else '') + ('Comparative column of FY2016 source; never backdate availability.' if ix else '')})
            row['total_liabilities']=row['total_assets']-row['equity']-row['minority_interest']
            row['ebit']=row['profit_before_tax']+row['finance_costs']
            assert row['total_liabilities']>0
            for field,formula in [('total_liabilities','total_assets - parent_equity - minority_interest'),
                                  ('ebit','profit_before_tax_after_exceptional_items + finance_costs')]:
                sources.append({'entity_id':entity,'period_end':row['period_end'],'field':field,
                    'value':row[field],'normalized_unit':'INR crore','source_document_id':doc.document_id,
                    'source_url':doc.source_url,'pdf_page':values['pages']['balance' if field=='total_liabilities' else 'profit_loss'],
                    'verification_status':'derived_from_reviewed_values','publication_status':'unverified','note':formula})
            accounts.append(row)
    pd.DataFrame(accounts).to_csv(d/'pilot_reviewed_accounts.csv',index=False)
    pd.DataFrame(sources).to_csv(d/'pilot_field_sources.csv',index=False)
    # Verified CIRP dates are distinct from first-default claims.
    entities=pd.read_csv(d/'entities.csv').fillna({'cirp_date':'','documented_default_date':''})
    events=[]
    ibbi_id='REGISTRY_2017_event'
    for r in entities[entities.role=='case'].itertuples():
        doc_id=ibbi_id;page=11
        if r.entity_id=='ERA':doc_id='ERA_2018_event';page=2
        if r.entity_id=='FUTURE':doc_id='FUTURE_2022_event';page=1
        events.append({'entity_id':r.entity_id,'event_type':'cirp_admission','date_lower':r.cirp_date,
            'date_upper':r.cirp_date,'date_precision':'day','verification_status':'documented',
            'source_document_id':doc_id,'pdf_page':page,'source_url':r.event_source_url,
            'first_default_status':'not_established','usable_as_feature':False})
    # Trustee's public notice documents dates/intervals earlier than the CIRP dates.
    prior_defaults=[('ALOK','2015-06-29','2015-06-29','day'),
                    ('AMTEK','2015-09-20','2015-09-20','day'),
                    ('BHUSHAN','2015-07-01','2015-07-01','day'),
                    ('ERA','2015-05-01','2015-05-31','month'),
                    ('JAYPEE','2015-06-01','2015-06-30','month')]
    trustee_url='https://www.axistrustee.in/pdf/Press-Release-dated-20-October-2015.pdf'
    for e,lo,hi,precision in prior_defaults:
        events.append({'entity_id':e,'event_type':'documented_payment_default','date_lower':lo,'date_upper':hi,
            'date_precision':precision,'verification_status':'documented','source_document_id':'REGISTRY_2015_event',
            'pdf_page':1,'source_url':trustee_url,'first_default_status':'earlier_defaults_not_exhaustively_excluded',
            'usable_as_feature':False})
    events.append({'entity_id':'ITNL','event_type':'one_day_payment_delay','date_lower':'2018-06-21',
        'date_upper':'2018-06-21','date_precision':'day','verification_status':'documented',
        'source_document_id':'ITNL_2018_payment_event','pdf_page':1,
        'source_url':'https://www.icra.in/Rating/ShowRationalReportFilePdf/71209',
        'first_default_status':'technical_delay_exception_rating_unchanged_not_equated_to_bank_default',
        'usable_as_feature':False})
    # Case research retains contradictory date assertions without promoting any
    # one of them to a first-default label or a historical feature.
    case_events=d/'bhushan_case_events.csv'
    if case_events.exists():
        events.extend(pd.read_csv(case_events).to_dict('records'))
    pd.DataFrame(events).to_csv(d/'events.csv',index=False)
    # Actual evidence from two distinct families; unknown availability is not silently filled.
    soft=[{
        'entity_id':'ITNL','signal_family':'related_party_exposure','period_end':'2016-03-31',
        'occurred_at':'2016-03-31','public_available_at':'','publication_status':'unverified',
        'value':3406.39,'unit':'INR crore','prior_value':2916.50,
        'description':'Standalone related-party loans and advances, net disclosed subtotal: long-term 1939.29 + short-term 1467.10. Prior 1268.05 + 1648.45. Not mixed into consolidated ratios.',
        'source_document_id':'ITNL_2016_annual','source_url':documents[documents.document_id=='ITNL_2016_annual'].iloc[0].source_url,
        'pdf_page':137,'verification_status':'reviewed_source','severity':'review_context_not_automatically_fraud',
    },{
        'entity_id':'ITNL','signal_family':'related_party_transaction','period_end':'2016-03-31',
        'occurred_at':'2016-03-31','public_available_at':'','publication_status':'unverified',
        'value':141.82,'unit':'INR crore','prior_value':None,
        'description':'Standalone profit on sale of Rapid MetroRail Gurgaon stake to parent; assess recurring earnings and group funding dependence.',
        'source_document_id':'ITNL_2016_annual','source_url':documents[documents.document_id=='ITNL_2016_annual'].iloc[0].source_url,
        'pdf_page':137,'verification_status':'reviewed_source','severity':'review_context_not_automatically_fraud',
    },{
        'entity_id':'ITNL','signal_family':'rating_action','period_end':'',
        'occurred_at':'2018-02-01','public_available_at':'2018-02-01','publication_status':'dated_rating_release',
        'value':None,'unit':'','prior_value':None,
        'description':'ICRA confirms structured-obligation AA+(SO) rating; underlying A(Negative) outstanding. Instrument-specific; not a blanket issuer AAA or an adverse downgrade. Too late for a 2017 warning.',
        'source_document_id':'ITNL_2018_rating','source_url':'https://www.icra.in/Rating/ShowRationalReportFilePdf/67019',
        'pdf_page':1,'verification_status':'reviewed_source','severity':'context_only_no_adverse_action',
    }]
    pd.DataFrame(soft).to_csv(d/'soft_signals.csv',index=False)
    # Corrections captured explicitly rather than silently changing extracted figures.
    corrections=[
        {'entity_id':'IRB','field':'current_liabilities','reason':'A wrapped trade-payables label interrupted the generic subtotal parser; manually read balance-sheet subtotal.'},
        {'entity_id':'SADBHAV','field':'receivables','reason':'Generic extraction matched long-term trade receivables first. Use the current trade receivables line for the deployed ratio.'},
        {'entity_id':'ASHOKA','field':'profit_before_tax','reason':'Use PBT after exceptional items, not the earlier subtotal.'},
        {'entity_id':'IRB','field':'net_income','reason':'Pilot consistently uses profit attributable to parent owners, not total group profit including minority.'},
        {'entity_id':'JINDALSTEL','field':'control_eligibility','reason':'Removed from proposed control pool after finding default evidence; replaced by a provisional Kalyani Steels match.'},
        {'entity_id':'HCC','field':'control_eligibility','reason':'SEBI order confirms a continuing default rating from February 2012; removed from controls. Source: https://nsearchives.nseindia.com/corporate/RPOWER_20062024203635_RPower_DisclosureReg30_SEBIOrdersigned.pdf'},
        {'entity_id':'PNC','field':'control_eligibility','reason':'2015 IPO does not cover earlier required cutoffs; replaced provisionally by an issuer listed before those cutoffs.'},
        {'entity_id':'ALOK','field':'period_months','reason':'FY2012-13 and FY2013-15 are 18-month periods. Never treat their flow ratios as ordinary 12-month observations.'},
    ]
    (d/'review_decisions.json').write_text(json.dumps(corrections,indent=2))
    return pd.DataFrame(accounts)

if __name__=='__main__':
    import sys
    run(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
