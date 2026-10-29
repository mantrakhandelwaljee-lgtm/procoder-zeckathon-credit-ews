"""Importable transforms so saved models also load in fresh processes."""
import numpy as np
from sklearn.base import BaseEstimator,TransformerMixin

class Winsorize(BaseEstimator, TransformerMixin):
    def __init__(self,lower=.005,upper=.995): self.lower=lower;self.upper=upper
    def fit(self,X,y=None):
        a=np.asarray(X,dtype=float).copy();a[~np.isfinite(a)]=np.nan
        self.lo_=np.nanquantile(a,self.lower,axis=0);self.hi_=np.nanquantile(a,self.upper,axis=0)
        return self
    def transform(self,X):
        a=np.asarray(X,dtype=float).copy();a[~np.isfinite(a)]=np.nan
        return np.clip(a,self.lo_,self.hi_)
    def get_feature_names_out(self,input_features=None):return np.asarray(input_features)
