import pandas as pd
import numpy as np
from sklearn.model_selection._split import train_test_split as train_test_split
from sklearn.pipeline import Pipeline as Pipeline
from sklearn.preprocessing._data import StandardScaler as StandardScaler
from sklearn.linear_model._logistic import LogisticRegression as LogisticRegression
import pickle as pickle
import json as json
from sklearn.metrics._classification import accuracy_score as accuracy_score
from sklearn.metrics._classification import precision_score as precision_score
from sklearn.metrics._classification import recall_score as recall_score
from sklearn.metrics._classification import f1_score as f1_score
from sklearn.metrics._ranking import roc_auc_score as roc_auc_score
def req(d,cols,name):
    missing=sorted(set(cols)-set(d.columns))
    if missing:raise ValueError(f"{name} missing {missing}")
    if d.empty:raise ValueError(f"{name} empty")

def key(d,col,name):
    if not d[col].is_unique or d[col].astype(str).str.strip().eq("").any():raise ValueError(f"{name} invalid {col}")

def nums(d,cols,name):
    for c in cols:d[c]=pd.to_numeric(d[c],errors="coerce")
    if not np.isfinite(d[cols].to_numpy(float)).all():raise ValueError(f"{name} non-finite values")

def js(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")

