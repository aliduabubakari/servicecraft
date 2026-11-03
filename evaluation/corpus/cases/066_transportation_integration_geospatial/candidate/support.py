import pandas as pd
import numpy as np
def valid(d,cols,idc,cats=()):
 if set(cols)-set(d):raise ValueError('columns')
 if not d[idc].is_unique or d[idc].astype(str).str.strip().eq('').any():raise ValueError('id')
 for c in cats:
  if d[c].isna().any() or d[c].astype(str).str.strip().eq('').any():raise ValueError('category')
 nums=[c for c in cols if c not in {idc,*cats}]
 for c in nums:d[c]=pd.to_numeric(d[c],errors='coerce')
 if not np.isfinite(d[nums].to_numpy(float)).all():raise ValueError('nonfinite')

def haversine(lat1,lon1,lat2,lon2):
 p1,p2=np.radians(lat1),np.radians(lat2);dp=np.radians(lat2-lat1);dl=np.radians(lon2-lon1);a=np.sin(dp/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2;return 6371.0088*2*np.arctan2(np.sqrt(a),np.sqrt(1-a))

