"""Executable behavioral references for the final partial batch 21."""
import argparse,sys
from pathlib import Path
import numpy as np,pandas as pd
TOOLS=Path(__file__).resolve().parents[2]/'tools';sys.path.insert(0,str(TOOLS))
from batch08_reference import js
from batch18_reference import recovery_fanout

def route_linear(data,out):
 d=pd.read_csv(data/'data.csv');cols=['trip_id','route','vehicle_type','departure_hour','distance_km','passengers','fare_amount','delay_minutes','day_of_week','is_holiday','weather_condition']
 if set(cols)-set(d):raise ValueError('columns')
 if not d.trip_id.is_unique or d.trip_id.astype(str).str.strip().eq('').any():raise ValueError('id')
 for c in ['route','vehicle_type','day_of_week','weather_condition']:
  if d[c].isna().any() or d[c].astype(str).str.strip().eq('').any():raise ValueError('category')
 nums=[c for c in cols if c not in {'trip_id','route','vehicle_type','day_of_week','weather_condition'}]
 for c in nums:d[c]=pd.to_numeric(d[c],errors='coerce')
 if not np.isfinite(d[nums].to_numpy(float)).all():raise ValueError('nonfinite')
 x=d[cols].sort_values('trip_id').copy();x['passenger_km']=x.distance_km*x.passengers;x['on_time']=(x.delay_minutes<=5).astype(int);x.to_csv(out/'trips_prepared.csv',index=False);routes=x.groupby('route',as_index=False).agg(trip_count=('trip_id','size'),total_passenger_km=('passenger_km','sum'),mean_passengers=('passengers','mean'),mean_fare=('fare_amount','mean'),mean_delay=('delay_minutes','mean'),on_time_rate=('on_time','mean')).sort_values('route');routes.to_csv(out/'route_summary.csv',index=False);rank=routes.sort_values(['total_passenger_km','on_time_rate','route'],ascending=[False,False,True]).reset_index(drop=True);rank.insert(1,'rank',np.arange(1,len(rank)+1));rank.to_csv(out/'route_ranking.csv',index=False);chart=rank[['route','rank','trip_count','total_passenger_km','mean_delay','on_time_rate']].copy();chart['passenger_km_label']=chart.total_passenger_km.round(2).astype(str);chart.to_csv(out/'route_chart_data.csv',index=False);js(out/'route_report.json',{'trips':int(rank.trip_count.sum()),'routes':len(rank),'top_route':rank.iloc[0].route,'top_total_passenger_km':rank.iloc[0].total_passenger_km})

RUNNERS={'053_sports_visualization_validation_recovery':recovery_fanout,'100_transportation_visualization_v2':route_linear}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);x=p.parse_args();x.output_dir.mkdir(parents=True,exist_ok=True);RUNNERS[Path(__file__).resolve().parent.name](x.data_dir,x.output_dir)
