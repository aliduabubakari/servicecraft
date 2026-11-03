import pandas as pd
import numpy as np
from sklearn.preprocessing._data import StandardScaler as StandardScaler
from sklearn.cluster._kmeans import KMeans as KMeans
import pickle as pickle
from sklearn.decomposition._pca import PCA as PCA
def check(d,cols,idcol):
 m=set(cols)-set(d.columns)
 if m:raise ValueError(str(m))
 if not d[idcol].is_unique or d[idcol].astype(str).str.strip().eq("").any():raise ValueError("id")
 for c in [x for x in cols if x not in {idcol,"team","position","route","vehicle_type","day_of_week","weather_condition"}]:d[c]=pd.to_numeric(d[c],errors="coerce")
 n=d.select_dtypes(include="number").columns
 if not np.isfinite(d[n].to_numpy(float)).all():raise ValueError("nonfinite")

