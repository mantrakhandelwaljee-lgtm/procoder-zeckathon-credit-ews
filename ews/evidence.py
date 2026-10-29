"""A single inventory of downloaded evidence and reviewed source versions."""
from pathlib import Path
import hashlib,json
import pandas as pd

MANIFESTS=['documents.csv','bhushan_documents.csv']

def load_documents(root):
    root=Path(root);frames=[]
    for name in MANIFESTS:
        p=root/'data/curated'/name
        if p.exists():
            frame=pd.read_csv(p,dtype=str).fillna('');frame['manifest']=name;frames.append(frame)
    if not frames:raise ValueError('No evidence manifests found')
    docs=pd.concat(frames,ignore_index=True)
    if docs.document_id.eq('').any():raise ValueError('Missing document ID')
    for doc_id,group in docs.groupby('document_id'):
        if any(group[c].nunique()>1 for c in ['source_url','sha256','status','relative_path']):
            raise ValueError(f'Conflicting manifest records for {doc_id}')
    return docs.drop_duplicates('document_id').reset_index(drop=True)

def audit_sources(root):
    root=Path(root);docs=load_documents(root);rows=[]
    for r in docs[docs.status.eq('downloaded')].itertuples():
        path=(root/r.relative_path).resolve()
        if not path.is_relative_to(root.resolve()):raise ValueError('Evidence path escapes project directory')
        if not path.exists():status='not_cached';actual=None
        else:
            actual=hashlib.sha256(path.read_bytes()).hexdigest()
            status='match' if actual==r.sha256 else 'mismatch'
        rows.append({'document_id':r.document_id,'expected_sha256':r.sha256,'actual_sha256':actual,'status':status})
    result={'downloaded_documents':len(rows),'cached_documents_checked':sum(r['status']!='not_cached' for r in rows),
        'hash_matches':sum(r['status']=='match' for r in rows),'not_cached':sum(r['status']=='not_cached' for r in rows),
        'hash_mismatches':[r['document_id'] for r in rows if r['status']=='mismatch'],
        'failed_document_routes':int(docs.status.eq('failed').sum()),'documents':rows}
    result['status']='fail' if result['hash_mismatches'] else ('pass_cached_subset' if result['not_cached'] else 'pass')
    out=root/'results/source-integrity.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2))
    if result['hash_mismatches']:raise ValueError(f"Source hash mismatch: {result['hash_mismatches']}")
    return result

def reviewed_versions(root,accounts):
    root=Path(root);frames=[accounts.assign(review_group='tollroad_pilot')]
    for name,label in [('bhushan_case_accounts.json','steel_case'),('fy2011_original_accounts.json','fy2011_original')]:
        p=root/'data/curated'/name
        if p.exists():frames.append(pd.DataFrame(json.loads(p.read_text())).assign(review_group=label))
    versions=pd.concat(frames,ignore_index=True)
    keys=['entity_id','period_end','source_document_id']
    if versions.duplicated(keys).any():raise ValueError('Duplicate reviewed source versions')
    return versions
