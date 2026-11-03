import pandas as pd
import numpy as np
import json as json
def prep(d,cols,idc):
 if set(cols)-set(d):raise ValueError("columns")
 if not d[idc].is_unique or d[idc].astype(str).str.strip().eq("").any():raise ValueError("id")
 for c in cols:
  if c not in {idc,"team","position","route","vehicle_type","day_of_week","weather_condition"}:d[c]=pd.to_numeric(d[c],errors="coerce")
 if not np.isfinite(d.select_dtypes('number').to_numpy(float)).all():raise ValueError("nonfinite")

def haversine(lat1,lon1,lat2,lon2):
 p1,p2=np.radians(lat1),np.radians(lat2);dp=np.radians(lat2-lat1);dl=np.radians(lon2-lon1);a=np.sin(dp/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2;return 6371.0088*2*np.arctan2(np.sqrt(a),np.sqrt(1-a))

def js(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")

