import hashlib,json
import pandas as pd
import pytest
from ews.evidence import load_documents,audit_sources,reviewed_versions


def manifest(tmp_path):
    d=tmp_path/'data/curated';d.mkdir(parents=True)
    raw=tmp_path/'data/raw/reports';raw.mkdir(parents=True)
    source=raw/'A.pdf';source.write_bytes(b'%PDF fixture')
    row=dict(document_id='A',entity_id='A',status='downloaded',source_url='https://example.org/a.pdf',
             sha256=hashlib.sha256(source.read_bytes()).hexdigest(),relative_path='data/raw/reports/A.pdf')
    pd.DataFrame([row]).to_csv(d/'documents.csv',index=False)
    return row,source


def test_integrity_distinguishes_missing_cache_from_verified_source(tmp_path):
    row,source=manifest(tmp_path)
    assert audit_sources(tmp_path)['hash_matches']==1
    source.unlink()
    result=audit_sources(tmp_path)
    assert result['hash_matches']==0 and result['not_cached']==1
    assert result['status']=='pass_cached_subset'


def test_tampered_source_fails_before_reuse(tmp_path):
    row,source=manifest(tmp_path);source.write_bytes(b'%PDF changed')
    with pytest.raises(ValueError):audit_sources(tmp_path)
    assert json.loads((tmp_path/'results/source-integrity.json').read_text())['status']=='fail'


def test_conflicting_case_manifest_cannot_replace_original_silently(tmp_path):
    row,source=manifest(tmp_path)
    row['sha256']='b'*64
    pd.DataFrame([row]).to_csv(tmp_path/'data/curated/bhushan_documents.csv',index=False)
    with pytest.raises(ValueError):load_documents(tmp_path)
