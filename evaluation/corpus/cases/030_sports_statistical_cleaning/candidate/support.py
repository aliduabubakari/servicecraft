import pandas as pd
import numpy as np
import json as json
def req(d,c,n):
    m=sorted(set(c)-set(d.columns))
    if m:raise ValueError(f"{n} missing {m}")

def key(d,c,n):
    if not d[c].is_unique or d[c].astype(str).str.strip().eq("").any():raise ValueError(f"{n} key")

def nums(d,c,n):
    for x in c:d[x]=pd.to_numeric(d[x],errors="coerce")
    if not np.isfinite(d[c].to_numpy(float)).all():raise ValueError(f"{n} nonfinite")

def js(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")

