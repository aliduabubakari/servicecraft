"""Executable behavioral references for batch 20."""
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
from batch16_reference import position_linear,trip_fanout
from batch17_reference import operations_fanin
from batch18_reference import recovery_fanout

def prediction_recovery_multiview(data,out):
 d=pd.read_csv(data/'data.csv',keep_default_na=True);cols=['trip_id','route','vehicle_type','departure_hour','distance_km','passengers','fare_amount','delay_minutes','day_of_week','is_holiday','weather_condition','is_delayed','cancellation_risk']
 if set(cols)-set(d):raise ValueError('columns')
 if not d.trip_id.is_unique or d.trip_id.astype(str).str.strip().eq('').any():raise ValueError('id')
 cats=['route','vehicle_type','day_of_week','weather_condition']
 for c in cats:d[c]=d[c].replace(r'^\s*$',np.nan,regex=True)
 nums=[c for c in cols if c not in {'trip_id',*cats}]
 for c in nums:d[c]=pd.to_numeric(d[c],errors='coerce')
 d['missing_distance_input']=d.distance_km.isna().astype(int);d['missing_fare_input']=d.fare_amount.isna().astype(int);d['missing_vehicle_input']=d.vehicle_type.isna().astype(int);d['missing_weather_input']=d.weather_condition.isna().astype(int);flags=['missing_distance_input','missing_fare_input','missing_vehicle_input','missing_weather_input'];d[[*cols,*flags]].sort_values('trip_id').to_csv(out/'audited_trips.csv',index=False)
 x=d.copy();recovered_numeric={}
 for c in nums:
  mask=x[c].isna();recovered_numeric[c]=int(mask.sum());group=x.groupby('route')[c].transform('median');x.loc[mask,c]=group[mask];x[c]=x[c].fillna(x[c].median())
 recovered_categorical={}
 for c in cats:
  mask=x[c].isna();recovered_categorical[c]=int(mask.sum());counts=x[c].dropna().value_counts();mode=sorted(counts[counts==counts.max()].index.astype(str))[0];x.loc[mask,c]=mode
 if not np.isfinite(x[nums].to_numpy(float)).all() or x[cats].isna().any().any():raise ValueError('recovery')
 assert set(x.is_delayed.unique())<={0,1};x[[*cols,*flags]].sort_values('trip_id').to_csv(out/'trips_recovered.csv',index=False);js(out/'recovery_audit.json',{'rows':len(x),'input_missing':int(d[cols].isna().sum().sum()),'numeric_recovered':recovered_numeric,'categorical_recovered':recovered_categorical,'remaining_missing':int(x[cols].isna().sum().sum())})
 op=x[['trip_id','departure_hour','distance_km','passengers','fare_amount','is_holiday','cancellation_risk',*flags]].copy();op['passenger_km']=op.distance_km*op.passengers;op['fare_per_passenger']=np.where(op.passengers>0,op.fare_amount/op.passengers,0);op.to_csv(out/'operational_features.csv',index=False);ctx=x[['trip_id','route','vehicle_type','day_of_week','weather_condition','delay_minutes','is_delayed']].copy();ctx.to_csv(out/'context_features.csv',index=False);m=op.merge(ctx,on='trip_id',validate='one_to_one');m.to_csv(out/'model_data.csv',index=False)
 nums2=['departure_hour','distance_km','passengers','fare_amount','is_holiday','cancellation_risk','passenger_km','fare_per_passenger'];features=nums2+cats;tr,te=train_test_split(m,test_size=.25,random_state=42,stratify=m.is_delayed);model=Pipeline([('features',ColumnTransformer([('numeric',StandardScaler(),nums2),('categorical',OneHotEncoder(handle_unknown='ignore'),cats)])),('model',LogisticRegression(C=1,solver='liblinear',max_iter=1000,random_state=42))]);model.fit(tr[features],tr.is_delayed);prob=model.predict_proba(te[features])[:,1];yp=(prob>=.5).astype(int)
 with (out/'delay_model.pkl').open('wb') as h:pickle.dump(model,h)
 pd.DataFrame({'trip_id':te.trip_id,'actual_is_delayed':te.is_delayed,'probability':prob,'predicted_is_delayed':yp}).sort_values('trip_id').to_csv(out/'delay_predictions.csv',index=False);js(out/'delay_metrics.json',{'train_rows':len(tr),'test_rows':len(te),'accuracy':accuracy_score(te.is_delayed,yp),'precision':precision_score(te.is_delayed,yp,zero_division=0),'recall':recall_score(te.is_delayed,yp,zero_division=0),'f1':f1_score(te.is_delayed,yp,zero_division=0),'roc_auc':roc_auc_score(te.is_delayed,prob)});route=m.groupby('route',as_index=False).agg(trip_count=('trip_id','size'),delay_rate=('is_delayed','mean'),mean_delay=('delay_minutes','mean'),mean_cancellation_risk=('cancellation_risk','mean')).sort_values('route');route.to_csv(out/'route_diagnostics.csv',index=False);weather=m.groupby('weather_condition',as_index=False).agg(trip_count=('trip_id','size'),delay_rate=('is_delayed','mean'),mean_delay=('delay_minutes','mean')).sort_values('weather_condition');weather.to_csv(out/'weather_diagnostics.csv',index=False);vehicle=m.groupby('vehicle_type',as_index=False).agg(trip_count=('trip_id','size'),delay_rate=('is_delayed','mean'),mean_cancellation_risk=('cancellation_risk','mean'),mean_passenger_km=('passenger_km','mean')).sort_values('vehicle_type');vehicle.to_csv(out/'vehicle_diagnostics.csv',index=False);js(out/'delay_report.json',{'trips':len(m),'input_missing':int(d[cols].isna().sum().sum()),'model_test_rows':len(te),'route_trips':int(route.trip_count.sum()),'weather_trips':int(weather.trip_count.sum()),'vehicle_trips':int(vehicle.trip_count.sum()),'routes':len(route),'weather_conditions':len(weather),'vehicle_types':len(vehicle)})

RUNNERS={'050_sports_visualization_integration_recovery_v2':recovery_fanout,'052_sports_visualization_integration_validation_v2':position_linear,'074_transportation_prediction_validation_recovery':prediction_recovery_multiview,'094_transportation_visualization_cleaning_validation_v2':trip_fanout,'098_transportation_visualization_integration_validation':operations_fanin}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);x=p.parse_args();x.output_dir.mkdir(parents=True,exist_ok=True);RUNNERS[Path(__file__).resolve().parent.name](x.data_dir,x.output_dir)
