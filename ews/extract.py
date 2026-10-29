"""Conservative candidate extraction, preserving complete source lines and page numbers.

These are review candidates. This module never marks a financial value or a historical
publication date verified merely because a regular expression matched it.
"""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd

NUM=r'\(?-?\d[\d,]*(?:\.\d+)?\)?|[-–—]'

def numbers(line):
    # Prefer table cells separated from their textual label.
    chunks=re.split(r'\s{2,}|\t+',line.strip())
    vals=[]
    cells=chunks if re.fullmatch(NUM,chunks[0].strip()) else chunks[1:]
    for chunk in cells:
        if re.fullmatch(NUM,chunk.strip()):
            x=chunk.strip()
            if x in ['-','–','—']: vals.append(None)
            else:vals.append(float(x.replace(',','').replace('(','-').replace(')','')))
    if len(vals) in [3,5]:vals=vals[1:] # leading note-reference column
    if len(vals)==2:return vals
    if len(vals)==4:return [vals[0],vals[2]]
    return None

def unit_factor(page):
    top=' '.join(page.splitlines()[:30]).lower()
    if re.search(r'\b(crore|crores)\b',top):return 1.,'INR crore'
    if re.search(r'\b(lakh|lakhs|lac|lacs)\b',top):return .01,'INR lakh'
    if re.search(r'\b(million|millions)\b',top):return .1,'INR million'
    if re.search(r'amount\s+in\s+(?:`|rs|₹)|\bin\s+rupees\b',top):return 1e-7,'INR'
    return None,'unresolved'

def statement_pages(pages,basis):
    found={}
    for i,page in enumerate(pages):
        lo=page.lower();top=' '.join(page.splitlines()[:20]).lower()
        is_consolidated='consolidated' in top
        if basis=='consolidated' and not is_consolidated:continue
        if basis=='standalone' and is_consolidated:continue
        if 'balance sheet' in top and 'current assets' in lo and 'current liabilities' in lo:
            found.setdefault('balance',i)
        if ('profit and loss' in top or 'profit & loss' in top or 'statement of income' in top) and ('finance cost' in lo or 'interest' in lo) and ('revenue' in lo or 'sales' in lo):
            found.setdefault('profit_loss',i)
        if ('cash flow' in top or 'cashflow' in top or 'cash flows' in top) and 'operating activit' in lo:
            found.setdefault('cash_flow',i)
    return found

def extract_doc(row,root):
    text=(root/row.text_relative_path).read_text(errors='replace');pages=text.split('\f')
    records=[];index=[]
    for basis in ['standalone','consolidated']:
        positions=statement_pages(pages,basis)
        for typ,i in positions.items():
            factor,unit=unit_factor(pages[i]);index.append({'document_id':row.document_id,'basis':basis,
                'statement':typ,'pdf_page':i+1,'unit':unit})
        found={}
        def add(key,pageno,line,values=None,derived=False):
            if key in found:return
            nums=numbers(line) if values is None else values
            factor,unit=unit_factor(pages[pageno])
            if nums is None:return
            found[key]=True
            records.append({'entity_id':row.entity_id,'report_year':row.report_year,
                'basis':basis,'field':key,'current_value':None if factor is None or nums[0] is None else nums[0]*factor,
                'comparative_value':None if factor is None or nums[1] is None else nums[1]*factor,
                'original_current_value':nums[0],'original_comparative_value':nums[1],
                'original_unit':unit,'normalized_unit':'INR crore' if factor else '',
                'document_id':row.document_id,'source_url':row.source_url,'pdf_page':pageno+1,
                'source_line':line.strip(),'verification_status':'requires_review',
                'public_available_at':'','publication_status':'unverified',
                'method':'derived_candidate' if derived else 'table_row_candidate'})
        if 'balance' in positions:
            i=positions['balance'];lines=pages[i].splitlines()
            for line in lines:
                lo=line.lower()
                for key,pat in [
                    ('inventory',r'\binventor(?:y|ies)\b'),
                    ('receivables',r'\btrade receivables?\b'),
                    ('cash_and_bank_reported',r'cash (?:and|&) (?:cash equivalents|bank balances)'),
                    ('long_term_debt',r'long[ -]term borrowings'),
                    ('short_term_debt',r'short[ -]term borrowings'),
                    ('current_debt_maturities',r'current maturities'),
                    ('retained_earnings',r'retained earnings'),
                    ('share_capital',r'\bshare capital\b'),
                    ('reserves_surplus',r'reserves? (?:and|&) surplus'),
                    ('minority_interest',r'minority interest'),
                    ('ppe',r'tangible assets|properties,? plants? (?:&|and) equipments?'),
                ]:
                    if re.search(pat,lo) and not ('intangible' in lo and key=='ppe'):add(key,i,line)
            totals=[]
            for line in lines:
                if re.match(r'^\s*(?:total(?: assets| equity.*liabilities)?)\s{2,}',line,re.I):
                    n=numbers(line)
                    if n:totals.append((line,n))
            if totals:add('total_assets',i,totals[-1][0])
            # Preserve subtotals from within sections; never call an arbitrary component the total.
            for field,start_pat,end_pat in [
                ('current_assets',r'^\s*(?:\(?[0-9]+\)?\s*)?current assets\s*$',r'^\s*total\b'),
                ('current_liabilities',r'^\s*(?:\(?[0-9]+\)?\s*)?current liabilities\s*$',r'^\s*total\b|^\s*(?:II\s+)?assets\b')]:
                active=False;last=None
                for line in lines:
                    if re.search(start_pat,line,re.I):active=True;continue
                    if active and re.search(end_pat,line,re.I):break
                    if active:
                        n=numbers(line)
                        chunks=re.split(r'\s{2,}|\t+',line.strip())
                        if n and (not re.search('[A-Za-z]',line) or len(chunks)>=6):last=(line,n)
                if last:
                    line,n=last
                    raw=[c for c in re.split(r'\s{2,}|\t+',line.strip())[1:] if re.fullmatch(NUM,c.strip())]
                    if len(raw) in [4,5]:
                        raw=raw[-4:]
                        def parse(x):return None if x.strip() in ['-','–','—'] else float(x.replace(',','').replace('(','-').replace(')',''))
                        n=[parse(raw[1]),parse(raw[3])]
                    add(field,i,line,n)
        if 'profit_loss' in positions:
            i=positions['profit_loss']
            for line in pages[i].splitlines():
                lo=line.lower()
                for key,pat in [
                    ('sales',r'revenue from operations|\bnet sales\b'),
                    ('finance_costs',r'finance costs?\b'),
                    ('depreciation',r'depreciation.*amorti[sz]ation|^\s*depreciation\s'),
                    ('other_income',r'\bother income\b'),
                    ('profit_before_tax',r'profit (?:/\s*\(loss\) )?before tax|profit before taxation'),
                    ('net_income',r'profit (?:for the year|after tax)|profit / \(loss\) for the year'),
                    ('sga_reported_candidate',r'administrative and general expenses')]:
                    if re.search(pat,lo):add(key,i,line)
        if 'cash_flow' in positions:
            i=positions['cash_flow']
            for j in range(i,min(len(pages),i+2)):
                for line in pages[j].splitlines():
                    if re.search(r'net cash.*(?:from|in|by).*operating activit',line,re.I):add('cfo',j,line)
    return records,index

def run(root):
    root=Path(root);docs=pd.read_csv(root/'data/curated/documents.csv').fillna({'text_relative_path':''})
    docs=docs[docs.status=='downloaded']
    required=docs[(docs.document_type=='annual')&(docs.text_relative_path!='')]
    absent=[r.document_id for r in required.itertuples() if not (root/r.text_relative_path).exists()]
    if absent:
        if (root/'data/curated/financial_candidates.csv').exists():
            print(f'Using saved extraction candidates; {len(absent)} original text files are not cached. Run --fetch to restore originals.',flush=True)
            return
        raise FileNotFoundError('Original report text missing; run python run.py --fetch')
    facts=[];idx=[]
    for row in docs.itertuples():
        if row.document_type!='annual' or not row.text_relative_path:continue
        f,i=extract_doc(row,root);facts+=f;idx+=i
    out=root/'data/curated'
    pd.DataFrame(facts).to_csv(out/'financial_candidates.csv',index=False)
    pd.DataFrame(idx).to_csv(out/'statement_page_index.csv',index=False)
    print(f'Extracted {len(facts)} source-linked candidate rows; none automatically verified.')

if __name__=='__main__':
    import sys
    run(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
