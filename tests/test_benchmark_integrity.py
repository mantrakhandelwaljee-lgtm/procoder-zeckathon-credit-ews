from pathlib import Path
import numpy as np
import pandas as pd
from ews.benchmark import load_data, Winsorize
from ews.accounting import COMMON

ROOT=Path(__file__).resolve().parents[1]

def test_actual_deployed_vectors_do_not_cross_frozen_split():
    x,a=load_data(ROOT/'data/raw/polish-bankruptcy.zip')
    s=pd.read_csv(ROOT/'results/benchmark/frozen_split.csv')
    x['split']=s['split'];x['deployed_hash']=pd.util.hash_pandas_object(x[list(COMMON)],index=False)
    assert x.groupby('deployed_hash').split.nunique().max()==1
    assert x.groupby('feature_hash').split.nunique().max()==1
    assert a['exact_duplicate_full_rows']==60

def test_clip_limits_learned_only_from_training():
    x=np.arange(100,dtype=float).reshape(-1,1)
    clip=Winsorize().fit(x);before=clip.hi_.copy()
    assert clip.transform([[1e20]])[0,0]==before[0]
    assert np.array_equal(clip.hi_,before)
