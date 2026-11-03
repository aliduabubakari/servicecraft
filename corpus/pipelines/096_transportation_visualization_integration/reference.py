"""Executable behavioral references for batch 17."""
import argparse,pickle,sys
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,f1_score,precision_score,recall_score,roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
TOOLS=Path(__file__).resolve().parents[2]/'tools';sys.path.insert(0,str(TOOLS))
from batch08_reference import js
from batch11_reference import prediction_parallel
from batch16_reference import trip_fanout

def valid(d,cols,idc,cats=()):
 if set(cols)-set(d):raise ValueError('columns')
 if not d[idc].is_unique or d[idc].astype(str).str.strip().eq('').any():raise ValueError('id')
 for c in cats:
  if d[c].isna().any() or d[c].astype(str).str.strip().eq('').any():raise ValueError('category')
 nums=[c for c in cols if c not in {idc,*cats}]
 for c in nums:d[c]=pd.to_numeric(d[c],errors='coerce')
 if not np.isfinite(d[nums].to_numpy(float)).all():raise ValueError('nonfinite')

def recovery_linear(data,out):
 d=pd.read_csv(data/'data.csv',keep_default_na=True);cols=['player_id','team','position','games_played','points_per_game','assists_per_game','rebounds_per_game','minutes_per_game','age','experience_years','salary_millions'];
 if set(cols)-set(d):raise ValueError('columns')
 if not d.player_id.is_unique or d.player_id.astype(str).str.strip().eq('').any():raise ValueError('id')
 for c in ['team','position']:d[c]=d[c].replace(r'^\s*$',np.nan,regex=True)
 nums=[c for c in cols if c not in {'player_id','team','position'}]
 for c in nums:d[c]=pd.to_numeric(d[c],errors='coerce')
 audit={'rows':len(d),'missing':{c:int(d[c].isna().sum()) for c in cols},'total_missing':int(d[cols].isna().sum().sum())};d['missing_points_input']=d.points_per_game.isna().astype(int);d['missing_salary_input']=d.salary_millions.isna().astype(int);d['missing_team_input']=d.team.isna().astype(int);d['missing_position_input']=d.position.isna().astype(int);flags=['missing_points_input','missing_salary_input','missing_team_input','missing_position_input'];d[[*cols,*flags]].sort_values('player_id').to_csv(out/'audited_players.csv',index=False);js(out/'validation_audit.json',audit)
 n=d.copy();recovered_numeric={}
 for c in nums:
  mask=n[c].isna();recovered_numeric[c]=int(mask.sum());group=n.groupby('position')[c].transform('median');n.loc[mask,c]=group[mask];n[c]=n[c].fillna(n[c].median())
 if not np.isfinite(n[nums].to_numpy(float)).all():raise ValueError('numeric recovery')
 n[[*cols,*flags]].sort_values('player_id').to_csv(out/'numeric_recovered.csv',index=False);recovered_categorical={}
 for c in ['team','position']:
  mask=n[c].isna();recovered_categorical[c]=int(mask.sum());counts=n[c].dropna().value_counts();mode=sorted(counts[counts==counts.max()].index.astype(str))[0];n.loc[mask,c]=mode
 n[[*cols,*flags]].sort_values('player_id').to_csv(out/'players_recovered.csv',index=False);summary=n.groupby('team',as_index=False).agg(player_count=('player_id','size'),mean_points=('points_per_game','mean'),mean_salary=('salary_millions','mean'),mean_experience=('experience_years','mean'),recovered_points=('missing_points_input','sum'),recovered_salary=('missing_salary_input','sum'),recovered_team=('missing_team_input','sum'),recovered_position=('missing_position_input','sum')).sort_values('team');summary.to_csv(out/'team_summary.csv',index=False);js(out/'recovery_report.json',{'rows':len(n),'input_missing':audit['total_missing'],'numeric_recovered':recovered_numeric,'categorical_recovered':recovered_categorical,'remaining_missing':int(n[cols].isna().sum().sum()),'team_players':int(summary.player_count.sum()),'teams':len(summary)})

def prediction_multiview(data,out):
 d=pd.read_csv(data/'data.csv');cols=['trip_id','route','vehicle_type','departure_hour','distance_km','passengers','fare_amount','delay_minutes','day_of_week','is_holiday','weather_condition','is_delayed','cancellation_risk'];valid(d,cols,'trip_id',['route','vehicle_type','day_of_week','weather_condition']);assert set(d.is_delayed.unique())<={0,1};d=d[cols].sort_values('trip_id');d.to_csv(out/'trips_clean.csv',index=False);op=d[['trip_id','departure_hour','distance_km','passengers','fare_amount','is_holiday','cancellation_risk']].copy();op['passenger_km']=op.distance_km*op.passengers;op['fare_per_passenger']=np.where(op.passengers>0,op.fare_amount/op.passengers,0);op.to_csv(out/'operational_features.csv',index=False);ctx=d[['trip_id','route','vehicle_type','day_of_week','weather_condition','delay_minutes','is_delayed']].copy();ctx.to_csv(out/'context_features.csv',index=False);m=op.merge(ctx,on='trip_id',validate='one_to_one');m.to_csv(out/'model_data.csv',index=False);nums=['departure_hour','distance_km','passengers','fare_amount','is_holiday','cancellation_risk','passenger_km','fare_per_passenger'];cats=['route','vehicle_type','day_of_week','weather_condition'];features=nums+cats;tr,te=train_test_split(m,test_size=.25,random_state=42,stratify=m.is_delayed);model=Pipeline([('features',ColumnTransformer([('numeric',StandardScaler(),nums),('categorical',OneHotEncoder(handle_unknown='ignore'),cats)])),('model',LogisticRegression(C=1,solver='liblinear',max_iter=1000,random_state=42))]);model.fit(tr[features],tr.is_delayed);prob=model.predict_proba(te[features])[:,1];yp=(prob>=.5).astype(int)
 with (out/'delay_model.pkl').open('wb') as h:pickle.dump(model,h)
 pd.DataFrame({'trip_id':te.trip_id,'actual_is_delayed':te.is_delayed,'probability':prob,'predicted_is_delayed':yp}).sort_values('trip_id').to_csv(out/'delay_predictions.csv',index=False);js(out/'delay_metrics.json',{'train_rows':len(tr),'test_rows':len(te),'accuracy':accuracy_score(te.is_delayed,yp),'precision':precision_score(te.is_delayed,yp,zero_division=0),'recall':recall_score(te.is_delayed,yp,zero_division=0),'f1':f1_score(te.is_delayed,yp,zero_division=0),'roc_auc':roc_auc_score(te.is_delayed,prob)});route=m.groupby('route',as_index=False).agg(trip_count=('trip_id','size'),delay_rate=('is_delayed','mean'),mean_delay=('delay_minutes','mean'),mean_cancellation_risk=('cancellation_risk','mean')).sort_values('route');route.to_csv(out/'route_diagnostics.csv',index=False);weather=m.groupby('weather_condition',as_index=False).agg(trip_count=('trip_id','size'),delay_rate=('is_delayed','mean'),mean_delay=('delay_minutes','mean'),mean_cancellation_risk=('cancellation_risk','mean')).sort_values('weather_condition');weather.to_csv(out/'weather_diagnostics.csv',index=False);vehicle=m.groupby('vehicle_type',as_index=False).agg(trip_count=('trip_id','size'),delay_rate=('is_delayed','mean'),mean_cancellation_risk=('cancellation_risk','mean'),mean_passenger_km=('passenger_km','mean')).sort_values('vehicle_type');vehicle.to_csv(out/'vehicle_risk_diagnostics.csv',index=False);js(out/'delay_report.json',{'trips':len(m),'model_test_rows':len(te),'route_trips':int(route.trip_count.sum()),'weather_trips':int(weather.trip_count.sum()),'vehicle_trips':int(vehicle.trip_count.sum()),'routes':len(route),'weather_conditions':len(weather),'vehicle_types':len(vehicle)})

def operations_fanin(data,out):
 d=pd.read_csv(data/'data.csv');cols=['trip_id','route','vehicle_type','distance_km','passengers','fare_amount','delay_minutes','weather_condition'];valid(d,cols,'trip_id',['route','vehicle_type','weather_condition']);x=d.copy();x['passenger_km']=x.distance_km*x.passengers;x['on_time']=(x.delay_minutes<=5).astype(int);route=x.groupby('route',as_index=False).agg(trip_count=('trip_id','size'),total_passenger_km=('passenger_km','sum'),mean_delay=('delay_minutes','mean'),on_time_rate=('on_time','mean')).sort_values('route');route.to_csv(out/'route_operations.csv',index=False);vehicle=x.groupby('vehicle_type',as_index=False).agg(trip_count=('trip_id','size'),mean_passengers=('passengers','mean'),mean_fare=('fare_amount','mean'),mean_delay=('delay_minutes','mean')).sort_values('vehicle_type');vehicle.to_csv(out/'vehicle_operations.csv',index=False);weather=x.groupby('weather_condition',as_index=False).agg(trip_count=('trip_id','size'),total_passenger_km=('passenger_km','sum'),mean_delay=('delay_minutes','mean'),on_time_rate=('on_time','mean')).sort_values('weather_condition');weather.to_csv(out/'weather_operations.csv',index=False);js(out/'operations_report.json',{'trips':int(route.trip_count.sum()),'route_trips':int(route.trip_count.sum()),'vehicle_trips':int(vehicle.trip_count.sum()),'weather_trips':int(weather.trip_count.sum()),'routes':len(route),'vehicle_types':len(vehicle),'weather_conditions':len(weather)})

RUNNERS={'045_sports_visualization_cleaning_recovery':recovery_linear,'070_transportation_prediction_cleaning_validation':prediction_parallel,'077_transportation_prediction_visualization_integration':prediction_multiview,'091_transportation_visualization':trip_fanout,'096_transportation_visualization_integration':operations_fanin}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);x=p.parse_args();x.output_dir.mkdir(parents=True,exist_ok=True);RUNNERS[Path(__file__).resolve().parent.name](x.data_dir,x.output_dir)
