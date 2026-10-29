from pathlib import Path
import os,subprocess,sys
import joblib
import numpy as np
import pandas as pd
from ews.accounting import COMMON
from ews.benchmark import load_data

ROOT=Path(__file__).resolve().parents[1]

def test_saved_model_reproduces_recorded_predictions_in_fresh_process():
    env=dict(os.environ,PYTHONPATH=str(ROOT))
    subprocess.run([sys.executable,'-c',
        'import joblib,sys; m=joblib.load(sys.argv[1]); assert len(m.calibrated_classifiers_)==3',
        str(ROOT/'results/benchmark/model.joblib')],env=env,check=True,capture_output=True)
    clean,_=load_data(ROOT/'data/raw/polish-bankruptcy.zip')
    recorded=pd.read_csv(ROOT/'results/benchmark/holdout_predictions.csv').head(20)
    X=clean.set_index('row_id').loc[recorded.row_id,list(COMMON)]
    actual=joblib.load(ROOT/'results/benchmark/model.joblib').predict_proba(X)[:,1]
    assert np.allclose(actual,recorded.score,atol=1e-12)

def test_actual_model_shap_values_sum_to_displayed_scores():
    contributions=pd.read_csv(ROOT/'results/india/pilot_shap_contributions.csv')
    scores=pd.read_csv(ROOT/'results/india/pilot_scores.csv').set_index('entity_id').score
    reconstructed=contributions.groupby('entity_id').contribution.sum()+contributions.groupby('entity_id').base_value.first()
    assert np.allclose(reconstructed.loc[scores.index],scores,atol=1e-6)
