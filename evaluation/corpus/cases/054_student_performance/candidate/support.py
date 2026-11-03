import pandas as pd
import numpy as np
from sklearn.model_selection._split import train_test_split as train_test_split
from sklearn.pipeline import Pipeline as Pipeline
from sklearn.preprocessing._data import StandardScaler as StandardScaler
from sklearn.linear_model._ridge import Ridge as Ridge
import pickle as pickle
from sklearn.metrics._regression import mean_absolute_error as mean_absolute_error
from sklearn.metrics._regression import mean_squared_error as mean_squared_error
import json as json
def require(frame, columns, name):
    missing=sorted(set(columns)-set(frame.columns))
    if missing: raise ValueError(f"{name} missing columns: {missing}")
    if frame.empty: raise ValueError(f"{name} is empty")

def nonblank_unique(frame, columns, name):
    for column in columns:
        if frame[column].astype(str).str.strip().eq("").any() or frame.duplicated(columns).any():
            raise ValueError(f"{name} has blank or duplicate key {columns}")

def numeric(frame, columns, name):
    for column in columns: frame[column]=pd.to_numeric(frame[column],errors="coerce")
    if not np.isfinite(frame[columns].to_numpy(float)).all(): raise ValueError(f"{name} has missing/non-finite numeric values")

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")

