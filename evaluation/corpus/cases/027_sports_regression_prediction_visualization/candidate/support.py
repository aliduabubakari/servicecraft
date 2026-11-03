import pandas as pd
import numpy as np
from sklearn.model_selection._split import train_test_split as train_test_split
from sklearn.pipeline import Pipeline as Pipeline
from sklearn.preprocessing._data import StandardScaler as StandardScaler
from sklearn.linear_model._ridge import Ridge as Ridge
import pickle as pickle
import json as json
from sklearn.metrics._regression import mean_absolute_error as mean_absolute_error
from sklearn.metrics._regression import mean_squared_error as mean_squared_error
from sklearn.metrics._regression import r2_score as r2_score
from sklearn.linear_model._logistic import LogisticRegression as LogisticRegression
from sklearn.metrics._classification import accuracy_score as accuracy_score
from sklearn.metrics._classification import precision_score as precision_score
from sklearn.metrics._classification import recall_score as recall_score
from sklearn.metrics._classification import f1_score as f1_score
from sklearn.metrics._ranking import roc_auc_score as roc_auc_score
def valid(d,cols,idc,cats=()):
 if set(cols)-set(d):raise ValueError('columns')
 if not d[idc].is_unique or d[idc].astype(str).str.strip().eq('').any():raise ValueError('id')
 for c in cats:
  if d[c].isna().any() or d[c].astype(str).str.strip().eq('').any():raise ValueError('category')
 nums=[c for c in cols if c not in {idc,*cats}]
 for c in nums:d[c]=pd.to_numeric(d[c],errors='coerce')
 if not np.isfinite(d[nums].to_numpy(float)).all():raise ValueError('nonfinite')

def js(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")

