#!/usr/bin/env python3
"""Test, execute the review notebook, prove benchmark preservation, and package a portable release."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys,tempfile,zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def benchmark_hashes():
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'results/benchmark').rglob('*')) if p.is_file()}

def main():
    before=benchmark_hashes()
    subprocess.run([sys.executable,str(ROOT/'run.py'),'--test'],cwd=ROOT,check=True)
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpecManager
    path=ROOT/'research-review.ipynb';nb=nbformat.read(path,as_version=4)
    with tempfile.TemporaryDirectory(prefix='credit-ews-kernel-') as td:
        spec=Path(td)/'ews-release';spec.mkdir()
        (spec/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
            'display_name':'Credit EWS release validation','language':'python'}))
        km=KernelManager(kernel_name='ews-release',kernel_spec_manager=KernelSpecManager(kernel_dirs=[td]))
        NotebookClient(nb,km=km,timeout=180,resources={'metadata':{'path':str(ROOT)}}).execute()
    nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
    nbformat.write(nb,path)
    after=benchmark_hashes()
    if before!=after:raise RuntimeError('Benchmark artifacts changed during release; refusing to package')
    suites=list(ET.parse(ROOT/'results/test-results.xml').getroot().iter('testsuite'))
    errors=sum(int(s.get('errors',0))+int(s.get('failures',0)) for s in suites)
    cells=[c for c in nb.cells if c.cell_type=='code']
    nberrors=sum(o.output_type=='error' for c in cells for o in c.outputs)
    if errors or nberrors or any(c.execution_count is None for c in cells):raise RuntimeError('Incomplete release validation')
    integrity=json.loads((ROOT/'results/source-integrity.json').read_text())
    validation={'validated_at_utc':datetime.now(timezone.utc).isoformat(),
        'tests':sum(int(s.get('tests',0)) for s in suites),'failures_or_errors':errors,
        'executed_notebook_code_cells':len(cells),'notebook_errors':nberrors,
        'benchmark_artifacts_unchanged':True,'benchmark_sha256':after,
        'source_hash_matches_at_release':integrity['hash_matches'],'uncached_sources_at_release':integrity['not_cached'],
        'note':'Release-time evidence. Each normal run refreshes results/source-integrity.json for its own cache.'}
    (ROOT/'results/release-validation.json').write_text(json.dumps(validation,indent=2))
    for name in ['bhushan-case','bhushan-reconciliation']:
        p=ROOT/'results/india'/name/'validation.json'
        p.write_text(json.dumps({'current_validation':'results/release-validation.json',
            'scope':'Shared pipeline tests and notebook execution; historical evidence limitations remain in status.json.'},indent=2))
    def include(p):
        rel=p.relative_to(ROOT)
        return p.is_file() and not any(x in rel.parts for x in ['__pycache__','.pytest_cache','.DS_Store','superseded']) and not str(rel).startswith(('data/raw/reports/','data/raw/text/')) and p.name!='MANIFEST.sha256'
    paths=sorted(p for p in ROOT.rglob('*') if include(p))
    (ROOT/'MANIFEST.sha256').write_text(''.join(digest(p)+'  '+str(p.relative_to(ROOT))+'\n' for p in paths))
    paths.append(ROOT/'MANIFEST.sha256');target=ROOT.parent/'credit-ews-code-and-results.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths:z.write(p,'credit-ews/'+str(p.relative_to(ROOT)))
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None:raise RuntimeError('Archive CRC failure')
    print(json.dumps({k:v for k,v in validation.items() if k!='benchmark_sha256'},indent=2))
    print(f'Portable release: {target}; {len(paths)} files; {target.stat().st_size:,} bytes')

if __name__=='__main__':main()
