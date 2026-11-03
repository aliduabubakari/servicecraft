import pandas as pd
import numpy as np
from sklearn.model_selection._split import train_test_split as train_test_split
from sklearn.pipeline import Pipeline as Pipeline
from sklearn.compose._column_transformer import ColumnTransformer as ColumnTransformer
from sklearn.preprocessing._data import StandardScaler as StandardScaler
from sklearn.preprocessing._encoders import OneHotEncoder as OneHotEncoder
from sklearn.linear_model._logistic import LogisticRegression as LogisticRegression
import pickle as pickle
import json as json
from sklearn.metrics._classification import accuracy_score as accuracy_score
from sklearn.metrics._classification import precision_score as precision_score
from sklearn.metrics._classification import recall_score as recall_score
from sklearn.metrics._classification import f1_score as f1_score
from sklearn.metrics._ranking import roc_auc_score as roc_auc_score
def prep(d,cols,idc):
 if set(cols)-set(d):raise ValueError("columns")
 if not d[idc].is_unique or d[idc].astype(str).str.strip().eq("").any():raise ValueError("id")
 for c in cols:
  if c not in {idc,"team","position","route","vehicle_type","day_of_week","weather_condition"}:d[c]=pd.to_numeric(d[c],errors="coerce")
 if not np.isfinite(d.select_dtypes('number').to_numpy(float)).all():raise ValueError("nonfinite")

def js(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")

def haversine(lat1,lon1,lat2,lon2):
 p1,p2=np.radians(lat1),np.radians(lat2);dp=np.radians(lat2-lat1);dl=np.radians(lon2-lon1);a=np.sin(dp/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2;return 6371.0088*2*np.arctan2(np.sqrt(a),np.sqrt(1-a))

