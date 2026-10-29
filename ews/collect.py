"""Public source collection. Retrieval never implies historical-date verification."""
from __future__ import annotations
import concurrent.futures, hashlib, json, re, subprocess, time
from pathlib import Path
from urllib.request import Request, urlopen
import pandas as pd

CASE_SOURCE='https://ibbi.gov.in/uploads/meetings/Agenda_7%28a%29_210917.pdf'
ROWS=[
('BHUSHAN','Bhushan Steel',500055,'steel','case','2017-07-26',''),
('MONNET','Monnet Ispat & Energy',513446,'steel','case','2017-07-18',''),
('ALOK','Alok Industries',521070,'textiles','case','2017-07-18','2015-06-29'),
('AMTEK','Amtek Auto',520077,'auto_components','case','2017-07-24','2015-09-20'),
('LANCO','Lanco Infratech',532778,'power','case','2017-08-07',''),
('JAYPEE','Jaypee Infratech',533207,'real_estate','case','2017-08-09',''),
('JYOTI','Jyoti Structures',513250,'power_epc','case','2017-07-04',''),
('ELECTROSTEEL','Electrosteel Steels',533264,'steel','case','2017-07-21',''),
('ERA','Era Infra Engineering',530323,'construction_epc','case','2018-05-08',''),
('FUTURE','Future Retail',540064,'retail','case','2022-07-20',''),
('JSW','JSW Steel',500228,'steel','peer','',''),
('TATASTEEL','Tata Steel',500470,'steel','peer','',''),
('SAIL','Steel Authority of India',500113,'steel','peer','',''),
('JINDALSTEL','Jindal Steel & Power',532286,'steel','excluded_control','',''),
('KALYANI','Kalyani Steels',500235,'steel','peer','',''),
('JINDALSAW','Jindal Saw',500378,'steel','peer','',''),
('GODAWARI','Godawari Power & Ispat',532734,'steel','peer','',''),
('VARDHMAN','Vardhman Textiles',502986,'textiles','peer','',''),
('WELSPUN','Welspun India',514162,'textiles','peer','',''),
('ARVIND','Arvind',500101,'textiles','peer','',''),
('BHARATFORGE','Bharat Forge',500493,'auto_components','peer','',''),
('MOTHERSON','Motherson Sumi Systems',517334,'auto_components','peer','',''),
('SUNDRAM','Sundram Fasteners',500403,'auto_components','peer','',''),
('NTPC','NTPC',532555,'power','peer','',''),
('TATAPOWER','Tata Power',500400,'power','peer','',''),
('JSWENERGY','JSW Energy',533148,'power','peer','',''),
('DLF','DLF',532868,'real_estate','peer','',''),
('OBEROI','Oberoi Realty',533273,'real_estate','peer','',''),
('SOBHA','Sobha',532784,'real_estate','peer','',''),
('KEC','KEC International',532714,'power_epc','peer','',''),
('KALPATARU','Kalpataru Power Transmission',522287,'power_epc','peer','',''),
('TECHNO','Techno Electric & Engineering (historical entity)',533281,'power_epc','peer','',''),
('SSWL','Steel Strips Wheels',513262,'steel_products','peer','',''),
('APL','APL Apollo Tubes',533758,'steel_products','peer','',''),
('RATNAMANI','Ratnamani Metals & Tubes',520111,'steel_products','peer','',''),
('HCC','Hindustan Construction',500185,'construction_epc','excluded_control','',''),
('NCC','NCC',500294,'construction_epc','peer','',''),
('PNC','PNC Infratech',539150,'construction_epc','excluded_control','',''),
('ITDCEM','ITD Cementation India',509496,'construction_epc','peer','',''),
('KNR','KNR Constructions',532942,'construction_epc','peer','',''),
('TRENT','Trent',500251,'retail','peer','',''),
('SHOPPERS','Shoppers Stop',532638,'retail','peer','',''),
('VMART','V-Mart Retail',534976,'retail','peer','',''),
('ITNL','IL&FS Transportation Networks',533177,'roads','supplementary_case','',''),
('IRB','IRB Infrastructure Developers',532947,'roads','supplementary_peer','',''),
('ASHOKA','Ashoka Buildcon',533271,'roads','supplementary_peer','',''),
('SADBHAV','Sadbhav Engineering',532710,'roads','supplementary_peer','',''),
]
MATCHES={
'BHUSHAN':['JSW','TATASTEEL','SAIL'],'MONNET':['KALYANI','JINDALSAW','GODAWARI'],
'ALOK':['VARDHMAN','WELSPUN','ARVIND'],'AMTEK':['BHARATFORGE','MOTHERSON','SUNDRAM'],
'LANCO':['NTPC','TATAPOWER','JSWENERGY'],'JAYPEE':['DLF','OBEROI','SOBHA'],
'JYOTI':['KEC','KALPATARU','TECHNO'],'ELECTROSTEEL':['SSWL','APL','RATNAMANI'],
'ERA':['ITDCEM','NCC','KNR'],'FUTURE':['TRENT','SHOPPERS','VMART'],
'ITNL':['IRB','ASHOKA','SADBHAV']}

def seed(root):
    root=Path(root);d=root/'data/curated';d.mkdir(parents=True,exist_ok=True)
    df=pd.DataFrame(ROWS,columns=['entity_id','historical_name','bse_code','sector','role','cirp_date','documented_default_date'])
    df['matching_status']='candidate_requires_historical_size_business_and_outcome_checks'
    df['listing_status']='requires_cutoff_specific_verification'
    df['default_date_status']='unresolved'
    df.loc[df.entity_id.isin(['ALOK','AMTEK']),'default_date_status']='documented_payment_date_first_default_not_exhaustively_established'
    df['event_source_url']=''
    df.loc[df.role=='case','event_source_url']=CASE_SOURCE
    df.loc[df.entity_id=='ERA','event_source_url']='https://ibbi.gov.in/uploads/order/eba413347ca84dbefc1c2764e1ac55d5.pdf'
    df.loc[df.entity_id=='FUTURE','event_source_url']='https://www.bseindia.com/xml-data/corpfiling/AttachHis/b4658618-2d0e-4b2d-a215-f17b2aaee755.pdf'
    df['default_source_url']=''
    df.loc[df.entity_id.isin(['ALOK','AMTEK']),'default_source_url']='https://www.axistrustee.in/pdf/Press-Release-dated-20-October-2015.pdf'
    df.to_csv(d/'entities.csv',index=False)
    matches=[]
    for case,peers in MATCHES.items():
        for peer in peers:
            caveat='Provisional sector match; verify historical size, leverage, business mix, listing and non-default outcome.'
            if case=='ELECTROSTEEL':caveat+=' Steel-products businesses are imperfect integrated-steel comparators.'
            if peer=='PNC':caveat+=' IPO in 2015: exclude before listing; verify cutoff.'
            if peer=='TECHNO':caveat+=' Historical entity later reorganized: do not join to current issuer blindly.'
            if peer=='SADBHAV':caveat+=' Later distress must be checked against the exact control observation horizon.'
            matches.append({'case_id':case,'peer_id':peer,'status':'candidate','caveat':caveat})
    pd.DataFrame(matches).to_csv(d/'peer_matches.csv',index=False)
    return df

def fetch_one(job,root):
    entity,year,url,doc_type=job
    raw=root/'data/raw/reports';raw.mkdir(parents=True,exist_ok=True)
    doc_id=f'{entity}_{year}_{doc_type}'
    path=raw/f'{doc_id}.pdf'
    result={'document_id':doc_id,'entity_id':entity,'report_year':year,'document_type':doc_type,
            'source_url':url,'relative_path':str(path.relative_to(root)),
            'public_available_at':'','publication_status':'unverified','retrieved_at':'2026-10-28',
            'status':'failed','error':'','sha256':'','bytes':0}
    try:
        if path.exists():b=path.read_bytes()
        else:
            req=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; academic credit risk research)'})
            with urlopen(req,timeout=30) as res:b=res.read(60_000_001)
        if len(b)>60_000_000:raise ValueError('PDF exceeds download limit; refusing a truncated source')
        if not b.startswith(b'%PDF'):raise ValueError('Response is not a PDF')
        path.write_bytes(b)
        result.update(status='downloaded',sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
        text_dir=root/'data/raw/text';text_dir.mkdir(exist_ok=True)
        txt=text_dir/f'{doc_id}.txt'
        if not txt.exists():
            proc=subprocess.run(['pdftotext','-layout',str(path),str(txt)],capture_output=True,timeout=45)
            if proc.returncode:result['error']='PDF downloaded; text extraction failed'
        if txt.exists():
            text=txt.read_text(errors='replace')
            result['text_characters']=len(text)
            result['text_relative_path']=str(txt.relative_to(root))
            # Candidates only: a printed date/signature does not prove exchange availability.
            first='\n'.join(text.split('\f')[:3])
            result['cover_date_candidates']=' | '.join(re.findall(r'\b\d{1,2}(?:st|nd|rd|th)?[ ,\-/]+(?:January|February|March|April|May|June|July|August|September|October|November|December)[ ,\-/]+20\d{2}\b',first,flags=re.I)[:5])
    except Exception as exc:result['error']=f'{type(exc).__name__}: {exc}'[:300]
    return result

def run(root):
    root=Path(root);df=seed(root)
    jobs=[]
    for row in df.itertuples():
        years=[2014,2015,2016]
        if row.entity_id in ['FUTURE','TRENT','SHOPPERS','VMART']:years=[2017,2018,2019,2020]
        if row.entity_id=='ERA':years=[2015,2016,2017]
        if row.entity_id in ['ALOK','AMTEK','BHARATFORGE','MOTHERSON','SUNDRAM','VARDHMAN','WELSPUN','ARVIND']:years=[2012,2013,2014,2015,2016]
        if row.entity_id in ['ITNL','IRB','ASHOKA','SADBHAV']:years=[2014,2015,2016,2017]
        for year in years:
            code=str(row.bse_code);url=f'https://www.bseindia.com/bseplus/AnnualReport/{code}/{code}03{str(year)[-2:]}.pdf'
            jobs.append((row.entity_id,year,url,'annual'))
    jobs += [('REGISTRY',2017,CASE_SOURCE,'event'),
        ('REGISTRY',2015,'https://www.axistrustee.in/pdf/Press-Release-dated-20-October-2015.pdf','event'),
        ('ERA',2018,'https://ibbi.gov.in/uploads/order/eba413347ca84dbefc1c2764e1ac55d5.pdf','event'),
        ('FUTURE',2022,'https://www.bseindia.com/xml-data/corpfiling/AttachHis/b4658618-2d0e-4b2d-a215-f17b2aaee755.pdf','event'),
        ('ILFS_PARENT',2017,'https://www.ilfsindia.com/media/1872/ilfs-ar-2016-17.pdf','annual'),
        ('ITNL',2018,'https://www.icra.in/Rating/ShowRationalReportFilePdf/67019','rating'),
        ('ITNL',2016,'https://stockdiscovery.s3.amazonaws.com/insight/india/5761/Annual%20Report/AR-16.pdf','filing_copy')]
    results=[];manifest=root/'data/curated/documents.csv'
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futures=[ex.submit(fetch_one,job,root) for job in jobs]
        for f in concurrent.futures.as_completed(futures):
            r=f.result();results.append(r)
            if len(results)%10==0 or r['status']=='failed':print(f"Sources {len(results)}/{len(jobs)} {r['document_id']} {r['status']}",flush=True)
            pd.DataFrame(results).sort_values('document_id').to_csv(manifest,index=False)
    print('Collection complete',pd.Series([r['status'] for r in results]).value_counts().to_dict(),flush=True)

def rehydrate_manifest(root,retry_failed=False):
    """Restore the exact curated URLs (including non-March report filenames)."""
    root=Path(root);manifest=root/'data/curated/documents.csv'
    if not manifest.exists():return run(root)
    original=pd.read_csv(manifest).fillna('')
    jobs=[r for r in original.to_dict('records') if r['status']=='downloaded' or retry_failed]
    updated={}
    def restore(row):
        result=fetch_one((row['entity_id'],int(row['report_year']),row['source_url'],row['document_type']),root)
        if row.get('sha256') and result['status']=='downloaded' and result['sha256']!=row['sha256']:
            p=root/result['relative_path'];p.rename(p.with_suffix('.changed.pdf'))
            result.update(status='quarantined_hash_mismatch',error='Source content changed; manual version review required',sha256=row['sha256'])
        # Keep any separately verified historical-publication decisions.
        for k in ['public_available_at','publication_status']:
            if row.get(k):result[k]=row[k]
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for result in ex.map(restore,jobs):updated[result['document_id']]=result
    rows=[updated.get(row['document_id'],row) for row in original.to_dict('records')]
    pd.DataFrame(rows).sort_values('document_id').to_csv(manifest,index=False)
    print('Manifest source restore complete',flush=True)

if __name__=='__main__':
    import sys
    run(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
