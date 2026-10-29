"""Frozen, duplicate-controlled benchmark; nested calibration of the selected configuration."""
from __future__ import annotations
import hashlib, io, json, zipfile, warnings
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.metrics import average_precision_score, precision_recall_curve, auc, roc_auc_score, brier_score_loss
from .accounting import COMMON
from .policy import error_cost, optimize_policy
from .preprocessing import Winsorize

SEED=271828

def load_data(archive):
    with zipfile.ZipFile(archive) as z: raw=z.read('5year.arff')
    body=raw.decode().split('@data',1)[1]
    df=pd.read_csv(io.StringIO(body),header=None,na_values='?',skipinitialspace=True)
    df.columns=[f'X{i}' for i in range(1,65)]+['label']
    df['row_id']=np.arange(len(df))
    df['feature_hash']=pd.util.hash_pandas_object(df[[f'X{i}' for i in range(1,65)]],index=False).astype(str)
    conflicts=df.groupby('feature_hash').label.nunique();bad=set(conflicts[conflicts>1].index)
    audit={'raw_rows':len(df),'raw_positives':int(df.label.sum()),
           'exact_duplicate_full_rows':int(df.drop(columns=['row_id','feature_hash']).duplicated().sum()),
           'conflicting_feature_groups':len(bad)}
    clean=df[~df.feature_hash.isin(bad)].drop_duplicates('feature_hash').reset_index(drop=True)
    audit.update(clean_rows=len(clean),clean_positives=int(clean.label.sum()),
                 clean_prevalence=float(clean.label.mean()),archive_sha256=hashlib.sha256(Path(archive).read_bytes()).hexdigest())
    return clean,audit

def make_pipeline(kind,C=1.,balanced=False,depth=3):
    if kind=='logistic': model=LogisticRegression(C=C,class_weight='balanced' if balanced else None,max_iter=2500,random_state=SEED)
    else:model=HistGradientBoostingClassifier(max_iter=160,learning_rate=.06,max_leaf_nodes=15,
        max_depth=depth,l2_regularization=2,min_samples_leaf=30,early_stopping=False,
        class_weight='balanced' if balanced else None,random_state=SEED)
    return Pipeline([('clip',Winsorize()),('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),
                     ('scale',StandardScaler()),('model',model)])

def metric_values(y,p):
    prec,rec,_=precision_recall_curve(y,p)
    return {'average_precision':float(average_precision_score(y,p)),
            'pr_auc_trapezoidal':float(auc(rec,prec)), 'roc_auc':float(roc_auc_score(y,p)),
            'brier_score':float(brier_score_loss(y,p)),'prevalence':float(np.mean(y))}

def top_policy(y,p,rate=.05):
    selected=np.zeros(len(y),dtype=bool)
    selected[np.argsort(-p,kind='stable')[:int(np.floor(rate*len(y)+1e-10))]]=True
    return selected

def run(root):
    root=Path(root);out=root/'results'/'benchmark';out.mkdir(parents=True,exist_ok=True)
    clean,audit=load_data(root/'data/raw/polish-bankruptcy.zip')
    # Group on the ACTUAL deployed feature subset, not only the original 64-column record.
    # Different 64-column records may collapse to identical 12-column vectors.
    groups=pd.util.hash_pandas_object(clean[list(COMMON)],index=False).astype(str).to_numpy()
    train_idx,test_idx=next(StratifiedGroupKFold(5,shuffle=True,random_state=SEED).split(clean,clean.label,groups))
    split=clean[['row_id','feature_hash','label']].copy();split['split']='development';split.loc[test_idx,'split']='holdout'
    split_path=out/'frozen_split.csv'
    if split_path.exists():
        old=pd.read_csv(split_path,dtype={'feature_hash':str})
        if not old.equals(split):raise RuntimeError('Frozen split mismatch; investigate data/config changes before proceeding')
    else: split.to_csv(split_path,index=False)
    assert not set(split.loc[train_idx,'feature_hash']) & set(split.loc[test_idx,'feature_hash'])
    assert not set(groups[train_idx]) & set(groups[test_idx])
    audit['deployed_feature_duplicate_rows']=int(pd.Series(groups).duplicated().sum())
    audit['deployed_feature_groups_crossing_holdout']=0
    features=list(COMMON);X=clean[features];y=clean.label.to_numpy(dtype=int)
    Xdev,ydev=X.iloc[train_idx],y[train_idx]
    cv=list(StratifiedGroupKFold(3,shuffle=True,random_state=SEED+1).split(Xdev,ydev,groups[train_idx]))
    configs=[{'kind':'logistic','C':c,'balanced':b} for c in [.1,1.,10.] for b in [False,True]]
    configs += [{'kind':'hist_boost','balanced':b,'depth':d} for d in [3,5] for b in [False,True]]
    rows=[]
    for config in configs:
        model=make_pipeline(**config)
        p=cross_val_predict(model,Xdev,ydev,cv=cv,method='predict_proba',n_jobs=1)[:,1]
        m=metric_values(ydev,p); m.update(config=config,top5=error_cost(ydev,top_policy(ydev,p)))
        rows.append(m)
        print('Development',config,'AP',round(m['average_precision'],4),flush=True)
    best=max(rows,key=lambda r:(r['average_precision'],-r['top5']['cost']))
    base=make_pipeline(**best['config'])
    # Calibration is nested within the already-selected configuration.
    # Configuration selection used all development CV labels; this is not fully nested model selection.
    # Outer validation rows are excluded from estimator/calibrator fitting, not configuration selection.
    pdev=np.zeros(len(ydev))
    for outer_train,outer_valid in cv:
        inner=list(StratifiedGroupKFold(3,shuffle=True,random_state=SEED+2).split(
            Xdev.iloc[outer_train],ydev[outer_train],groups[train_idx][outer_train]))
        nested=CalibratedClassifierCV(make_pipeline(**best['config']),method='sigmoid',cv=inner,ensemble=True,n_jobs=1)
        nested.fit(Xdev.iloc[outer_train],ydev[outer_train])
        pdev[outer_valid]=nested.predict_proba(Xdev.iloc[outer_valid])[:,1]
    calibrated=CalibratedClassifierCV(base,method='sigmoid',cv=cv,ensemble=True,n_jobs=1)
    best_policy,policy_curve=optimize_policy(ydev,pdev)
    calibrated.fit(Xdev,ydev)
    # All configuration decisions above precede this hold-out prediction.
    ptest=calibrated.predict_proba(X.iloc[test_idx])[:,1]
    top=top_policy(y[test_idx],ptest)
    production=top & (ptest>best_policy['threshold'])
    fixed_cost=top & (ptest>1/21)
    test_report={'sample_count':len(test_idx),'positive_count':int(y[test_idx].sum()),
        **metric_values(y[test_idx],ptest),'top5':error_cost(y[test_idx],top),
        'development_selected_threshold_with_cap':error_cost(y[test_idx],production),
        'theoretical_1_over_21_with_cap':error_cost(y[test_idx],fixed_cost),
        'no_alert':error_cost(y[test_idx],np.zeros(len(test_idx),dtype=bool))}
    # Conditional uncertainty, resampling test observations with class stratification.
    rng=np.random.default_rng(SEED+10);pos=np.flatnonzero(y[test_idx]==1);neg=np.flatnonzero(y[test_idx]==0)
    aps=[];recalls=[]
    for _ in range(1000):
        ix=np.r_[rng.choice(pos,len(pos)),rng.choice(neg,len(neg))]
        yt,pt=y[test_idx][ix],ptest[ix]
        aps.append(average_precision_score(yt,pt));recalls.append(error_cost(yt,top_policy(yt,pt))['recall'])
    test_report['ap_bootstrap_95_interval']=[float(x) for x in np.quantile(aps,[.025,.975])]
    test_report['top5_recall_bootstrap_95_interval']=[float(x) for x in np.quantile(recalls,[.025,.975])]
    report={'dataset':'UCI Polish Companies Bankruptcy / 5year.arff / 1-year horizon',
        'source':'https://archive.ics.uci.edu/dataset/365/polish+companies+bankruptcy+data',
        'protocol_version':'2: grouped on deployed 12-feature vectors in hold-out, selection and calibration',
        'seed':SEED,'features':COMMON,'data_audit':audit,'development_rows':len(train_idx),
        'development_positives':int(ydev.sum()),'selection_metric':'development out-of-fold average precision; cost tie-break',
        'selected_config':best['config'],'calibration':'nested 3-fold sigmoid; final 3-fold ensemble on development',
        'development_selected_policy':{k:(None if isinstance(v,float) and not np.isfinite(v) else v) for k,v in best_policy.items()},
        'holdout':test_report,
        'limitations':['Anonymous records: calendar-time and issuer-disjoint validation cannot be established.',
            'Exact-feature duplicates grouped; unknown related observations may remain.',
            'Bootstrap intervals are conditional on this dataset and do not capture issuer clustering or model selection.',
            'Transferred Indian scores are not calibrated Indian probabilities.',
            'No claim of Indian recall follows from this benchmark.']}
    (out/'metrics.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    (out/'development_comparison.json').write_text(json.dumps(rows,indent=2))
    pd.DataFrame(policy_curve).to_csv(out/'development_policy_curve.csv',index=False)
    pd.DataFrame({'row_id':clean.iloc[test_idx].row_id,'label':y[test_idx],'score':ptest,'top5_selected':top,
                  'cost_policy_selected':production}).to_csv(out/'holdout_predictions.csv',index=False)
    pd.DataFrame({'row_id':clean.iloc[train_idx].row_id,'label':ydev,'score':pdev}).to_csv(out/'development_oof_predictions.csv',index=False)
    joblib.dump(calibrated,out/'model.joblib')
    # A separately fitted uncalibrated selected estimator provides transparent raw-score contributions.
    base.fit(Xdev,ydev);joblib.dump(base,out/'explanation_model.joblib')
    pd.DataFrame({'feature':features,'low':base['clip'].lo_,'high':base['clip'].hi_}).to_csv(out/'training_feature_ranges.csv',index=False)
    plot_results(y[test_idx],ptest,out)
    print(json.dumps(test_report,indent=2),flush=True)
    return report

def plot_results(y,p,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from sklearn.calibration import calibration_curve
    fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
    precision,recall,_=precision_recall_curve(y,p)
    axes[0].plot(recall,precision,color='#087f8c',lw=2,label=f'AP {average_precision_score(y,p):.3f}')
    axes[0].axhline(np.mean(y),ls='--',color='#888',label=f'Prevalence {np.mean(y):.3f}')
    axes[0].set(xlabel='Recall',ylabel='Precision',title='Untouched hold-out: precision-recall',xlim=(0,1),ylim=(0,1));axes[0].legend()
    prob_true,prob_pred=calibration_curve(y,p,n_bins=8,strategy='quantile')
    axes[1].plot(prob_pred,prob_true,'o-',color='#087f8c');axes[1].plot([0,1],[0,1],'--',color='#888')
    axes[1].set(xlabel='Mean predicted probability',ylabel='Observed bankruptcy fraction',title='Calibration on Polish hold-out')
    for ax in axes:ax.spines[['top','right']].set_visible(False)
    fig.savefig(out/'benchmark-validation.png',dpi=180);plt.close(fig)

if __name__=='__main__':
    import sys
    run(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
