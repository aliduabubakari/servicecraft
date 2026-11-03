import pandas as pd
import numpy as np
import json as json
def require(frame,columns,name):
    missing=sorted(set(columns)-set(frame.columns))
    if missing:raise ValueError(f"{name} missing columns {missing}")
    if frame.empty:raise ValueError(f"{name} is empty")

def unique_nonblank(frame,columns,name):
    if frame.duplicated(columns).any() or any(frame[c].astype(str).str.strip().eq("").any() for c in columns):raise ValueError(f"{name} has invalid key {columns}")

def numeric(frame,columns,name):
    for column in columns:frame[column]=pd.to_numeric(frame[column],errors="coerce")
    if not np.isfinite(frame[columns].to_numpy(float)).all():raise ValueError(f"{name} has non-finite required values")

def write_json(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False,default=lambda item:item.item() if isinstance(item,np.generic) else str(item))+"\n")

