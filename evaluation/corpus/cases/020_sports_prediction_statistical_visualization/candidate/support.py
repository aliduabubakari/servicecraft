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
def req(d,c,n):
    m=sorted(set(c)-set(d.columns))
    if m:raise ValueError(f"{n} missing {m}")

def key(d,c,n):
    if not d[c].is_unique or d[c].astype(str).str.strip().eq("").any():raise ValueError(f"{n} key")

def nums(d,c,n):
    for x in c:d[x]=pd.to_numeric(d[x],errors="coerce")
    if not np.isfinite(d[c].to_numpy(float)).all():raise ValueError(f"{n} nonfinite")

def js(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")

