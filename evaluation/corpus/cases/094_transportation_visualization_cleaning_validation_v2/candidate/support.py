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

