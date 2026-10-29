#!/usr/bin/env python3
"""Rebuild the research outputs from cached evidence without publishing anything."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,tempfile

ROOT=Path(__file__).resolve().parent
os.environ.setdefault('OMP_NUM_THREADS','2')
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'credit-ews-matplotlib'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch',action='store_true',help='Download/restore exact report URLs in the evidence manifest')
    parser.add_argument('--retry-failed',action='store_true',help='Retry failed routes when fetching')
    parser.add_argument('--train',action='store_true',help='Reproduce the fixed benchmark protocol and frozen hold-out')
    parser.add_argument('--test',action='store_true',help='Run meaningful numerical and leakage tests')
    args=parser.parse_args()
    from ews.collect import rehydrate_manifest
    if args.fetch:rehydrate_manifest(ROOT,args.retry_failed)
    raw=ROOT/'data/raw/polish-bankruptcy.zip'
    expected='17377929aa0b204bbf957e56462cf827c19fe4e2ce89f27dfbc77f9ea2bb16c9'
    if not raw.exists():
        from urllib.request import urlopen
        raw.parent.mkdir(parents=True,exist_ok=True)
        b=urlopen('https://archive.ics.uci.edu/static/public/365/polish%2Bcompanies%2Bbankruptcy%2Bdata.zip',timeout=60).read()
        if hashlib.sha256(b).hexdigest()!=expected:raise RuntimeError('Benchmark archive changed; investigate version before proceeding')
        raw.write_bytes(b)
    if hashlib.sha256(raw.read_bytes()).hexdigest()!=expected:raise RuntimeError('Benchmark archive hash mismatch')
    if args.train:
        from ews.benchmark import run
        run(ROOT)
    if not (ROOT/'results/benchmark/model.joblib').exists():
        raise SystemExit('No trained model. Run python run.py --train')
    from ews.extract import run as extract
    from ews.curate import run as curate
    from ews.india import run as india
    from ews.backtest import run_if_approved
    from ews.report import run as report
    from ews.evidence import audit_sources
    audit_sources(ROOT)
    extract(ROOT);curate(ROOT);india(ROOT);run_if_approved(ROOT)
    from ews.case_bhushan import run as case_bhushan
    case_bhushan(ROOT)
    from ews.reconcile_bhushan import run as reconcile_bhushan
    reconcile_bhushan(ROOT)
    if args.test:
        subprocess.run([sys.executable,'-m','pytest','tests','-q','--junitxml=results/test-results.xml'],cwd=ROOT,check=True)
    report(ROOT)
    print(f'Outputs written to {ROOT / "RESULTS.md"}')

if __name__=='__main__':main()
