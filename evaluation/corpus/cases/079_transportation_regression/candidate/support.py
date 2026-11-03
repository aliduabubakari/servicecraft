import pandas as pd
import numpy as np
from sklearn.model_selection._split import train_test_split as train_test_split
from sklearn.pipeline import Pipeline as Pipeline
from sklearn.preprocessing._data import StandardScaler as StandardScaler
from sklearn.linear_model._base import LinearRegression as LinearRegression
import pickle as pickle
from sklearn.metrics._regression import mean_absolute_error as mean_absolute_error
from sklearn.metrics._regression import mean_squared_error as mean_squared_error
import json as json
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

