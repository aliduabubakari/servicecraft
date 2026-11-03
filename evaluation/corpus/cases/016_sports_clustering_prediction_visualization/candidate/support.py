import pandas as pd
import numpy as np
from sklearn.preprocessing._data import StandardScaler as StandardScaler
from sklearn.cluster._kmeans import KMeans as KMeans
import json as json
def prep(d,cols,idc):
 if set(cols)-set(d):raise ValueError("columns")
 if not d[idc].is_unique or d[idc].astype(str).str.strip().eq("").any():raise ValueError("id")
 for c in cols:
  if c not in {idc,"team","position","route","vehicle_type","day_of_week","weather_condition"}:d[c]=pd.to_numeric(d[c],errors="coerce")
 if not np.isfinite(d.select_dtypes('number').to_numpy(float)).all():raise ValueError("nonfinite")

def js(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")

