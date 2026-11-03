import pandas as pd
import numpy as np
from sklearn.model_selection._split import train_test_split as train_test_split
from sklearn.pipeline import Pipeline as Pipeline
from sklearn.preprocessing._data import StandardScaler as StandardScaler
from sklearn.linear_model._logistic import LogisticRegression as LogisticRegression
import pickle as pickle
from sklearn.metrics._classification import accuracy_score as accuracy_score
from sklearn.metrics._classification import precision_score as precision_score
from sklearn.metrics._classification import recall_score as recall_score
from sklearn.metrics._classification import f1_score as f1_score
from sklearn.metrics._ranking import roc_auc_score as roc_auc_score
import json as json
def check(d,cols,idcol):
 m=set(cols)-set(d.columns)
 if m:raise ValueError(str(m))
 if not d[idcol].is_unique or d[idcol].astype(str).str.strip().eq("").any():raise ValueError("id")
 for c in [x for x in cols if x not in {idcol,"team","position","route","vehicle_type","day_of_week","weather_condition"}]:d[c]=pd.to_numeric(d[c],errors="coerce")
 n=d.select_dtypes(include="number").columns
 if not np.isfinite(d[n].to_numpy(float)).all():raise ValueError("nonfinite")

def js(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")

